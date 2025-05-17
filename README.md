# KGen AI Support Assistant

A conversational AI support assistant for gaming support, capable of answering questions about game mechanics, player stats, clan information, and more.

## Features

- **Multi-agent architecture** for handling different types of questions
- **Combined data & knowledge retrieval** for comprehensive answers
- **Follow-up capabilities** for ambiguous queries
- **Feedback system** to collect user input on answer quality
- **Sample questions** for quick testing
- **LangSmith integration** for observability and debugging

## Project Structure

- **Backend**: FastAPI server with AI agents
- **Frontend**: Streamlit chat interface
- **Database**: SQLite with gaming support data
- **Observability**: LangSmith tracing and evaluation

## Setup Instructions

### Local Development

1. **Clone the repository**

   ```
   git clone https://github.com/yourusername/kgen-support-assistant.git
   cd kgen-support-assistant
   ```

2. **Set up a virtual environment**

   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**

   ```
   pip install -r requirements.txt
   ```

4. **Set up environment variables**

   - Create a `.env` file in the root directory
   - Add the following variables:

     ```
     OPENAI_API_KEY=your_openai_api_key
     DATABASE_URL=sqlite:///kgen_gaming_support_advanced.db

     # Optional LangSmith configuration for observability
     LANGCHAIN_API_KEY=your_langsmith_api_key
     LANGCHAIN_PROJECT=gaming-support-assistant
     LANGCHAIN_TRACING_V2=true
     ```

5. **Run the backend server**

   ```
   uvicorn app.main:app --reload --port 8000
   ```

6. **Run the frontend**

   ```
   cd frontend
   streamlit run streamlit_app.py
   ```

7. **Access the application**
   - Backend API: http://localhost:8000
   - Frontend: http://localhost:8501
   - LangSmith Dashboard: https://smith.langchain.com/

## Deployment Options

### Backend Deployment (Render)

1. **Sign up for Render** (https://render.com)
2. **Create a new Web Service**
   - Connect your GitHub repository
   - Set build command: `pip install -r requirements.txt`
   - Set start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - Add environment variables (OPENAI_API_KEY, etc.)

### Frontend Deployment (Streamlit Cloud)

1. **Sign up for Streamlit Cloud** (https://streamlit.io/cloud)
2. **Deploy your app**
   - Connect your GitHub repository
   - Set the main file path: `frontend/streamlit_app.py`
   - Set required secrets (API_URL, DEMO_TOKEN)

### Database Options

- **Development**: SQLite (included)
- **Production**: Consider migrating to PostgreSQL for better performance and scalability

## API Documentation

Once the backend is running, visit:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Using the Feedback System

The application includes a feedback system that allows users to:

1. Rate responses with thumbs up/down
2. Provide detailed feedback on negative ratings
3. Track feedback in JSON files (stored in the `feedback` directory)

This feedback can be used to improve the AI responses over time.

## Environment Configuration

### Development vs Production

The application uses different settings for development and production:

- **Development**: Local server with debug mode
- **Production**: Remote servers with optimized settings

To switch between environments, set the `ENVIRONMENT` variable to either `development` or `production` in your `.env` file.

## LangSmith Integration

The application integrates with LangSmith for enhanced observability, debugging, and evaluation of AI conversations. See [docs/langsmith.md](docs/langsmith.md) for detailed instructions on:

- Setting up LangSmith for your development environment
- Using traces to debug conversation flows
- Monitoring LLM performance metrics
- Evaluating and improving agent responses

LangSmith helps identify issues with:

- Query classification
- Conversation context handling
- Support ticket creation processes
- End-to-end conversation flows

## License

[MIT License](LICENSE)

## Credits

Built with:

- OpenAI's GPT models
- FastAPI
- Streamlit
- LangChain
- LangSmith
