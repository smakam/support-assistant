from jira import JIRA
from app.core.config import settings

class JiraClient:
    def __init__(self):
        self.client = JIRA(
            server=settings.JIRA_SERVER,
            basic_auth=(settings.JIRA_EMAIL, settings.JIRA_API_TOKEN)
        )
        self.project_key = settings.JIRA_PROJECT_KEY

    async def create_ticket(self, summary: str, description: str, issue_type: str = "Support") -> str:
        try:
            issue_dict = {
                'project': {'key': self.project_key},
                'summary': summary,
                'description': description,
                'issuetype': {'name': issue_type},
            }
            
            issue = self.client.create_issue(fields=issue_dict)
            return issue.key
            
        except Exception as e:
            print(f"Error creating JIRA ticket: {str(e)}")
            # Return a dummy ticket ID in case of failure
            return "ERROR-123" 