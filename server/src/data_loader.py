from pathlib import Path
from typing import List, Dict, Any
from langchain_community.document_loaders import TextLoader
from langchain_core.documents import Document
import sys
import os

# Suppress TensorFlow oneDNN warnings
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.config import EXTRACTED_DATA_DIR, CATEGORIES


def load_all_documents(data_dir: str = None) -> List[Document]:
    """
    Load all text files from the categorized extracted data directory.
    Also loads any .txt files directly in the data_dir (like sample.txt).
    
    Args:
        data_dir: Optional custom data directory. If None, uses EXTRACTED_DATA_DIR from config.
    
    Returns:
        List of LangChain Document objects with metadata (category, filename, source)
    """
    # Use configured extracted data directory or custom path
    if data_dir is None:
        data_path = Path(EXTRACTED_DATA_DIR).resolve()
    else:
        data_path = Path(data_dir).resolve()
    
    print(f"[INFO] Loading documents from: {data_path}")
    documents = []
    
    # First, load any .txt files directly in the data_dir (like sample.txt)
    direct_txt_files = list(data_path.glob('*.txt'))
    if direct_txt_files:
        print(f"[INFO] Found {len(direct_txt_files)} text file(s) directly in data directory")
        for txt_file in direct_txt_files:
            try:
                loader = TextLoader(str(txt_file), encoding='utf-8')
                loaded_docs = loader.load()
                
                # Add basic metadata for non-categorized files
                for doc in loaded_docs:
                    doc.metadata['category'] = 'uncategorized'
                    doc.metadata['filename'] = txt_file.name
                    doc.metadata['source_path'] = str(txt_file)
                    doc.metadata['category_description'] = 'Uncategorized text file'
                
                documents.extend(loaded_docs)
                print(f"[DEBUG] Loaded: {txt_file.name} ({len(loaded_docs[0].page_content)} chars)")
                
            except Exception as e:
                print(f"[ERROR] Failed to load {txt_file}: {e}")
    
    # Then load text files from each category folder
    for category in CATEGORIES.keys():
        category_path = data_path / category
        
        if not category_path.exists():
            continue
        
        # Find all .txt files in this category
        txt_files = list(category_path.glob('*.txt'))
        print(f"[INFO] Found {len(txt_files)} text files in '{category}' category")
        
        for txt_file in txt_files:
            try:
                # Load the text file
                loader = TextLoader(str(txt_file), encoding='utf-8')
                loaded_docs = loader.load()
                
                # Add category metadata to each document
                for doc in loaded_docs:
                    doc.metadata['category'] = category
                    doc.metadata['filename'] = txt_file.name
                    doc.metadata['source_path'] = str(txt_file)
                    doc.metadata['category_description'] = CATEGORIES[category]['description']
                
                documents.extend(loaded_docs)
                print(f"[DEBUG] Loaded: {txt_file.name} ({len(loaded_docs[0].page_content)} chars)")
                
            except Exception as e:
                print(f"[ERROR] Failed to load {txt_file}: {e}")
    
    print(f"\n[SUCCESS] Total documents loaded: {len(documents)}")
    return documents


def load_documents_by_category(category: str, data_dir: str = None) -> List[Document]:
    """
    Load text files from a specific category only.
    
    Args:
        category: Category name (e.g., 'college_info', 'departments')
        data_dir: Optional custom data directory
    
    Returns:
        List of LangChain Document objects from that category
    """
    if category not in CATEGORIES:
        raise ValueError(f"Invalid category '{category}'. Valid categories: {list(CATEGORIES.keys())}")
    
    # Use configured extracted data directory or custom path
    if data_dir is None:
        data_path = Path(EXTRACTED_DATA_DIR).resolve()
    else:
        data_path = Path(data_dir).resolve()
    
    category_path = data_path / category
    
    if not category_path.exists():
        print(f"[WARNING] Category folder not found: {category_path}")
        return []
    
    documents = []
    txt_files = list(category_path.glob('*.txt'))
    print(f"[INFO] Loading {len(txt_files)} files from '{category}' category")
    
    for txt_file in txt_files:
        try:
            loader = TextLoader(str(txt_file), encoding='utf-8')
            loaded_docs = loader.load()
            
            for doc in loaded_docs:
                doc.metadata['category'] = category
                doc.metadata['filename'] = txt_file.name
                doc.metadata['source_path'] = str(txt_file)
                doc.metadata['category_description'] = CATEGORIES[category]['description']
            
            documents.extend(loaded_docs)
            
        except Exception as e:
            print(f"[ERROR] Failed to load {txt_file}: {e}")
    
    print(f"[SUCCESS] Loaded {len(documents)} documents from '{category}'")
    return documents


def get_category_statistics(data_dir: str = None) -> Dict[str, int]:
    """
    Get count of text files in each category.
    
    Args:
        data_dir: Optional custom data directory
    
    Returns:
        Dictionary with category names and file counts
    """
    if data_dir is None:
        data_path = Path(EXTRACTED_DATA_DIR).resolve()
    else:
        data_path = Path(data_dir).resolve()
    
    stats = {}
    
    for category in CATEGORIES.keys():
        category_path = data_path / category
        
        if category_path.exists():
            txt_files = list(category_path.glob('*.txt'))
            stats[category] = len(txt_files)
        else:
            stats[category] = 0
    
    return stats


# Example usage
if __name__ == "__main__":
    print("="*60)
    print("COLLEGE AI - DATA LOADER")
    print("="*60)
    
    # Show statistics
    print("\n📊 Category Statistics:")
    stats = get_category_statistics()
    for category, count in stats.items():
        print(f"  {category:20s}: {count:4d} files")
    
    # Load all documents
    print(f"\n📂 Loading all documents...")
    docs = load_all_documents()
    
    if docs:
        print(f"\n✅ Successfully loaded {len(docs)} documents")
        print(f"\n📄 Example document:")
        print(f"  Category: {docs[0].metadata['category']}")
        print(f"  Filename: {docs[0].metadata['filename']}")
        print(f"  Content preview: {docs[0].page_content[:200]}...")
        
        # Test loading by category
        print(f"\n📂 Loading 'departments' category only...")
        dept_docs = load_documents_by_category('departments')
        print(f"  Loaded {len(dept_docs)} department documents")
    else:
        print("\n⚠️  No documents found. Run the pipeline first: python -m src.main")