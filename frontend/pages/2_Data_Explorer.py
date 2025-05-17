import streamlit as st
import pandas as pd
import sqlite3
import os
import sys
import logging

# Add parent directory to path to import shared functions
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

# Import shared functions from main app
from streamlit_app import read_knowledge_base, get_db_schema, get_sample_data, find_file, IS_PRODUCTION

# Constants
KNOWLEDGE_BASE_PATH = os.environ.get("KNOWLEDGE_BASE_PATH", "advanced_knowledge_base.txt")
DB_PATH = os.environ.get("DB_PATH", "kgen_gaming_support_advanced.db")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)
logger = logging.getLogger(__name__)

def main():
    st.title("Explore Data Sources")
    
    tabs = st.tabs(["Knowledge Base", "Database Schema", "Sample Data"])
    
    with tabs[0]:
        st.subheader("Static Knowledge Base")
        st.markdown("""
        This knowledge base contains pre-written information about game concepts, 
        mechanics, and policies. The system uses vector search to find relevant information.
        """)
        
        kb_content = read_knowledge_base()
        
        # Display the knowledge base items in a more user-friendly format
        if kb_content and kb_content.startswith("- "):
            items = [item.strip() for item in kb_content.split("\n-") if item.strip()]
            for i, item in enumerate(items):
                if i == 0 and item.startswith("- "):
                    item = item[2:]
                st.markdown(f"- {item}")
        else:
            st.text(kb_content)
    
    with tabs[1]:
        st.subheader("Database Schema")
        st.markdown("""
        The SQL database stores structured game data like player information, 
        clan details, achievements, and purchase history.
        """)
        
        schema = get_db_schema()
        
        if isinstance(schema, str):
            st.error(schema)
        else:
            # Display schema in an expandable format
            for table_name, columns in schema.items():
                with st.expander(f"Table: {table_name}"):
                    # Create a more readable format
                    table_df = pd.DataFrame(columns)
                    st.table(table_df)
                    
                    # Show SQL CREATE TABLE statement
                    st.subheader("SQL Definition")
                    create_table_sql = f"CREATE TABLE {table_name} (\n"
                    for i, col in enumerate(columns):
                        create_table_sql += f"    {col['name']} {col['type']}"
                        if i < len(columns) - 1:
                            create_table_sql += ","
                        create_table_sql += "\n"
                    create_table_sql += ");"
                    
                    st.code(create_table_sql, language="sql")
    
    with tabs[2]:
        st.subheader("Sample Data")
        st.markdown("""
        Below are sample records from each table in the database. 
        The system uses this data to answer questions about specific players, clans, and game statistics.
        """)
        
        schema = get_db_schema()
        if isinstance(schema, str):
            st.error(schema)
        else:
            col1, col2 = st.columns([1, 2])
            
            with col1:
                table_names = list(schema.keys())
                selected_table = st.selectbox("Select a table to view sample data:", table_names)
            
            with col2:
                sample_count = st.slider("Number of rows to display:", min_value=5, max_value=50, value=10)
            
            st.subheader(f"Sample records from {selected_table}")
            sample_data = get_sample_data(selected_table, limit=sample_count)
            st.dataframe(sample_data, use_container_width=True)
            
            # Add capability to run custom SQL queries
            with st.expander("Run custom SQL query"):
                st.markdown("""
                Write your own SQL query to explore the database. 
                For safety reasons, only SELECT queries are allowed.
                """)
                
                custom_query = st.text_area("SQL Query:", f"SELECT * FROM {selected_table} LIMIT 10;", height=100)
                
                if st.button("Run Query"):
                    if custom_query.lower().strip().startswith("select"):
                        try:
                            if IS_PRODUCTION:
                                # Use PostgreSQL in production
                                import psycopg2
                                import psycopg2.extras
                                
                                db_url = os.environ.get("DATABASE_URL")
                                if not db_url:
                                    st.error("DATABASE_URL environment variable not set in production")
                                    st.info("Using demo mode - queries will return sample data only")
                                else:
                                    try:
                                        # Connect to PostgreSQL
                                        conn = psycopg2.connect(db_url)
                                        df = pd.read_sql_query(custom_query, conn)
                                        conn.close()
                                        
                                        st.subheader("Query Results")
                                        st.dataframe(df, use_container_width=True)
                                        st.success(f"Query returned {len(df)} rows.")
                                    except Exception as e:
                                        st.error(f"Error executing query: {str(e)}")
                                        st.info("Using demo mode - displaying sample data")
                                        # Show sample data for the selected table as fallback
                                        df = get_sample_data(selected_table, limit=10)
                                        st.subheader("Sample Data")
                                        st.dataframe(df, use_container_width=True)
                            else:
                                # Find the database file for local development
                                db_path = find_file(DB_PATH)
                                if not db_path:
                                    st.error(f"Database file not found: {DB_PATH}")
                                    st.info("Using demo mode - queries will return sample data only")
                                    # Show sample data for the selected table as fallback
                                    df = get_sample_data(selected_table, limit=10)
                                    st.subheader("Sample Data")
                                    st.dataframe(df, use_container_width=True)
                                else:
                                    conn = sqlite3.connect(db_path)
                                    df = pd.read_sql_query(custom_query, conn)
                                    conn.close()
                                    
                                    st.subheader("Query Results")
                                    st.dataframe(df, use_container_width=True)
                                    st.success(f"Query returned {len(df)} rows.")
                        except Exception as e:
                            st.error(f"Error executing query: {str(e)}")
                    else:
                        st.error("Only SELECT queries are allowed for security reasons.")
                        
            # Show relationships between tables
            with st.expander("Database Relationships"):
                st.markdown("""
                ### Table Relationships
                
                The database has the following key relationships:
                
                - **players** table has player profiles and stats
                - **clans** table contains clan information
                - **clan_members** links players to clans (many-to-one)
                - **items** lists all game items
                - **player_items** shows which items each player owns (many-to-many)
                - **achievements** lists all possible achievements
                - **player_achievements** tracks which players have earned which achievements (many-to-many)
                - **purchases** records all in-game purchases
                
                These relationships allow the system to answer complex questions about players, clans, and their game activities.
                """)
                
                # Create a simple ERD-style visualization
                st.code("""
+---------------+        +---------------+        +---------------+
|    players    |        | clan_members  |        |     clans     |
+---------------+        +---------------+        +---------------+
| player_id (PK)|<-------| player_id (FK)|        | clan_id (PK)  |
| username      |        | clan_id (FK)  |------->| clan_name     |
| rank          |        | join_date     |        | clan_type     |
| level         |        | role          |        | founded_date  |
| xp            |        +---------------+        | member_count  |
+---------------+                                 +---------------+
        |                                                 
        |                 +---------------+                
        |                 | player_items  |                
        |                 +---------------+                
        +---------------->| player_id (FK)|                
        |                 | item_id (FK)  |<---------------+
        |                 | quantity      |                |
        |                 +---------------+                |
        |                                                  |
        |                                          +---------------+
        |                                          |     items     |
        |                                          +---------------+
        |                                          | item_id (PK)  |
        |                                          | item_name     |
        |                                          | rarity        |
        |                                          | type          |
        |                                          +---------------+
        |
        |                 +------------------+
        |                 | player_achievements |
        |                 +------------------+
        +---------------->| player_id (FK)   |
                          | achievement_id (FK) |<--------------+
                          | date_earned      |                  |
                          +------------------+                  |
                                                                |
                                                       +------------------+
                                                       |   achievements   |
                                                       +------------------+
                                                       | achievement_id (PK) |
                                                       | name            |
                                                       | description     |
                                                       | xp_reward       |
                                                       +------------------+
                """)

if __name__ == "__main__":
    main() 