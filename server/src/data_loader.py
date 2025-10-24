from pathlib import Path
from typing import List, Dict, Any
from langchain_community.document_loaders import TextLoader
from langchain_core.documents import Document
import sys
import os
import pandas as pd

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
    
    # Also load CSV files from each category folder (convert to text)
    for category in CATEGORIES.keys():
        category_path = data_path / category
        
        if not category_path.exists():
            continue
        
        # Find all .csv files in this category
        csv_files = list(category_path.glob('*.csv'))
        if csv_files:
            print(f"[INFO] Found {len(csv_files)} CSV files in '{category}' category")
            
            for csv_file in csv_files:
                try:
                    # Load CSV and convert to text
                    csv_doc = load_csv_as_document(csv_file, category)
                    if csv_doc:
                        documents.append(csv_doc)
                        print(f"[DEBUG] Loaded CSV: {csv_file.name} ({len(csv_doc.page_content)} chars)")
                    
                except Exception as e:
                    print(f"[ERROR] Failed to load CSV {csv_file}: {e}")
    
    print(f"\n[SUCCESS] Total documents loaded: {len(documents)}")
    return documents


def load_csv_as_document(csv_file: Path, category: str) -> Document:
    """
    Load a CSV file and convert it to a text document for embedding.
    
    Args:
        csv_file: Path to the CSV file
        category: Category name for metadata
    
    Returns:
        LangChain Document object with CSV data as text
    """
    try:
        # Read CSV file
        df = pd.read_csv(csv_file)
        
        # Create readable text from CSV
        text_content = f"File: {csv_file.name}\n"
        text_content += f"Category: {category}\n"
        text_content += f"Total Records: {len(df)}\n\n"
        
        # Add column information
        text_content += f"Columns: {', '.join(df.columns.tolist())}\n\n"
        
        # Convert data to readable format
        if 'Student Name' in df.columns and 'Department' in df.columns:
            # This is placement data - create department-wise summaries
            text_content += "PLACEMENT DATA SUMMARY:\n\n"
            
            # Department-wise breakdown
            dept_counts = df['Department'].value_counts()
            text_content += "Students placed by Department:\n"
            for dept, count in dept_counts.items():
                text_content += f"- {dept}: {count} students\n"
            
            text_content += "\n"
            
            # Company information if available
            if 'Company Logo URL' in df.columns:
                # Extract company names from logo URLs
                companies = df['Company Logo URL'].apply(lambda x: extract_company_from_url(x) if pd.notna(x) else 'Unknown').value_counts()
                text_content += "Companies that recruited:\n"
                for company, count in companies.items():
                    text_content += f"- {company}: {count} students\n"
            
            text_content += "\n"
            
            # Add individual records (first 20 for context)
            text_content += "Sample Placement Records:\n"
            for idx, row in df.head(20).iterrows():
                student = row.get('Student Name', 'Unknown')
                dept = row.get('Department', 'Unknown')
                company = extract_company_from_url(row.get('Company Logo URL', '')) if pd.notna(row.get('Company Logo URL')) else 'Unknown'
                text_content += f"- {student} ({dept}) placed at {company}\n"
            
            if len(df) > 20:
                text_content += f"... and {len(df) - 20} more students\n"
        
        else:
            # Generic CSV handling
            text_content += "CSV Data:\n\n"
            
            # Add first 10 rows as sample
            for idx, row in df.head(10).iterrows():
                row_text = " | ".join([f"{col}: {val}" for col, val in row.items() if pd.notna(val)])
                text_content += f"Row {idx + 1}: {row_text}\n"
            
            if len(df) > 10:
                text_content += f"... and {len(df) - 10} more rows\n"
        
        # Create Document object
        doc = Document(
            page_content=text_content,
            metadata={
                'category': category,
                'filename': csv_file.name,
                'source_path': str(csv_file),
                'category_description': CATEGORIES.get(category, {}).get('description', 'Unknown category'),
                'file_type': 'csv',
                'total_records': len(df),
                'columns': df.columns.tolist()
            }
        )
        
        return doc
        
    except Exception as e:
        print(f"[ERROR] Failed to process CSV {csv_file}: {e}")
        return None


def extract_company_from_url(url: str) -> str:
    """
    Extract company name from logo URL.
    
    Args:
        url: Company logo URL
    
    Returns:
        Company name or 'Unknown'
    """
    if not url or pd.isna(url):
        return 'Unknown'
    
    # Extract filename from URL
    filename = url.split('/')[-1].lower()
    
    # Map common company logo filenames to names
    company_mapping = {
        'tcs.jpg': 'TCS',
        'infosys.jpg': 'Infosys',
        'wipro.jpg': 'Wipro',
        'accenture.jpg': 'Accenture',
        'logo-30.jpg': 'Corporate Company',  # Generic company logo
        'cognizant.jpg': 'Cognizant',
        'microsoft.jpg': 'Microsoft',
        'google.jpg': 'Google',
        'amazon.jpg': 'Amazon'
    }
    
    return company_mapping.get(filename, filename.replace('.jpg', '').replace('.png', '').title())


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


def get_category_statistics(data_dir: str = None) -> Dict[str, Dict[str, int]]:
    """
    Get count of text and CSV files in each category.
    
    Args:
        data_dir: Optional custom data directory
    
    Returns:
        Dictionary with category names and file counts (txt and csv)
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
            csv_files = list(category_path.glob('*.csv'))
            stats[category] = {
                'txt': len(txt_files),
                'csv': len(csv_files),
                'total': len(txt_files) + len(csv_files)
            }
        else:
            stats[category] = {'txt': 0, 'csv': 0, 'total': 0}
    
    return stats


# Example usage
if __name__ == "__main__":
    print("="*60)
    print("COLLEGE AI - DATA LOADER")
    print("="*60)
    
    # Show statistics
    print("\n📊 Category Statistics:")
    stats = get_category_statistics()
    for category, counts in stats.items():
        txt_count = counts['txt']
        csv_count = counts['csv']
        total_count = counts['total']
        print(f"  {category:20s}: {total_count:4d} files ({txt_count} txt, {csv_count} csv)")
    
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