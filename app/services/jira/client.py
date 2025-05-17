from jira import JIRA
from app.core.config import settings
import os
import re

class JiraClient:
    def __init__(self):
        # Get Jira config directly from .env file
        env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), '.env')
        jira_config = self._read_env_file(env_path)
        
        # Debug prints for Jira config
        print("JIRA CONFIG FROM DIRECT .ENV READ:")
        print("JIRA_SERVER:", jira_config.get('JIRA_SERVER', 'NOT FOUND'))
        print("JIRA_EMAIL:", jira_config.get('JIRA_EMAIL', 'NOT FOUND'))
        print("JIRA_API_TOKEN:", jira_config.get('JIRA_API_TOKEN', 'NOT FOUND'))
        print("JIRA_PROJECT_KEY:", jira_config.get('JIRA_PROJECT_KEY', 'NOT FOUND'))
        
        # Skip Pydantic settings completely and use our direct .env reading
        self.server = jira_config.get('JIRA_SERVER')
        self.email = jira_config.get('JIRA_EMAIL')
        self.api_token = jira_config.get('JIRA_API_TOKEN')
        self.project_key = jira_config.get('JIRA_PROJECT_KEY')
        print("Using direct .env reading for Jira config")
        
        # Initialize Jira client
        if not self.server or self.server == 'https://your-instance.atlassian.net':
            print("WARNING: Invalid JIRA_SERVER value, Jira integration will not work!")
            self.client = None
        else:
            try:
                self.client = JIRA(
                    server=self.server,
                    basic_auth=(self.email, self.api_token)
                )
                print(f"Jira client initialized with server: {self.server}")
            except Exception as e:
                print(f"Failed to initialize Jira client: {e}")
                self.client = None

    def _read_env_file(self, env_path):
        """Read .env file directly and extract variables"""
        config = {}
        try:
            if os.path.exists(env_path):
                with open(env_path, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            key_value = line.split('=', 1)
                            if len(key_value) == 2:
                                key, value = key_value
                                config[key.strip()] = value.strip().strip('"\'')
                print(f"Successfully read .env file: {env_path}")
            else:
                print(f".env file not found at: {env_path}")
                
            # Also try to read from environment variables
            for key in ['JIRA_SERVER', 'JIRA_EMAIL', 'JIRA_API_TOKEN', 'JIRA_PROJECT_KEY']:
                if key in os.environ and key not in config:
                    config[key] = os.environ[key]
                    
        except Exception as e:
            print(f"Error reading .env file: {e}")
        return config

    async def create_ticket(self, summary: str, description: str, issue_type: str = "Task") -> str:
        if not self.client:
            print("Jira client not initialized, returning dummy ticket")
            return "JIRA_DISABLED"
            
        try:
            # For debugging, print available project issue types
            try:
                project_meta = self.client.createmeta(projectKeys=self.project_key)
                issue_types = []
                if project_meta.get('projects') and len(project_meta['projects']) > 0:
                    issue_types = [it['name'] for it in project_meta['projects'][0].get('issuetypes', [])]
                    print(f"Available issue types in project {self.project_key}: {issue_types}")
                
                # If specified issue_type is not available, use the first available type
                if issue_types and issue_type not in issue_types:
                    print(f"Issue type '{issue_type}' not available. Using '{issue_types[0]}' instead.")
                    issue_type = issue_types[0]
            except Exception as e:
                print(f"Could not retrieve issue types: {e}. Will try with '{issue_type}' anyway.")
            
            # Clean up the description
            # Remove leading whitespace from each line while preserving formatting
            cleaned_description = []
            for line in description.split("\n"):
                cleaned_description.append(line.lstrip())
            description = "\n".join(cleaned_description)
            
            # Add special formatting for section headers to make them stand out in Jira
            description = description.replace("=== USER INFORMATION ===", "*USER INFORMATION*")
            description = description.replace("=== ESCALATION QUERY ===", "*ESCALATION QUERY*")
            description = description.replace("=== CONVERSATION HISTORY ===", "*CONVERSATION HISTORY*")
            description = description.replace("=== TECHNICAL INFO ===", "*TECHNICAL INFO*")
            
            # Add horizontal lines to separate sections
            description = description.replace("*USER INFORMATION*", "----\n*USER INFORMATION*\n----")
            description = description.replace("*ESCALATION QUERY*", "----\n*ESCALATION QUERY*\n----")
            description = description.replace("*CONVERSATION HISTORY*", "----\n*CONVERSATION HISTORY*\n----")
            description = description.replace("*TECHNICAL INFO*", "----\n*TECHNICAL INFO*\n----")
            
            # Add note about conversation history at the top of the description
            history_tag = ""
            if "CONVERSATION HISTORY" in description and "[1]" in description:
                history_tag = "[Includes Full Conversation History]"
            elif "CONVERSATION HISTORY" in description:
                history_tag = "[Includes Conversation Data]"
                
            if history_tag:
                description = f"{history_tag}\n\n{description}"
            
            print(f"Creating JIRA ticket with description length: {len(description)}")
            
            issue_dict = {
                'project': {'key': self.project_key},
                'summary': summary,
                'description': description,
                'issuetype': {'name': issue_type},
            }
            print(f"Creating JIRA ticket with issue type: '{issue_type}'")
            
            issue = self.client.create_issue(fields=issue_dict)
            print(f"Successfully created Jira ticket: {issue.key}")
            return issue.key
            
        except Exception as e:
            print(f"Error creating JIRA ticket: {str(e)}")
            # Return a dummy ticket ID in case of failure
            return "ERROR-123" 