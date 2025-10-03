import os
import logging
import bs4
import tiktoken
from dotenv import load_dotenv
from langchain_community.document_loaders import WebBaseLoader, PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings

load_dotenv()
logger = logging.getLogger(__name__)

def _clean_html(content: str) -> str:
    """Remove unnecessary HTML tags and scripts while preserving main content."""
    soup = bs4.BeautifulSoup(content, "html.parser")
    
    for element in soup(["script", "style", "nav", "footer", "iframe", "aside", "header", "meta", "link"]):
        element.decompose()
    
    return soup.get_text(separator="\n", strip=True)

def _count_tokens(text: str, model: str = "text-embedding-3-small") -> int:
    """Count tokens in text for a specific model."""
    try:
        encoding = tiktoken.encoding_for_model(model)
        return len(encoding.encode(text))
    except:
        return len(text) // 4

def _validate_file_source(source: str) -> None:
    """Validate file source before processing."""
    if not os.path.exists(source):
        raise FileNotFoundError(f"File not found: {source}")
    
    file_ext = source.split('.')[-1].lower()
    if file_ext not in ['pdf', 'txt']:
        raise ValueError(f"Unsupported file format: {file_ext}. Use PDF or TXT")
    
    file_size = os.path.getsize(source)
    if file_size == 0:
        raise ValueError("File is empty")
    
    MAX_FILE_SIZE = 20 * 1024 * 1024
    if file_size > MAX_FILE_SIZE:
        raise ValueError(f"File too large ({file_size/1024/1024:.1f}MB). Max size: 20MB")

def _split_large_document(docs, max_tokens=250000):
    """Split document into smaller parts if it exceeds token limit."""
    if not docs:
        return docs
    
    total_tokens = _count_tokens(docs[0].page_content)
    
    if total_tokens <= max_tokens:
        return docs
    
    logger.warning(f"Document too large ({total_tokens} tokens). Splitting into smaller parts...")
    
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=100,
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    
    splits = text_splitter.split_documents(docs)
    
    final_splits = []
    for split in splits:
        split_tokens = _count_tokens(split.page_content)
        if split_tokens > max_tokens:
            sentences = split.page_content.split('. ')
            current_chunk = ""
            for sentence in sentences:
                sentence_tokens = _count_tokens(sentence)
                if _count_tokens(current_chunk) + sentence_tokens > max_tokens:
                    if current_chunk:
                        new_doc = type(split)(page_content=current_chunk, metadata=split.metadata.copy())
                        final_splits.append(new_doc)
                    current_chunk = sentence
                else:
                    current_chunk += ". " + sentence if current_chunk else sentence
            if current_chunk:
                new_doc = type(split)(page_content=current_chunk, metadata=split.metadata.copy())
                final_splits.append(new_doc)
        else:
            final_splits.append(split)
    
    logger.info(f"Split large document into {len(final_splits)} parts")
    return final_splits

def reindex(source: str) -> int:
    """Reindex content from URL or file."""
    try:
        if source.startswith(('http://', 'https://')):
            logger.info(f"📥 Loading article: {source}")
            
            loader = WebBaseLoader(
                web_paths=(source,),
                requests_kwargs={
                    "headers": {
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                    }
                }
            )
            
            docs = loader.load()
            
            if docs:
                docs[0].page_content = _clean_html(docs[0].page_content)
        else:
            _validate_file_source(source)
            file_ext = source.split('.')[-1].lower()
            
            if file_ext == 'pdf':
                logger.info(f"📥 Loading PDF file: {source}")
                loader = PyPDFLoader(source)
                docs = loader.load()
            
            elif file_ext == 'txt':
                logger.info(f"📥 Loading TXT file: {source}")
                loader = TextLoader(source, encoding='utf-8', autodetect_encoding=True)
                docs = loader.load()
        
        if not docs:
            raise ValueError("No documents were loaded")
            
        if not docs[0].page_content.strip():
            raise ValueError("No content found in the document")
        
        docs = _split_large_document(docs, max_tokens=250000)
        
        total_tokens = sum(_count_tokens(doc.page_content) for doc in docs)
        logger.info(f"📄 Loaded document with {total_tokens} total tokens")
        
        logger.info("✂️ Splitting document into chunks...")
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=800,
            chunk_overlap=150,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        splits = text_splitter.split_documents(docs)
        
        if not splits:
            raise ValueError("No chunks were created after splitting")
        
        logger.info(f"Created {len(splits)} chunks")
        
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY not found in environment variables")
        
        embeddings = OpenAIEmbeddings(
            model="text-embedding-3-small",
            api_key=api_key,
            base_url="https://api.proxyapi.ru/openai/v1",
            chunk_size=100
        )
        
        logger.info("📊 Creating FAISS vector store...")
        
        if len(splits) > 1000:
            logger.info(f"Processing {len(splits)} chunks in batches...")
            batch_size = 500
            vector_store = None
            
            for i in range(0, len(splits), batch_size):
                batch = splits[i:i + batch_size]
                logger.info(f"Processing batch {i//batch_size + 1}/{(len(splits)-1)//batch_size + 1}")
                
                if vector_store is None:
                    vector_store = FAISS.from_documents(batch, embeddings)
                else:
                    vector_store.add_documents(batch)
        else:
            vector_store = FAISS.from_documents(splits, embeddings)
        
        index_dir = "./faiss_index"
        os.makedirs(index_dir, exist_ok=True)
        
        logger.info("💾 Saving vector store...")
        vector_store.save_local(index_dir)
        
        logger.info(f"✅ Created vector store with {len(splits)} chunks")
        return len(splits)
        
    except Exception as e:
        logger.error(f"Indexing failed: {str(e)}")
        raise RuntimeError(f"Indexing failed: {str(e)}")

def get_index_info() -> dict:
    """Get information about the current index."""
    index_dir = "./faiss_index"
    
    if not os.path.exists(index_dir):
        return None
    
    try:
        index_files = [f for f in os.listdir(index_dir) if f.endswith('.faiss') or f.endswith('.pkl')]
        if not index_files:
            return None
            
        total_size = sum(os.path.getsize(os.path.join(index_dir, f)) for f in os.listdir(index_dir))
        
        return {
            "exists": True,
            "file_count": len(index_files),
            "total_size": total_size,
            "path": os.path.abspath(index_dir)
        }
        
    except Exception as e:
        logger.error(f"Error getting index info: {str(e)}")
        return None

def clear_index() -> bool:
    """Clear the FAISS index."""
    try:
        index_dir = "./faiss_index"
        if os.path.exists(index_dir):
            for file in os.listdir(index_dir):
                file_path = os.path.join(index_dir, file)
                if os.path.isfile(file_path):
                    os.remove(file_path)
            logger.info("✅ Index cleared successfully")
            return True
        return False
    except Exception as e:
        logger.error(f"Error clearing index: {str(e)}")
        return False
