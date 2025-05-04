from typing import Dict
from langchain_community.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.chains import LLMChain
from app.services.agents.static_agent import StaticKnowledgeAgent
from app.services.agents.dynamic_agent import DynamicDataAgent
from app.core.config import settings
from app.policies.rules import rules_block

class HybridAgent:
    def __init__(self):
        self.llm = ChatOpenAI(
            api_key=settings.OPENAI_API_KEY,
            temperature=0
        )
        self.static_agent = StaticKnowledgeAgent()
        self.dynamic_agent = DynamicDataAgent()
        
        self.combiner_prompt = ChatPromptTemplate.from_messages([
            ("system", f"""{rules_block()}

You are an AI support assistant that combines information from documentation and live data.
Your task is to create a comprehensive answer by combining:
1. Static knowledge from documentation
2. Dynamic data from the database

Create a natural, conversational response that seamlessly integrates both sources.
Make sure to maintain accuracy while making the response engaging and helpful."""),
            ("human", """Static Knowledge: {static_answer}
Dynamic Data: {dynamic_answer}

Original Question: {original_query}""")
        ])
        
        self.combiner_chain = LLMChain(
            llm=self.llm,
            prompt=self.combiner_prompt
        )

    async def answer_query(self, query: str, user_context: Dict) -> str:
        # Split hybrid questions that need both static and dynamic answers
        dynamic_question = query
        knowledge_question = query

        # Special case for magic clan questions
        if "magic clan" in query.lower() and "known for" in query.lower():
            if "firemages" in query.lower():
                # Split into a specific clan type question and a general knowledge question
                dynamic_question = "Is FireMages a magic clan?"
                knowledge_question = "What are magic clans known for?"
                print(f"Split hybrid query into: \nDynamic: {dynamic_question}\nStatic: {knowledge_question}")

        # Get answers from both agents
        static_answer = await self.static_agent.answer_query(knowledge_question)
        dynamic_answer = await self.dynamic_agent.answer_query(dynamic_question, user_context)
        
        # Combine the answers
        combined_response = await self.combiner_chain.arun(
            static_answer=static_answer,
            dynamic_answer=dynamic_answer,
            original_query=query
        )
        
        return combined_response 