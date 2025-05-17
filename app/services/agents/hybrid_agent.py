from typing import Dict
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.chains import LLMChain
from app.services.agents.static_agent import StaticKnowledgeAgent
from app.services.agents.dynamic_agent import DynamicDataAgent
from app.core.config import settings
from app.policies.rules import rules_block
import logging
import re

logger = logging.getLogger("uvicorn.error")

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
        # Check if this is a hybrid query that needs both static and dynamic information
        clan_name = None
        is_hybrid_clan_query = False
        
        # Pattern to extract clan names and detect benefits/information questions
        clan_pattern = re.compile(r'is\s+([a-zA-Z]+)\s+a\s+([a-zA-Z]+)\s+clan', re.IGNORECASE)
        benefits_pattern = re.compile(r'benefits|good for|abilities|specialize|what.*do', re.IGNORECASE)
        
        # Check if we have a clan question
        clan_match = clan_pattern.search(query)
        if clan_match:
            clan_name = clan_match.group(1)
            clan_type_query = clan_match.group(0)  # The "is X a Y clan" part
            
            # Check if we also have a benefits question
            if benefits_pattern.search(query):
                is_hybrid_clan_query = True
                logger.info(f"Detected hybrid clan query about {clan_name} with benefits question")
                
        # Initialize response components
        static_answer = ""
        dynamic_answer = ""
        
        # Handle hybrid clan questions with specialized approach
        if is_hybrid_clan_query and clan_name:
            # First, get clan type from database
            dynamic_question = f"Is {clan_name} a magic clan?"
            dynamic_answer = await self.dynamic_agent.answer_query(dynamic_question, user_context)
            
            # Extract clan type from dynamic answer (assuming it's structured properly)
            clan_type = None
            if "magic" in dynamic_answer.lower():
                clan_type = "magic"
            elif "physical" in dynamic_answer.lower() or "pvp" in dynamic_answer.lower():
                clan_type = "physical" if "physical" in dynamic_answer.lower() else "pvp"
            elif "balanced" in dynamic_answer.lower():
                clan_type = "balanced"
            
            # Then pass this information to the static agent along with the benefits question
            if clan_type:
                # Create an enhanced knowledge query that combines the DB result with the knowledge question
                knowledge_question = f"{clan_name} is a {clan_type} clan according to our database. What are the benefits or characteristics of {clan_type} clans?"
                logger.info(f"Enhanced knowledge query: {knowledge_question}")
                static_answer = await self.static_agent.answer_query(knowledge_question)
            else:
                # Fallback to general benefits question if we couldn't extract clan type
                knowledge_question = "What are the different clan types and their benefits?"
                static_answer = await self.static_agent.answer_query(knowledge_question)
        else:
            # Standard approach for non-hybrid queries
            static_answer = await self.static_agent.answer_query(query)
            dynamic_answer = await self.dynamic_agent.answer_query(query, user_context)
        
        # Combine the answers
        combined_response = await self.combiner_chain.arun(
            static_answer=static_answer,
            dynamic_answer=dynamic_answer,
            original_query=query
        )
        
        return combined_response 