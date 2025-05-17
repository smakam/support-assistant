from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter, CharacterTextSplitter
from langchain_openai import ChatOpenAI
from langchain.chains import ConversationalRetrievalChain
from pathlib import Path
from app.core.config import settings
from app.policies.rules import rules_block
from langchain.prompts import ChatPromptTemplate
from langsmith import traceable
import logging

logger = logging.getLogger("uvicorn.error")

class StaticKnowledgeAgent:
    def __init__(self):
        self.embeddings = OpenAIEmbeddings(
            openai_api_key=settings.OPENAI_API_KEY
        )
        self.llm = ChatOpenAI(
            api_key=settings.OPENAI_API_KEY,
            temperature=0
        )
        self.vector_store = self._initialize_vector_store()
        
        # Build a custom QA prompt that includes shared agent rules
        qa_prompt = ChatPromptTemplate.from_messages([
            ("system", f"""{rules_block()}

You are an AI assistant answering questions using the provided knowledge base.
Always follow the rules above and be concise and professional.

IMPORTANT: Your answer MUST be based ONLY on the retrieved context provided below.

CRITICAL INSTRUCTIONS:
1. If the context contains ANY relevant information, use it to provide a partial answer
2. Even if you cannot answer the question completely, provide whatever relevant information exists in the context
3. If the context mentions features, characteristics, or information about a topic, include those details
4. DO NOT say "I don't have enough information" if the context contains ANY relevant details
5. If the context mentions a category (like a clan type) and contains information about that category, connect those pieces
6. If the question has multiple parts, answer the parts you can based on the context

Only respond based on the facts in the context provided. If the context doesn't 
provide ANY information about the topic, only then say "I don't have enough information about that."
NEVER generate information not contained in the context."""),
            ("human", "Question: {question}\nContext:\n{context}")
        ])
        
        # Configure retriever for better performance
        retriever = self.vector_store.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 2}  # Limit to top 2 most relevant chunks only
        )
        
        # Use the standard chain but with our improved prompt and retriever
        self.qa_chain = ConversationalRetrievalChain.from_llm(
            llm=self.llm,
            retriever=retriever,
            combine_docs_chain_kwargs={"prompt": qa_prompt},
            return_source_documents=True,
            verbose=True  # Enable verbose mode for debugging
        )

    @traceable(name="initialize_vector_store")
    def _initialize_vector_store(self):
        # Check if we have a saved vector store
        vector_store_path = Path(settings.VECTOR_STORE_PATH)
        if vector_store_path.exists():
            logger.info(f"Loading existing vector store from {vector_store_path}")
            return FAISS.load_local(
                str(vector_store_path),
                self.embeddings,
                allow_dangerous_deserialization=True
            )

        # Create new vector store from knowledge base
        knowledge_base_path = Path(settings.KNOWLEDGE_BASE_PATH)
        logger.info(f"Creating new vector store from {knowledge_base_path}")
        with open(knowledge_base_path) as f:
            raw_text = f.read()

        # Process one bullet point at a time for precise retrieval
        lines = raw_text.split('\n')
        texts = []
        
        for line in lines:
            if line.strip().startswith('- '):
                texts.append(line.strip())
        
        logger.info(f"Split knowledge base into {len(texts)} individual bullet points")
        for i, text in enumerate(texts):
            logger.info(f"Bullet point {i+1}: {text}")
        
        vector_store = FAISS.from_texts(
            texts,
            self.embeddings
        )
        
        # Save for future use
        vector_store.save_local(str(vector_store_path))
        return vector_store

    @traceable(name="answer_static_query")
    async def answer_query(self, query: str) -> str:
        logger.info(f"Static agent processing query: {query}")
        
        # First, directly retrieve documents to log what's being retrieved
        docs = self.vector_store.similarity_search(query, k=2)
        logger.info(f"Retrieved {len(docs)} documents from vector store")
        
        if not docs:
            return "I don't have information about that in my knowledge base."
        
        # Log the retrieved documents for debugging
        for i, doc in enumerate(docs):
            logger.info(f"Relevant document {i+1}: {doc.page_content}")
        
        # Now use the chain to get the answer
        response = await self.qa_chain.ainvoke({
            "question": query,
            "chat_history": []  # We could maintain chat history if needed
        })
        
        # Log which documents were actually used
        if "source_documents" in response:
            logger.info(f"Chain used {len(response['source_documents'])} source documents")
            for i, doc in enumerate(response["source_documents"]):
                logger.info(f"Source document {i+1}: {doc.page_content}")
        
        return response["answer"] 