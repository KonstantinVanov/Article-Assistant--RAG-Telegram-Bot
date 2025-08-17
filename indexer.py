import os
import logging
import bs4
from langchain_community.document_loaders import WebBaseLoader, PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
load_dotenv()
logger = logging.getLogger(__name__)

def _clean_html(content: str) -> str:
    """Remove unnecessary HTML tags and scripts while preserving main content."""
    soup = bs4.BeautifulSoup(content, "html.parser")
    
    # Remove unwanted elements (adjust as needed)
    for element in soup(["script", "style", "nav", "footer", "iframe", "aside"]):
        element.decompose()
    
    # Get text from remaining elements
    return soup.get_text(separator="\n", strip=True)

def reindex(source: str) -> int:
    try:
        # Determine if source is URL or file path
        if source.startswith(('http://', 'https://')):
            # Universal web article processing
            logger.info(f"📥 Loading article: {source}")
            
            # Load with headers to mimic browser request
            loader = WebBaseLoader(
                web_paths=(source,),
                requests_kwargs={
                    "headers": {
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                    }
                }
            )
            
            docs = loader.load()
            
            # Clean HTML content for better processing
            if docs:
                docs[0].page_content = _clean_html(docs[0].page_content)
        else:
            # PDF file processing (unchanged)
            if not os.path.exists(source):
                raise FileNotFoundError(f"File not found: {source}")
            
            if not source.lower().endswith('.pdf'):
                raise ValueError("Only PDF files are supported")
                
            logger.info(f"📥 Loading PDF file: {source}")
            loader = PyPDFLoader(source)
            docs = loader.load()
        
        if not docs or not docs[0].page_content.strip():
            raise ValueError("No content found in the document")
        
        # Split text
        logger.info("✂️ Splitting document...")
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        splits = text_splitter.split_documents(docs)
        
        # Initialize embeddings
        embeddings = OpenAIEmbeddings(
            model="text-embedding-3-small",
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url="https://api.proxyapi.ru/openai/v1"
        )
        
        # Create FAISS vector store
        logger.info("📊 Creating FAISS vector store...")
        vector_store = FAISS.from_documents(splits, embeddings)
        
        # Save to disk
        logger.info("💾 Saving vector store...")
        vector_store.save_local("./faiss_index")
        
        logger.info(f"✅ Created vector store with {len(splits)} chunks")
        return len(splits)
        
    except Exception as e:
        logger.error(f"Indexing failed: {str(e)}")
        raise RuntimeError(f"Indexing failed: {str(e)}")