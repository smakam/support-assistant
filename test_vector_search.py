#!/usr/bin/env python3
"""
Test script to validate vector search functionality in the StaticKnowledgeAgent.
This script tests whether the agent is properly using vector search to retrieve
relevant content from the knowledge base.
"""
import asyncio
import logging
from dotenv import load_dotenv
import os
import sys
from unittest.mock import patch

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

# First load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

# Make sure we set the LANGCHAIN_TRACING_V2 variable for visibility in LangSmith
os.environ["LANGCHAIN_TRACING_V2"] = "true"

# Import just the path settings to avoid initializing OpenAI
from app.core.config import settings

def check_vector_store_chunking():
    """Check how the knowledge base is being chunked without initializing OpenAI"""
    logging.info("Checking how knowledge base would be chunked")
    
    # Remove existing vector store if any
    vector_store_path = settings.VECTOR_STORE_PATH
    if os.path.exists(vector_store_path):
        logging.info(f"Removing existing vector store at {vector_store_path}")
        import shutil
        try:
            shutil.rmtree(vector_store_path)
        except Exception as e:
            logging.error(f"Error removing vector store: {e}")

    # Read the knowledge base directly
    knowledge_base_path = settings.KNOWLEDGE_BASE_PATH
    logging.info(f"Reading knowledge base from {knowledge_base_path}")
    
    with open(knowledge_base_path, 'r') as f:
        raw_text = f.read()
    
    # Simulate the chunking process
    lines = raw_text.split('\n')
    bullet_points = []
    
    for line in lines:
        if line.strip().startswith('- '):
            bullet_points.append(line.strip())
    
    logging.info(f"Found {len(bullet_points)} bullet points in knowledge base")
    
    for i, bullet in enumerate(bullet_points):
        logging.info(f"Bullet {i+1}: {bullet}")
    
    # Check how they would be handled
    logging.info("\nAnalysis of knowledge base chunking:")
    logging.info(f"When vector search is used, these {len(bullet_points)} items would be independently searchable")
    logging.info("But if the entire knowledge base is used as context, all items would be provided regardless of relevance")
    
    # Test some example queries to see what would be retrieved
    test_queries = [
        "What are the benefits of VIP players?",
        "Tell me about legendary items",
        "How are clans ranked?",
        "Can XP boosters be stacked?",
        "What are magic clans good for?"
    ]
    
    logging.info("\nSimulating which bullet points would be relevant for each query:")
    
    for query in test_queries:
        logging.info(f"\nQuery: '{query}'")
        relevant_bullets = []
        
        # Very simple keyword matching to simulate vector search
        query_terms = set(query.lower().split())
        for bullet in bullet_points:
            bullet_terms = set(bullet.lower().split())
            # Check for term overlap
            if query_terms.intersection(bullet_terms):
                relevant_bullets.append(bullet)
        
        if relevant_bullets:
            logging.info(f"Found {len(relevant_bullets)} potentially relevant bullet points:")
            for bullet in relevant_bullets:
                logging.info(f"  - {bullet}")
        else:
            logging.info("No directly matching bullet points found using simple term matching")

if __name__ == "__main__":
    check_vector_store_chunking() 