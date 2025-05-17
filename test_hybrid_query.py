#!/usr/bin/env python3
"""
Test script to specifically test the hybrid query handling with the improved prompt.
"""
import asyncio
import logging
from dotenv import load_dotenv
import os
import sys
from openai import OpenAI

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

# First load environment variables
load_dotenv()

async def test_hybrid_query():
    """Test how the system handles a hybrid query that requires both dynamic and static data"""
    from app.services.agents.static_agent import StaticKnowledgeAgent
    
    print("\n=== Testing Hybrid Query Handling with Enhanced Prompt ===")
    
    # Initialize the static agent with our improved prompt
    agent = StaticKnowledgeAgent()
    
    # Simulate as if we already know FireMages is a Magic clan (this would come from SQL)
    clan_info = "FireMages is a Magic clan according to our database."
    
    # Test the query that previously failed
    query = "Is FireMages a magic clan and what are the benefits?"
    
    # Let's be explicit about connecting the SQL result with the knowledge base query
    enhanced_query = f"{clan_info} {query}"
    
    print(f"\n=== Testing Query: '{enhanced_query}' ===")
    
    # Get answer from agent
    answer = await agent.answer_query(enhanced_query)
    
    print(f"\nAgent answer: {answer}")
    
    # Also test just asking about magic clans in general
    general_query = "What are magic clans good for?"
    print(f"\n=== Testing General Query: '{general_query}' ===")
    general_answer = await agent.answer_query(general_query)
    print(f"\nAgent answer: {general_answer}")

if __name__ == "__main__":
    asyncio.run(test_hybrid_query()) 