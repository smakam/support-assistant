from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.chat_models import ChatOpenAI
from langchain.chains import ConversationalRetrievalChain
from pathlib import Path
from app.core.config import settings
from app.policies.rules import rules_block
from langchain.prompts import ChatPromptTemplate

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
Always follow the rules above and be concise and professional."""),
            ("human", "Question: {question}\nContext:\n{context}")
        ])
        # Use the custom prompt for RAG
        self.qa_chain = ConversationalRetrievalChain.from_llm(
            llm=self.llm,
            retriever=self.vector_store.as_retriever(),
            combine_docs_chain_kwargs={"prompt": qa_prompt},
            return_source_documents=True
        )

    def _initialize_vector_store(self):
        # Check if we have a saved vector store
        vector_store_path = Path(settings.VECTOR_STORE_PATH)
        if vector_store_path.exists():
            return FAISS.load_local(
                str(vector_store_path),
                self.embeddings,
                allow_dangerous_deserialization=True
            )

        # Create new vector store from knowledge base
        knowledge_base_path = Path(settings.KNOWLEDGE_BASE_PATH)
        with open(knowledge_base_path) as f:
            raw_text = f.read()

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        texts = text_splitter.split_text(raw_text)
        
        vector_store = FAISS.from_texts(
            texts,
            self.embeddings
        )
        
        # Save for future use
        vector_store.save_local(str(vector_store_path))
        return vector_store

    async def answer_query(self, query: str) -> str:
        response = await self.qa_chain.ainvoke({
            "question": query,
            "chat_history": []  # We could maintain chat history if needed
        })
        return response["answer"] 