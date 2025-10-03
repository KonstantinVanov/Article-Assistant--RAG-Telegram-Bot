import os
import logging
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import FAISS

load_dotenv()
logger = logging.getLogger(__name__)

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    logger.error("OPENAI_API_KEY not found in environment variables!")
else:
    logger.info("OpenAI API key loaded successfully")

embeddings = OpenAIEmbeddings(
    model="text-embedding-3-small",
    api_key=api_key,
    base_url="https://api.proxyapi.ru/openai/v1"
) if api_key else None

prompt_template = ChatPromptTemplate.from_template(
    """Expert Research Assistant Guidelines:

1. Source Accuracy:
   - Strictly use ONLY the provided context
   - For missing info: "The article doesn't specify"
   - Never hallucinate facts

2. Response Structure:
   - Core Answer (1 bolded sentence)
   - Key Evidence (3-5 bullet points max)
   - Practical Implications (when relevant)
   - Limitations (if data is incomplete)

3. Technical Content:
   - Code: ```python\n...\n``` 
   - Formulas: $E=mc^2$ format
   - Terms: "API (Application Programming Interface)"

4. Language Rules:
   - Match question's language
   - Auto-correct grammar subtly
   - Use ISO standards for dates/units

Context:
{context}

Question: {question}"""

)

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
        
        vector_store = get_vector_store()
        if not vector_store:
            return "❌ System error: Knowledge base not available"
        
        retrieved_docs = vector_store.similarity_search(question, k=4)
        
        if not retrieved_docs:
            logger.warning("No relevant documents found")
            return "❌ No relevant information found in knowledge base."
        
        docs_content = "\n\n---\n\n".join([
            f"Document {i+1}:\n{doc.page_content}" 
            for i, doc in enumerate(retrieved_docs)
        ])
        
        formatted_prompt = prompt_template.format(
            question=question,
            context=docs_content
        )
        
        logger.info("Generating answer with LLM...")
        response = llm.invoke(formatted_prompt)
        return response.content
    
    except Exception as e:
        error_msg = f"Error processing question: {str(e)}"
        logger.exception(error_msg)
        return f"❌ {error_msg}"
