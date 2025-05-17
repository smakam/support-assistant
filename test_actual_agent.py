#!/usr/bin/env python3
"""
Test script to test the actual StaticKnowledgeAgent implementation with real embeddings.
"""
import asyncio
import logging
from dotenv import load_dotenv
import os
import sys

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

# First load environment variables
load_dotenv()

async def test_actual_agent():
    """Test the actual StaticKnowledgeAgent implementation"""
    from app.services.agents.static_agent import StaticKnowledgeAgent
    
    print("\n=== Testing Actual StaticKnowledgeAgent Implementation ===")
    
    # Initialize the agent
    agent = StaticKnowledgeAgent()
    
    # Test queries
    test_queries = [
        "What are the benefits of VIP players?",
        "Tell me about legendary items",
        "How are clans ranked?", 
        "Can XP boosters be stacked?",
        "What are magic clans good for?"
    ]
    
    for query in test_queries:
        print(f"\n=== Testing Query: '{query}' ===")
        
        # Get answer from agent
        answer = await agent.answer_query(query)
        
        print(f"Agent answer: {answer}")

if __name__ == "__main__":
    asyncio.run(test_actual_agent()) 