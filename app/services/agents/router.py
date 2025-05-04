from typing import Dict, Optional
from langchain_community.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.chains import LLMChain
from app.schemas.support import SourceType
from app.services.agents.static_agent import StaticKnowledgeAgent
from app.services.agents.dynamic_agent import DynamicDataAgent
from app.services.agents.hybrid_agent import HybridAgent
from app.core.config import settings
from app.policies.rules import rules_block

class QueryResponse:
    def __init__(
        self,
        answer: str,
        source_type: SourceType,
        follow_up_question: Optional[str] = None,
        ticket_id: Optional[str] = None,
        query_id: Optional[str] = None
    ):
        self.answer = answer
        self.source_type = source_type
        self.follow_up_question = follow_up_question
        self.ticket_id = ticket_id
        self.query_id = query_id

class QueryRouter:
    def __init__(self):
        self.llm = ChatOpenAI(
            api_key=settings.OPENAI_API_KEY,
            temperature=0
        )
        
        self.classifier_prompt = ChatPromptTemplate.from_messages([
            ("system", f"""{rules_block()}

You are an AI support assistant for a gaming platform. Classify user queries into the following categories based on whether they need documentation only or live data:

1. STATIC - Conceptual questions about game mechanics, support policies, items, or general features that can be answered solely from documentation (e.g., "Why are legendary items rare?").
2. DYNAMIC - Questions about specific player or clan data (e.g., level, purchases, clan type, member counts) that require querying the live database.
3. HYBRID - Questions that need both documentation and live data to answer fully.
4. FOLLOW_UP - Queries missing necessary context (player name, clan name, timeframe) that require clarification.
5. ESCALATION - Issues needing human support intervention.

Examples to clarify classification:
- "Is my clan a magic clan?" → FOLLOW_UP (missing clan name)
- "Show me my rank" → FOLLOW_UP (missing player name)
- "What items have I purchased?" → FOLLOW_UP (missing player name)
- "Is FireMages a magic clan?" → DYNAMIC (has clan name, needs clan_type from database)
- "What type of clan is FireMages?" → DYNAMIC (specific clan data query)
- "How many members does my clan have?" → FOLLOW_UP (missing clan name)
- "How many members does FireMages have?" → DYNAMIC (has clan name, needs count from database)
- "What are the benefits of magic clans?" → STATIC (general game mechanics)
- "How many gold achievements has DragonSlayer99 earned?" → DYNAMIC (has player name, needs achievement data)
- "What achievements has IceWarden unlocked?" → DYNAMIC (has player name, needs achievement data)
- "What is DragonSlayer99's rank?" → DYNAMIC (has player name, needs leaderboard data)

IMPORTANT: Any query using "my", "me", or "I" without specifying a player name must be classified as FOLLOW_UP.
If a query already contains a specific player name (like DragonSlayer99, IceWarden, ShadowNinja), it should NOT be classified as FOLLOW_UP.

Respond with exactly one uppercase category name (STATIC, DYNAMIC, HYBRID, FOLLOW_UP, or ESCALATION)."""),
            ("human", "{query}")
        ])
        
        self.classifier_chain = LLMChain(
            llm=self.llm,
            prompt=self.classifier_prompt
        )
        
        # Initialize agents
        self.static_agent = StaticKnowledgeAgent()
        self.dynamic_agent = DynamicDataAgent()
        self.hybrid_agent = HybridAgent()
        # self.jira_client = JiraClient()  # REMOVE eager JIRA init

    async def route_query(self, query: str, user_context: Dict) -> QueryResponse:
        # Classify the query
        classification_result = await self.classifier_chain.ainvoke({"query": query})
        query_type = classification_result.get("text", "").strip().upper()

        # Route to appropriate handler
        if query_type == "STATIC":
            answer = await self.static_agent.answer_query(query)
            return QueryResponse(answer=answer, source_type=SourceType.STATIC)
        
        elif query_type == "DYNAMIC":
            answer = await self.dynamic_agent.answer_query(query, user_context)
            return QueryResponse(answer=answer, source_type=SourceType.DYNAMIC)
        
        elif query_type == "HYBRID":
            answer = await self.hybrid_agent.answer_query(query, user_context)
            return QueryResponse(answer=answer, source_type=SourceType.HYBRID)
        
        elif query_type == "FOLLOW_UP":
            follow_up = await self.generate_follow_up(query)
            return QueryResponse(
                answer="I need some additional information to help you better.",
                source_type=SourceType.FOLLOW_UP,
                follow_up_question=follow_up
            )
        
        elif query_type == "ESCALATION":
            ticket_id = await self.create_support_ticket(query, user_context)
            return QueryResponse(
                answer="I've created a support ticket for further assistance.",
                source_type=SourceType.ESCALATION,
                ticket_id=ticket_id
            )
        
        else:
            print(f"Unknown classification from LLM: {query_type}")
            # Fallback or error handling
            answer = await self.hybrid_agent.answer_query(query, user_context)
            return QueryResponse(answer=answer, source_type=SourceType.HYBRID)

    async def generate_follow_up(self, query: str) -> str:
        # Build a follow-up prompt that guides the user to rephrase their query with missing context
        follow_up_prompt = ChatPromptTemplate.from_messages([
            ("system", f"""{rules_block()}

Generate a concise follow-up asking the user to provide ONLY the specific missing information.
For simple follow-ups, ask for just the exact data needed, not a rephrased question.

EXAMPLES:
- If the user asked 'List the legendary items purchased', respond with:
  "Could you please provide just the player name?"
- If the user asked 'What is the win rate in region', respond with:
  "Please specify which region you're asking about."
- If the user asked 'Show me clan stats', respond with:
  "Please provide the specific clan name you're interested in."

The system will automatically combine the original question with this information.
DO NOT ask users to rephrase their entire question."""),
            ("human", "{query}")
        ])
        
        follow_up_chain = LLMChain(llm=self.llm, prompt=follow_up_prompt)
        response = await follow_up_chain.ainvoke({"query": query})
        return response.get("text", "Could you please rephrase your question with the needed details?")

    async def create_support_ticket(self, query: str, user_context: Dict) -> str:
        try:
            from app.services.jira.client import JiraClient
            jira_client = JiraClient()
            return await jira_client.create_ticket(
                summary=f"Support Request from {user_context['username']}",
                description=f"""
                User: {user_context['username']}
                Role: {user_context['role']}
                Query: {query}
                """,
                issue_type="Support"
            )
        except Exception as e:
            print(f"JIRA integration error: {e}")
            return "JIRA_DISABLED"

# Create a singleton instance
query_router = QueryRouter() 