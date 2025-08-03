import os
import logging
import bs4
from langchain_community.document_loaders import WebBaseLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
logger = logging.getLogger(__name__)

def reindex(link: str) -> int:
    try:
        # Configure parser
        strainer = bs4.SoupStrainer(class_={"post-title", "post-header", "post-content"})
        
        # Load document
        logger.info(f"📥 Loading article: {link}")
        loader = WebBaseLoader(
            web_paths=(link,),
            bs_kwargs={"parse_only": strainer}
        )
        docs = loader.load()
        
        if not docs or not docs[0].page_content.strip():
            raise ValueError("No content found in the article")
        
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

if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO)
    
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        url = "https://lilianweng.github.io/posts/2024-11-28-reward-hacking/"
    
    try:
        num_chunks = reindex(url)
        print(f"🎉 Article successfully indexed! Processed chunks: {num_chunks}")
    except Exception as e:
        print(f"❌ Indexing error: {str(e)}")
        sys.exit(1)