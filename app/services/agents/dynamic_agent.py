from typing import Dict
from langchain_community.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain_community.utilities.sql_database import SQLDatabase
from langchain.chains.llm import LLMChain
from app.core.config import settings
import re

class DynamicDataAgent:
    def __init__(self):
        self.llm = ChatOpenAI(
            api_key=settings.OPENAI_API_KEY,
            temperature=0
        )
        self.db = SQLDatabase.from_uri(settings.active_db_url)
        
        # Get the actual database schema
        self.db_schema = self.db.get_table_info()
        print(f"Loaded database schema: {self.db_schema[:500]}...")  # Print first 500 chars for debugging
        
        # Create a chain for converting SQL results to natural language
        # Use 'question' as the key for the original user query
        self.response_prompt = ChatPromptTemplate.from_template("""
        You are a helpful gaming support assistant. Based on the following SQL query and its result,
        please provide a conversational response to the user's question.
        
        SQL Query: {query}
        SQL Result: {result}
        User Question: {question}
        
        RESPONSE GUIDELINES:
        1. Be professional and factual
        2. IMPORTANT: Treat all players mentioned in queries as third parties, completely separate from the user asking the question
        3. NEVER use language that implies the player being asked about is the one reading the message
        4. Always phrase responses like "Player X has Y" rather than any complimentary or personal remarks about that player
        5. Keep responses concise and focused on answering the question directly
        6. Use a kind, light-hearted tone when appropriate, but directed at the person asking the question, not the player in the query
        7. Provide only objective information about other players without subjective comments on their achievements or status
        8. Completely avoid phrases like:
           - "They've been putting in some serious gaming hours"
           - "Pretty impressive collection they're building"
           - "They're definitely making their mark"
        9. Examples of appropriate responses:
           - For rank queries: "ShadowNinja is ranked 8th."
           - For item queries: "PixelMage has purchased 3 legendary items."
           - For clan queries: "DarkWolves has 42 members."
        
        Your response:
        """)
        
        self.response_chain = LLMChain(
            llm=self.llm,
            prompt=self.response_prompt
        )

        # Create a schema-driven SQL generation prompt
        self.sql_gen_prompt = ChatPromptTemplate.from_template("""
        You are an SQL expert. Create a valid SQL query for SQLite based solely on the database schema below.
        
        DATABASE SCHEMA:
        {db_schema}
        
        SCHEMA ANALYSIS INSTRUCTIONS:
        1. Analyze the tables and their columns carefully
        2. Identify the primary keys and foreign key relationships
        3. For questions about players, use the 'players' table which has 'username' column 
        4. For questions about rankings, join 'leaderboards' (which has player_id) with 'players' (which has username)
        5. For questions about clans, use the 'clans' table which has 'clan_name' and 'clan_type' columns
        6. For questions about purchases, JOIN the 'purchases' table (which has player_id) with 'players' table (which has username)
        7. IMPORTANT: purchases.player_id links to players.player_id, not by name
        8. For time-based queries on purchases, use the purchase_date column
        9. For achievement queries, JOIN the 'achievements' table (which has player_id) with 'players' (which has username)
        10. In achievements table, 'tier' column indicates the level (e.g., 'gold', 'silver', 'bronze')
        11. For queries about 'legendary items', filter purchases with "WHERE pur.rarity = 'Legendary'"
        
        QUERY CONSTRUCTION RULES:
        - Return ONLY the raw SQL query with no explanations or comments
        - Do not use semicolons at the end
        - Always enclose text values in single quotes
        - Use table aliases for readability in JOINs (e.g., 'p' for players, 'pur' for purchases)
        - Limit results to 10 rows unless specifically asked for more
        - Order by relevant fields (e.g., most recent season for leaderboards)
        - For date/time queries, use date functions (e.g., datetime(purchase_date) > datetime('now', '-7 days'))
        - When looking up players by name, always use case-insensitive comparison (LOWER(p.username) = LOWER('PlayerName'))
        - Always check if tables need to be joined before querying (e.g., purchases need to join with players)
        
        User question: {question}
        SQL query:""")
        
        # Create direct SQL generation chain
        self.sql_gen_chain = LLMChain(
            llm=self.llm,
            prompt=self.sql_gen_prompt
        )
        
        # Add a debug print to show input query for troubleshooting
        self.debug = settings.DEBUG

        # Add a prompt for username detection
        self.username_detection_prompt = ChatPromptTemplate.from_template("""
        Analyze this query and determine if it already contains a specific username.
        
        Query: "{query}"
        
        In gaming contexts, usernames often have distinctive patterns like:
        - Words with numbers (e.g., DragonSlayer99, IceWarden42)
        - CamelCase combinations (e.g., ShadowNinja, BlazeRider)
        - Words with special characters (e.g., Dark_Knight, Fire-Mage)
        
        Does this query mention a specific player's username? 
        Respond with just YES or NO and the username if found (e.g., "YES: DragonSlayer99" or "NO").
        """)
        
        self.username_detector = LLMChain(
            llm=self.llm,
            prompt=self.username_detection_prompt
        )

    async def handle_combined_query(self, query: str) -> str:
        """Handle queries that request multiple pieces of information in one question."""
        print(f"Handling combined query: {query}")
        
        # Define patterns for common combined queries
        combined_patterns = [
            {
                "trigger": ["players", "clans"],
                "queries": [
                    "SELECT COUNT(*) FROM players",
                    "SELECT COUNT(*) FROM clans"
                ],
                "response_template": "There are {0} players and {1} clans in the database."
            },
            {
                "trigger": ["matches", "players"],
                "queries": [
                    "SELECT COUNT(*) FROM matches",
                    "SELECT COUNT(*) FROM players"
                ],
                "response_template": "There are {0} matches and {1} players recorded in the database."
            }
        ]
        
        # Check if query matches any combined pattern
        for pattern in combined_patterns:
            if all(word in query.lower() for word in pattern["trigger"]):
                try:
                    # Execute all queries in this pattern
                    results = []
                    for sql_query in pattern["queries"]:
                        print(f"Executing query: {sql_query}")
                        result = self.db.run(sql_query)
                        # Extract the count value - should be a single number
                        if isinstance(result, str) and result.isdigit():
                            results.append(result)
                        else:
                            # Try to get first row first column for COUNT queries
                            try:
                                count_value = result.strip().split('\n')[0]
                                results.append(count_value)
                            except:
                                results.append("unknown")
                    
                    # Format the response using the template and results
                    return pattern["response_template"].format(*results)
                except Exception as e:
                    print(f"Error handling combined query: {e}")
        
        # If we get here, no combined pattern matched or there was an error
        return None

    async def answer_query(self, query: str, user_context: Dict) -> str:
        # Log the incoming query for debugging
        if hasattr(self, 'debug') and self.debug and 'clan' in query.lower():
            print(f"[DEBUG] Dynamic Agent processing clan query: {query}")

        # First check if query contains personal references 
        has_personal_reference = any(ref in query.lower() for ref in ["my ", "me ", "i ", "mine"])
        
        # Only use LLM for username detection if we have personal references
        # or the query is about player-specific data
        needs_username_check = has_personal_reference or any(topic in query.lower() 
                               for topic in ["achievement", "rank", "status", "purchase", "level", "xp"])
        
        has_username = False
        detected_username = None
        
        if needs_username_check:
            # Use the LLM to detect if there's a username in the query
            detection_result = await self.username_detector.ainvoke({"query": query})
            
            # Extract result text
            if isinstance(detection_result, dict) and "text" in detection_result:
                detection_text = detection_result["text"].strip()
            else:
                detection_text = str(detection_result).strip()
                
            print(f"Username detection result: {detection_text}")
            
            # Check if a username was detected
            has_username = detection_text.startswith("YES")
            
            # Extract the detected username if present
            if has_username and ":" in detection_text:
                detected_username = detection_text.split(":", 1)[1].strip()
                print(f"Detected username: {detected_username}")
        
        # Request username if we have personal references but no detected username  
        if has_personal_reference and not has_username:
            # Return without executing - this will trigger a follow-up from the router
            print(f"Personalized query detected without specific username: {query}")
            return "This query requires specific player information. Please provide a username."

        # Use query directly without user context substitution
        enhanced_query = query
        
        try:
            # Check for combined queries first
            combined_response = await self.handle_combined_query(query)
            if combined_response:
                return combined_response

            # Generate SQL query with our simplified approach
            print(f"Generating SQL for query: {enhanced_query}")
            
            # Get SQL from LLM based on schema - no more hardcoded patterns
            sql_response = await self.sql_gen_chain.ainvoke({
                "question": enhanced_query,
                "db_schema": self.db_schema
            })
            
            if isinstance(sql_response, dict) and "text" in sql_response:
                sql_query = sql_response["text"].strip()
            else:
                sql_query = str(sql_response).strip()
            
            # Clean up before execution
            sql_query = self._clean_sql_query(sql_query)
            print(f"Generated SQL query: {sql_query}")
            
            # Execute the SQL query
            print(f"Executing SQL query: {sql_query}") 
            
            # Execute the SQL against our database
            sql_result = self.db.run(sql_query)
            
            print(f"SQL result: {sql_result}")
            
            # Generic handling for empty results
            if not sql_result.strip():
                # Extract player name if present - more carefully to avoid mistaking "List" as a player name
                # Common gaming usernames with CamelCase, numbers, or special characters
                player_pattern = r'\b(?!List\b|Show\b|Tell\b|Give\b|What\b|Who\b|How\b|Why\b|When\b|Where\b)([A-Z][a-zA-Z0-9]+)\b'
                player_matches = re.findall(player_pattern, query)
                
                # If we detect a username in enhanced_query (which might include follow-up info), use that instead
                if detected_username:
                    player_name = detected_username
                elif player_matches:
                    player_name = player_matches[0]
                else:
                    player_name = "the player"
                
                if "legendary items" in query.lower():
                    return f"I've checked our records, and it appears {player_name} hasn't purchased any legendary items yet."
                elif "achievements" in query.lower():
                    return f"I've checked our records, and it appears {player_name} hasn't earned any achievements yet."
                elif "purchases" in query.lower() or "items" in query.lower():
                    return f"I've checked our records, and it appears {player_name} hasn't made any purchases yet."
                else:
                    return "I've looked into your question, but I couldn't find any matching data in our records."

            # Generate a natural language response
            # Pass the original query using the key 'question'
            try:
                response = await self.response_chain.ainvoke({
                    "query": sql_query,
                    "result": sql_result,
                    "question": query
                })
            except KeyError as ke:
                print(f"KeyError in response chain: {ke}")
                # Try a simpler approach with just the result for fallback
                return f"Based on the data, here's what I found: {sql_result}"
            
            if isinstance(response, dict) and "text" in response:
                return response["text"]
            elif isinstance(response, str):
                return response
            else:
                return f"Based on the database, I found: {sql_result}"
                
        except KeyError as ke:
            print(f"KeyError in dynamic agent: {ke}")
            print(f"Query that caused error: {enhanced_query}")
            return "I encountered an issue understanding the keys. Please try rephrasing."
        except Exception as e:
            # Handle other errors gracefully
            print(f"Error in dynamic agent: {str(e)}")
            return "I encountered an error while retrieving that information. Please try rephrasing your question or contact support if the issue persists."
    
    def _clean_sql_query(self, query: str) -> str:
        """Clean the SQL query to avoid multiple statement execution issues."""
        # Remove any trailing semicolons
        query = query.strip().rstrip(';')
        
        # Split on semicolons and take only the first statement
        query = query.split(';')[0].strip()
        
        # Remove any LIMIT clause with semicolon
        query = re.sub(r'LIMIT\s+\d+\s*;', 'LIMIT 10', query, flags=re.IGNORECASE)
        
        return query 