import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import io
from PIL import Image
import os
import sys
import logging

# Add parent directory to path to import shared functions
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

# Import shared functions from main app
from streamlit_app import create_system_diagram

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)
logger = logging.getLogger(__name__)

def main():
    st.title("System Architecture & Documentation")
    
    st.markdown("""
    ## AI Customer Assistant

    This demo application showcases an AI-powered customer support system for a fictional gaming platform. 
    The system uses a combination of static knowledge and dynamic game data to answer user queries.
    """)
    
    # Show architecture diagram
    st.subheader("System Architecture")
    arch_diagram = create_system_diagram()
    st.image(arch_diagram, caption="AI Customer Assistant System Architecture")
    
    # Explanation of components
    st.markdown("""
    ### Key Components:
    
    **1. Router**
    - Classifies incoming queries and routes them to the appropriate specialized agent
    - Categories: Static Knowledge, Dynamic Data, Hybrid, Follow-up, and Escalation
    
    **2. Specialized Agents**
    - **Static Knowledge Agent**: Answers questions about game mechanics and policies using vector search
    - **Dynamic Data Agent**: Handles database queries about specific player or clan information
    - **Hybrid Agent**: Combines both knowledge base and database information
    
    **3. Data Sources**
    - **Knowledge Base**: Contains text knowledge about game mechanics, policies, and general information
    - **SQL Database**: Stores structured game data like player stats, clan information, and achievements
    
    **4. External Systems**
    - **Jira**: Used for creating tickets when escalating issues to human support
    - **LangSmith**: Provides tracing and observability for debugging and monitoring
    """)
    
    # Show code examples
    with st.expander("How the system works"):
        st.code("""
# Query routing flow example:
1. User asks: "What are legendary items?"
   - Router classifies as: STATIC
   - StaticKnowledgeAgent uses vector search to find relevant information
   - Response: "Legendary items are the rarest items in the game and offer the highest stat bonuses..."

2. User asks: "What is DragonSlayer99's rank?"
   - Router classifies as: DYNAMIC
   - DynamicDataAgent creates SQL query to get player rank
   - Response: "DragonSlayer99 is currently ranked #42 in the Global leaderboard"

3. User asks: "Is FireMages a magic clan and what are the benefits?"
   - Router classifies as: HYBRID
   - HybridAgent combines SQL lookup with knowledge base information
   - Response: "Yes, FireMages is a magic clan. Magic clans specialize in spell-based attacks and support abilities..."
        """)
    
    # Technical architecture diagram (new)
    st.subheader("Technical Architecture")
    
    # Create technical architecture diagram
    fig, ax = plt.subplots(figsize=(12, 8))
    ax.axis('off')
    
    # Define component layers
    layers = {
        "Frontend Layer": [
            {"name": "Streamlit Web UI", "tech": "Streamlit, Python", "x": 0.5, "y": 0.85},
        ],
        "API Layer": [
            {"name": "FastAPI Service", "tech": "FastAPI, Python", "x": 0.5, "y": 0.7},
        ],
        "Agent Layer": [
            {"name": "Router", "tech": "LangChain, LangSmith", "x": 0.5, "y": 0.55},
            {"name": "Static Knowledge Agent", "tech": "VectorDB, LangChain", "x": 0.25, "y": 0.45},
            {"name": "Dynamic Data Agent", "tech": "SQLite, SQL", "x": 0.5, "y": 0.45},
            {"name": "Hybrid Agent", "tech": "VectorDB, SQL, Chain", "x": 0.75, "y": 0.45},
        ],
        "Data Layer": [
            {"name": "Knowledge Base", "tech": "Vector Embeddings", "x": 0.25, "y": 0.3},
            {"name": "SQL Database", "tech": "SQLite", "x": 0.5, "y": 0.3},
            {"name": "JIRA API", "tech": "REST API", "x": 0.75, "y": 0.3},
        ],
        "Observability Layer": [
            {"name": "LangSmith", "tech": "Tracing, Evaluation", "x": 0.5, "y": 0.15},
        ],
    }
    
    # Define layer colors
    layer_colors = {
        "Frontend Layer": "#D7E9F7",
        "API Layer": "#C4E0F9",
        "Agent Layer": "#ADD8E6",
        "Data Layer": "#ECD5B8",
        "Observability Layer": "#F9D6C5",
    }
    
    # Draw layers
    for i, (layer_name, components) in enumerate(layers.items()):
        # Draw layer background
        y_pos = 0.9 - (i * 0.15)
        height = 0.12
        ax.add_patch(plt.Rectangle((0.1, y_pos - height), 0.8, height, 
                              fill=True, alpha=0.3, color=layer_colors[layer_name]))
        ax.text(0.05, y_pos - height/2, layer_name, ha='left', va='center', fontsize=12, weight='bold')
        
        # Draw components in this layer
        for component in components:
            # Component box
            ax.add_patch(plt.Rectangle((component["x"]-0.15, component["y"]-0.04), 0.3, 0.08, 
                        fill=True, alpha=0.7, color=layer_colors[layer_name]))
            ax.text(component["x"], component["y"], component["name"], ha='center', va='center', fontsize=10)
            # Technology label below
            ax.text(component["x"], component["y"]-0.06, component["tech"], ha='center', va='center', 
                   fontsize=8, style='italic')
    
    # Draw connections
    # Frontend to API
    ax.arrow(0.5, 0.81, 0, -0.06, head_width=0.01, head_length=0.01, fc='black', ec='black')
    
    # API to Router
    ax.arrow(0.5, 0.66, 0, -0.06, head_width=0.01, head_length=0.01, fc='black', ec='black')
    
    # Router to Agents
    ax.arrow(0.5, 0.51, -0.2, -0.03, head_width=0.01, head_length=0.01, fc='black', ec='black')
    ax.arrow(0.5, 0.51, 0, -0.03, head_width=0.01, head_length=0.01, fc='black', ec='black')
    ax.arrow(0.5, 0.51, 0.2, -0.03, head_width=0.01, head_length=0.01, fc='black', ec='black')
    
    # Agents to Data
    ax.arrow(0.25, 0.41, 0, -0.07, head_width=0.01, head_length=0.01, fc='black', ec='black')
    ax.arrow(0.5, 0.41, 0, -0.07, head_width=0.01, head_length=0.01, fc='black', ec='black')
    ax.arrow(0.75, 0.41, 0, -0.07, head_width=0.01, head_length=0.01, fc='black', ec='black')
    
    # Hybrid Agent to multiple data sources
    ax.arrow(0.75, 0.41, -0.2, -0.07, head_width=0.01, head_length=0.01, fc='black', ec='black', linestyle='dotted')
    
    # Agents to LangSmith
    ax.arrow(0.35, 0.45, 0.1, -0.25, head_width=0.01, head_length=0.01, fc='black', ec='black', linestyle='dashed')
    ax.arrow(0.5, 0.41, 0, -0.21, head_width=0.01, head_length=0.01, fc='black', ec='black', linestyle='dashed')
    ax.arrow(0.65, 0.45, -0.1, -0.25, head_width=0.01, head_length=0.01, fc='black', ec='black', linestyle='dashed')
    
    plt.title("AI Customer Assistant - Technical Architecture", fontsize=14)
    
    # Legend
    legend_elements = [
        plt.Rectangle((0, 0), 1, 1, color="#D7E9F7", alpha=0.7, label="Frontend Layer"),
        plt.Rectangle((0, 0), 1, 1, color="#C4E0F9", alpha=0.7, label="API Layer"),
        plt.Rectangle((0, 0), 1, 1, color="#ADD8E6", alpha=0.7, label="Agent Layer"),
        plt.Rectangle((0, 0), 1, 1, color="#ECD5B8", alpha=0.7, label="Data Layer"),
        plt.Rectangle((0, 0), 1, 1, color="#F9D6C5", alpha=0.7, label="Observability Layer"),
        plt.Line2D([0], [0], color='black', lw=2, linestyle='dotted', label='Hybrid Data Connections'),
        plt.Line2D([0], [0], color='black', lw=2, linestyle='dashed', label='Tracing Connections'),
    ]
    ax.legend(handles=legend_elements, loc='upper center', bbox_to_anchor=(0.5, 0), ncol=3)
    
    plt.tight_layout()
    
    # Convert to image and display
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=100)
    buf.seek(0)
    img = Image.open(buf)
    st.image(img, caption="AI Customer Assistant System Technical Architecture")

if __name__ == "__main__":
    main() 