# LangSmith Integration

This project uses [LangSmith](https://smith.langchain.com/) for observability, debugging, and evaluation of LLM calls.

## Setup

1. Sign up for a LangSmith account at [smith.langchain.com](https://smith.langchain.com/).
2. Get your API key from the LangSmith dashboard.
3. Add the following environment variables to your `.env` file:

```
LANGCHAIN_API_KEY=your_langsmith_api_key_here
LANGCHAIN_PROJECT=gaming-support-assistant
LANGCHAIN_TRACING_V2=true
```

## Viewing Traces

Once you've set up LangSmith and run your application:

1. Go to [smith.langchain.com](https://smith.langchain.com/)
2. Navigate to the "Traces" section
3. Select the "gaming-support-assistant" project (or your custom project name)
4. You'll see all traced operations organized by run ID

## Key Traced Components

The following components are automatically traced:

- API endpoints in `app/api/v1/endpoints/support.py`
- Query routing in `app/services/agents/router.py`
- LLM calls in all chains and agents
- Support ticket creation with Jira

## Adding Custom Traces

You can add custom traces to any function by using the `@traceable` decorator:

```python
from langsmith import traceable

@traceable(name="my_function_name")
def my_function():
    # Your code here
    pass
```

## Debugging with LangSmith

When debugging issues:

1. Check the traces for the specific user query
2. Examine inputs and outputs of each step
3. Identify where the flow deviated from expected behavior
4. Use the LangSmith UI to explore the detailed properties of each step

## Performance Monitoring

LangSmith provides metrics on:

- Latency of each step in the pipeline
- Token usage per LLM call
- Success rates of different operations

These can be viewed in the LangSmith dashboard.

## Feedback and Evaluation

User feedback submitted through the interface is automatically tracked with the corresponding trace, helping you identify which types of queries need improvement.
