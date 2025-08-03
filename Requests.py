import os
import logging
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import FAISS
from dotenv import load_dotenv
from pathlib import Path
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Verify API key exists
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    logger.error("OPENAI_API_KEY not found in environment variables!")
else:
    logger.info("OpenAI API key loaded successfully")

# Initialize embeddings model
embeddings = OpenAIEmbeddings(
    model="text-embedding-3-small",
    api_key=api_key,
    base_url="https://api.proxyapi.ru/openai/v1"
) if api_key else None

# Prompt template for answer generation
prompt_template = ChatPromptTemplate.from_template(
    """You are a helpful assistant answering questions about an article. 
Use only the provided context to answer. If the answer isn't in the context, 
politely say you don't know.

Context:
{context}

Question: {question}
"""
)

# Initialize language model
llm = ChatOpenAI(
    model='gpt-4o-mini',
    api_key=api_key,
    base_url="https://api.proxyapi.ru/openai/v1",
    temperature=0.3
) if api_key else None

def get_vector_store():
    """Returns initialized vector store with fresh data"""
    try:
        logger.info("Loading FAISS vector store...")
        vector_store = FAISS.load_local(
            folder_path="./faiss_index",
            embeddings=embeddings,
            allow_dangerous_deserialization=True
        )
        logger.info("Vector store loaded successfully")
        return vector_store
    except Exception as e:
        logger.error(f"Vector store loading failed: {str(e)}")
        return None

def answer(question: str) -> str:
    """Generates an answer to a question based on indexed article"""
    try:
        if not api_key:
            return "❌ System error: OpenAI API key is missing"
        
        if not llm:
            return "❌ System error: Language model not initialized"
        
        logger.info(f"Processing question: '{question}'")
        
        # Always get fresh vector store to ensure latest data
        vector_store = get_vector_store()
        if not vector_store:
            return "❌ System error: Knowledge base not available"
        
        # Retrieve relevant documents
        retrieved_docs = vector_store.similarity_search(question, k=4)
        
        if not retrieved_docs:
            logger.warning("No relevant documents found")
            return "❌ No relevant information found in knowledge base."
        
        # Combine document content
        docs_content = "\n\n---\n\n".join([
            f"Document {i+1}:\n{doc.page_content}" 
            for i, doc in enumerate(retrieved_docs)
        ])
        
        # Format prompt
        formatted_prompt = prompt_template.format(
            question=question,
            context=docs_content
        )
        
        # Generate answer
        logger.info("Generating answer with LLM...")
        response = llm.invoke(formatted_prompt)
        return response.content
    
    except Exception as e:
        error_msg = f"Error processing question: {str(e)}"
        logger.exception(error_msg)
        return f"❌ {error_msg}"

if __name__ == "__main__":
    print("\nTesting Requests.py module\n")
    
    if not api_key:
        print("❌ OpenAI API key is missing")
    else:
        print("✅ OpenAI API key loaded successfully")
    
    try:
        store = get_vector_store()
        if store:
            print("✅ Vector store loaded successfully")
            test_docs = store.similarity_search("test", k=1)
            print(f"Test query returned {len(test_docs)} documents")
        else:
            print("❌ Vector store not initialized")
    except Exception as e:
        print(f"❌ Store loading error: {str(e)}")