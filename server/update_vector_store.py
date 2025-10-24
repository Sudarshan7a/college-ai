"""
Update Vector Store with New Data
Add new documents from data_23_10_25 to the vector store
"""
import os
import shutil
from pathlib import Path
from src.vector_store import build_vector_store_from_all_documents, FAISS_STORE_DIR
from src.data_loader import load_all_documents
from src.config import BASE_PATH, EXTRACTED_DATA_DIR

def copy_new_data():
    """Copy new data from data_23_10_25 to server/data/extracted/"""
    
    # Source: server/data_23_10_25
    source_dir = Path(BASE_PATH) / "data_23_10_25"
    
    # Destination: server/data/extracted
    dest_dir = Path(EXTRACTED_DATA_DIR)
    
    if not source_dir.exists():
        print(f"❌ Source directory not found: {source_dir}")
        return False
    
    print(f"📂 Source: {source_dir}")
    print(f"📂 Destination: {dest_dir}")
    print("\n" + "="*60)
    print("COPYING NEW DATA")
    print("="*60)
    
    copied_files = 0
    categories = set()
    
    # Walk through all files in source directory
    for category_dir in source_dir.iterdir():
        if not category_dir.is_dir():
            continue
            
        category = category_dir.name
        categories.add(category)
        
        # Create destination category directory if it doesn't exist
        dest_category_dir = dest_dir / category
        dest_category_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy all files from this category
        for file_path in category_dir.iterdir():
            if file_path.is_file():
                dest_file = dest_category_dir / file_path.name
                
                # Copy file
                shutil.copy2(file_path, dest_file)
                copied_files += 1
                print(f"  ✅ {category}/{file_path.name}")
    
    print(f"\n✅ Copied {copied_files} files across {len(categories)} categories")
    print(f"   Categories: {', '.join(sorted(categories))}")
    return True


def rebuild_vector_store():
    """Rebuild the vector store with documents from BOTH directories"""
    print("\n" + "="*60)
    print("REBUILDING VECTOR STORE WITH COMBINED DATA")
    print("="*60)
    
    # Load documents from BOTH directories
    print("📂 Loading documents from multiple sources...")
    
    # 1. Load from existing extracted data
    print(f"  📁 Source 1: {EXTRACTED_DATA_DIR}")
    docs_existing = load_all_documents(EXTRACTED_DATA_DIR)
    print(f"     ✅ Loaded {len(docs_existing)} documents from existing data")
    
    # 2. Load from new data directory  
    new_data_dir = Path(BASE_PATH) / "data_23_10_25"
    print(f"  📁 Source 2: {new_data_dir}")
    docs_new = load_all_documents(str(new_data_dir))
    print(f"     ✅ Loaded {len(docs_new)} documents from new data")
    
    # 3. Combine all documents
    all_documents = docs_existing + docs_new
    print(f"\n📊 Total combined documents: {len(all_documents)}")
    
    # Show breakdown by category
    categories = {}
    for doc in all_documents:
        cat = doc.metadata.get('category', 'unknown')
        categories[cat] = categories.get(cat, 0) + 1
    
    print("\n📈 Documents by category:")
    for cat, count in sorted(categories.items()):
        print(f"  • {cat}: {count} files")
    
    # 4. Build vector store with combined documents
    print(f"\n🔨 Building vector store with {len(all_documents)} documents...")
    
    from src.vector_store import FaissVectorStore
    store = FaissVectorStore(persist_dir=FAISS_STORE_DIR)
    store.build_from_documents(all_documents, clean_text=True)
    
    if store:
        print("\n" + "="*60)
        print("✅ COMBINED VECTOR STORE CREATED SUCCESSFULLY!")
        print("="*60)
        stats = store.get_statistics()
        print(f"\n📊 Total vectors: {stats['total_vectors']}")
        print(f"📁 Metadata count: {stats['metadata_count']}")
        print(f"📐 Dimension: {stats['index_dimension']}")
        print("\n💡 Restart the server to use the updated vector store")
        return True
    else:
        print("\n❌ Failed to build combined vector store")
        return False


def main():
    print("\n🚀 CREATING COMBINED VECTOR STORE")
    print("="*60)
    print("📁 Processing data from:")
    print(f"  • {EXTRACTED_DATA_DIR}")
    print(f"  • {Path(BASE_PATH) / 'data_23_10_25'}")
    
    # Build combined vector store directly
    if not rebuild_vector_store():
        print("\n❌ Failed to create combined vector store")
        return
    
    print("\n✅ ALL DONE! Restart the server.")


if __name__ == "__main__":
    main()
