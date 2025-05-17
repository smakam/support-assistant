from typing import Dict, Optional
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.chains import LLMChain
from app.schemas.support import SourceType
from app.services.agents.static_agent import StaticKnowledgeAgent
from app.services.agents.dynamic_agent import DynamicDataAgent
from app.services.agents.hybrid_agent import HybridAgent
from app.core.config import settings
from app.policies.rules import rules_block
from langsmith import traceable, RunTree
from datetime import datetime

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
5. ESCALATION - Issues needing human support intervention, or when the user requests to speak to a human, escalate, or contact support.

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
- "I want to speak to a human" → ESCALATION
- "I need to escalate this issue" → ESCALATION
- "Contact support" → ESCALATION
- "My payment failed and nothing works" → ESCALATION
- "There is a bug in the game that is not fixed" → ESCALATION

IMPORTANT: Any query using "my", "me", or "I" without specifying a player name must be classified as FOLLOW_UP unless it is a clear request for escalation or human support, in which case classify as ESCALATION.
If a query already contains a specific player name (like DragonSlayer99, IceWarden, ShadowNinja), it should NOT be classified as FOLLOW_UP.

Requests for escalation, human support, or contacting support should always be classified as ESCALATION, regardless of context.

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

    @traceable(name="route_query")
    async def route_query(self, query: str, user_context: Dict, conversation_history: list = None, parent_run_id: str = None) -> QueryResponse:
        """
        Route a query to the appropriate agent based on its type.
        
        Args:
            query: The user's query text
            user_context: User context information
            conversation_history: Previous conversation messages
            parent_run_id: Optional parent run ID for maintaining trace continuity
        """
        # Use parent_run_id if provided to maintain trace continuity in LangSmith
        run_tree_kwargs = {}
        if parent_run_id:
            print(f"Using parent run ID for trace continuity: {parent_run_id}")
            run_tree_kwargs = {"parent_run_id": parent_run_id}
            
            # Attempt to mark this as a child run of the parent
            try:
                from langsmith import Client
                client = Client()
                
                # Get current run id
                current_run_id = None
                try:
                    from langsmith.run_trees import RunTree
                    current_run = RunTree.get_current()
                    if current_run:
                        current_run_id = current_run.id
                        print(f"Current run ID: {current_run_id}")
                        
                        # Link current run to parent
                        if current_run_id and parent_run_id:
                            client.update_run(parent_run_id, {"child_runs": [current_run_id]})
                            print(f"Linked current run {current_run_id} as child of {parent_run_id}")
                except Exception as e:
                    print(f"Could not get current run ID: {e}")
            except Exception as e:
                print(f"Failed to link runs: {e}")
                
        # Check for explicit escalation phrases first, before even calling the classifier
        escalation_phrases = [
            "speak to a human", "talk to a human", "need a human", "contact support", 
            "escalate", "support ticket", "create a ticket", "speak to an agent",
            "talk to support", "need help from a person", "human support"
        ]
        
        # If query contains any escalation phrase, bypass classification and go straight to escalation
        if any(phrase in query.lower() for phrase in escalation_phrases) or query.lower().startswith("escalate:"):
            print(f"Direct escalation detected: '{query}'")
            # Make sure parent_run_id is available to maintain trace continuity in LangSmith
            if parent_run_id:
                print(f"Escalation will maintain parent_run_id: {parent_run_id}")
            else:
                print("Warning: No parent_run_id for escalation request, missing trace continuity")
                # Check if conversation_history exists for better continuity
                if conversation_history and len(conversation_history) > 0:
                    print(f"Found {len(conversation_history)} messages in history for escalation")
            
            # Create support ticket with conversation history for context
            ticket_id = await self.create_support_ticket(query, user_context, conversation_history, parent_run_id=parent_run_id)
            return QueryResponse(
                answer="I've created a support ticket for further assistance.",
                source_type=SourceType.ESCALATION,
                ticket_id=ticket_id
            )
        
        # Otherwise proceed with regular classification
        classification_result = await self.classifier_chain.ainvoke({"query": query})
        query_type = classification_result.get("text", "").strip().upper()
        
        print(f"Query classified as: {query_type}")

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
            ticket_id = await self.create_support_ticket(query, user_context, conversation_history, parent_run_id=parent_run_id)
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

    @traceable(name="generate_follow_up")
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

    @traceable(name="create_support_ticket")
    async def create_support_ticket(self, query: str, user_context: Dict, conversation_history: list = None, parent_run_id: str = None) -> str:
        """
        Create a support ticket with the conversation context.
        
        Args:
            query: The user's query text that triggered escalation
            user_context: User context information
            conversation_history: Previous conversation messages
            parent_run_id: Optional parent run ID for maintaining trace continuity in LangSmith
        """
        # If parent_run_id is provided, link this ticket creation to the parent conversation
        run_tree_kwargs = {}
        if parent_run_id:
            run_tree_kwargs = {"parent_run_id": parent_run_id}
            print(f"Creating ticket as part of conversation with parent_run_id: {parent_run_id}")
            
        try:
            from app.services.jira.client import JiraClient
            jira_client = JiraClient()
            
            # Debug print for conversation history
            if conversation_history:
                print(f"Received conversation history with {len(conversation_history)} messages")
                # Debug the first few messages to check content
                for i, msg in enumerate(conversation_history[:3]):
                    print(f"Message {i+1} type: {msg.get('type')}, content start: {msg.get('content', '')[:50]}...")
            else:
                print("No conversation history received")
            
            # Format the conversation history into a readable format
            conversation_text = ""
            if conversation_history and len(conversation_history) > 0:
                conversation_text = "\nConversation History:\n"
                for i, message in enumerate(conversation_history):
                    # Add a message number for better readability
                    msg_num = i + 1
                    
                    if isinstance(message, dict):
                        if message.get('type') == 'user':
                            conversation_text += f"\n[{msg_num}] 👤 USER: {message.get('content', '')}\n"
                        elif message.get('type') == 'assistant':
                            conversation_text += f"[{msg_num}] 🤖 ASSISTANT: {message.get('content', '')}\n"
                        elif message.get('type') == 'followup':
                            conversation_text += f"[{msg_num}] ❓ FOLLOW-UP: {message.get('content', '')}\n"
                        elif message.get('type') == 'system':
                            conversation_text += f"[{msg_num}] ⚙️ SYSTEM: {message.get('content', '')}\n"
                
                # Print a sample of the conversation text for debugging
                print(f"Formatted conversation text (first 300 chars): {conversation_text[:300]}...")
                print(f"Conversation history length for Jira: {len(conversation_text)} characters")
            else:
                print("WARNING: Proceeding without conversation history for Jira ticket")
            
            # Include more user context and information in the ticket
            user_info = f"Username: {user_context.get('username', 'N/A')}\n" \
                      f"Role: {user_context.get('role', 'N/A')}"
                      
            # Extract query details - handle the ESCALATE: prefix if present
            actual_query = query
            additional_details = ""
            if query.startswith("ESCALATE:"):
                parts = query.split("Additional details:", 1)
                actual_query = parts[0].replace("ESCALATE:", "").strip()
                if len(parts) > 1:
                    additional_details = f"\nAdditional Details from User:\n{parts[1].strip()}"
            
            # Create a more structured ticket description with clear sections
            description = f"""
            === USER INFORMATION ===
            {user_info}
            
            === ESCALATION QUERY ===
            {actual_query}
            {additional_details}
            
            === CONVERSATION HISTORY ===
            {conversation_text}
            
            === TECHNICAL INFO ===
            Parent Run ID: {parent_run_id or "N/A"}
            Ticket Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            """
            
            print(f"Creating ticket with description length: {len(description)}")
            
            return await jira_client.create_ticket(
                summary=f"Support Request from {user_context['username']}: {actual_query[:50]}...",
                description=description,
                issue_type="Task"
            )
        except Exception as e:
            print(f"JIRA integration error: {e}")
            return "JIRA_DISABLED"

# Create a singleton instance
query_router = QueryRouter() 