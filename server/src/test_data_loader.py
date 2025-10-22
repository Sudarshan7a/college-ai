"""
Test script for data_loader.py
Tests loading categorized text files from data/extracted/
"""

from pathlib import Path
from pprint import pprint
import sys

# Add parent directory to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.data_loader import load_all_documents, load_documents_by_category, get_category_statistics
from src.config import CATEGORIES


def test_category_statistics():
    """
    Test getting statistics for each category.
    """
    print("\n" + "="*60)
    print("TEST 1: Category Statistics (from data/extracted/)")
    print("="*60)
    
    stats = get_category_statistics()
    
    print("\n📊 Files per category:")
    total_files = 0
    for category, count in stats.items():
        print(f"  {category:20s}: {count:4d} files")
        total_files += count
    
    print(f"\n  {'TOTAL':20s}: {total_files:4d} files")
    
    if total_files == 0:
        print("\n⚠️  No files found. Run the pipeline first: python -m src.main")
    
    return True


def test_load_all_documents():
    """
    Test loading all documents from all categories.
    """
    print("\n" + "="*60)
    print("TEST 2: Load All Documents")
    print("="*60)
    
    print("\n📂 Loading sample.txt from data/ directory...")
    documents = load_all_documents("data")
    
    if not documents:
        print("❌ No documents loaded!")
        return False
    
    print(f"\n✅ Loaded {len(documents)} documents")
    
    # Show first document details
    print("\n📄 First Document Details:")
    first_doc = documents[0]
    print(f"  Type: {type(first_doc)}")
    print(f"  Category: {first_doc.metadata.get('category', 'N/A')}")
    print(f"  Filename: {first_doc.metadata.get('filename', 'N/A')}")
    print(f"  Source Path: {first_doc.metadata.get('source_path', 'N/A')}")
    print(f"  Description: {first_doc.metadata.get('category_description', 'N/A')}")
    print(f"  Content Length: {len(first_doc.page_content)} characters")
    
    print(f"\n📝 Content Preview (first 300 chars):")
    print(f"  {first_doc.page_content[:300]}...")
    
    print("\n🔍 Full Metadata:")
    pprint(first_doc.metadata, indent=2)
    
    return True


def test_load_by_category():
    """
    Test loading documents from specific categories.
    """
    print("\n" + "="*60)
    print("TEST 3: Load by Category (from data/extracted/)")
    print("="*60)
    
    # Test with a few categories
    test_categories = ['departments', 'college_info', 'placements']
    
    for category in test_categories:
        if category not in CATEGORIES:
            continue
        
        print(f"\n📂 Loading '{category}' category...")
        docs = load_documents_by_category(category)
        
        if docs:
            print(f"  ✅ Loaded {len(docs)} documents")
            print(f"  📄 First file: {docs[0].metadata.get('filename', 'N/A')}")
            print(f"  📏 Content length: {len(docs[0].page_content)} characters")
        else:
            print(f"  ⚠️  No documents found in '{category}'")


def test_metadata_completeness():
    """
    Verify that all required metadata fields are present.
    """
    print("\n" + "="*60)
    print("TEST 4: Metadata Completeness")
    print("="*60)
    
    documents = load_all_documents("data")
    
    if not documents:
        print("❌ No documents to test")
        return False
    
    required_fields = ['category', 'filename', 'source_path', 'category_description']
    
    print(f"\n🔍 Checking {len(documents)} documents for required metadata fields...")
    print(f"   Required fields: {required_fields}")
    
    all_complete = True
    incomplete_count = 0
    
    for i, doc in enumerate(documents):
        missing_fields = [field for field in required_fields if field not in doc.metadata]
        
        if missing_fields:
            all_complete = False
            incomplete_count += 1
            if incomplete_count <= 3:  # Show first 3 issues
                print(f"\n  ⚠️  Document {i+1} missing fields: {missing_fields}")
                print(f"     Source: {doc.metadata.get('source_path', 'unknown')}")
    
    if all_complete:
        print(f"\n  ✅ All {len(documents)} documents have complete metadata!")
    else:
        print(f"\n  ⚠️  {incomplete_count} documents have incomplete metadata")
    
    return all_complete


def test_content_sample():
    """
    Show sample content from different categories.
    """
    print("\n" + "="*60)
    print("TEST 5: Content Samples")
    print("="*60)
    
    documents = load_all_documents("data")
    
    if not documents:
        print("❌ No documents to sample")
        return
    
    # Group by category
    by_category = {}
    for doc in documents:
        category = doc.metadata.get('category', 'unknown')
        if category not in by_category:
            by_category[category] = []
        by_category[category].append(doc)
    
    # Show one sample from each category
    for category, docs in sorted(by_category.items()):
        print(f"\n📁 Category: {category}")
        print(f"   Files: {len(docs)}")
        if docs:
            sample = docs[0]
            print(f"   Sample: {sample.metadata.get('filename', 'N/A')}")
            print(f"   Preview: {sample.page_content[:150]}...")


def run_all_tests():
    """
    Run all test functions.
    """
    print("\n" + "="*60)
    print("COLLEGE AI - DATA LOADER TEST SUITE")
    print("="*60)
    
    tests = [
        ("Category Statistics", test_category_statistics),
        ("Load All Documents", test_load_all_documents),
        ("Load By Category", test_load_by_category),
        ("Metadata Completeness", test_metadata_completeness),
        ("Content Samples", test_content_sample),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result if result is not None else True))
        except Exception as e:
            print(f"\n❌ Test '{test_name}' failed with error: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    passed_count = sum(1 for _, p in results if p)
    total_count = len(results)
    
    print(f"\nPassed: {passed_count}/{total_count}")
    
    if passed_count == total_count:
        print("\n🎉 All tests passed!")
    else:
        print("\n⚠️  Some tests failed. Check the output above.")


if __name__ == "__main__":
    run_all_tests()
