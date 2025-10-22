"""
Semantic Quality Test - Verify embedding model is working correctly
Tests if the embedding model can distinguish between different topics.
"""

import os
import sys
from pathlib import Path

# Suppress TensorFlow warnings
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sentence_transformers import SentenceTransformer, util


def test_semantic_quality(model_name: str = "sentence-transformers/all-mpnet-base-v2"):
    """
    Test if the embedding model can correctly match queries to relevant documents.
    
    Args:
        model_name: Model to test
    """
    print("="*70)
    print("SEMANTIC QUALITY TEST")
    print("="*70)
    print(f"\n🔬 Testing model: {model_name}")
    print("\n[INFO] Loading model...")
    
    model = SentenceTransformer(model_name)
    
    print("[SUCCESS] Model loaded!\n")
    
    # Define test queries and expected matching documents
    test_cases = [
        {
            "query": "What are the placement statistics and average package?",
            "relevant": "The Computer Science Department had 95% placements in 2024 with an average package of 6.5 LPA. Top recruiters include TCS, Infosys, and Amazon.",
            "irrelevant": "The college library is open from 8 AM to 10 PM and has 50,000 books."
        },
        {
            "query": "How to apply for admission?",
            "relevant": "Admission is through the online portal at admission.college.edu. Students must submit their application form along with required documents.",
            "irrelevant": "The placement cell organizes campus drives throughout the year with various companies."
        },
        {
            "query": "Tell me about computer science courses",
            "relevant": "The CSE department offers specializations in Artificial Intelligence, Data Science, Machine Learning, and Cyber Security.",
            "irrelevant": "The college campus has a cafeteria, gym, and sports facilities for students."
        },
        {
            "query": "What facilities are available in hostel?",
            "relevant": "Hostel facilities include WiFi, 24/7 security, mess services, common room, and study areas for students.",
            "irrelevant": "The admission process requires 12th grade marks and entrance exam scores for eligibility."
        },
        {
            "query": "Tell me about cultural events and fests",
            "relevant": "The college organizes annual technical and cultural fests like TechnoVision and CulturalMania with various competitions and workshops.",
            "irrelevant": "The placement statistics show 90% of students get placed with packages ranging from 4 to 12 LPA."
        }
    ]
    
    print("="*70)
    print("RUNNING SEMANTIC TESTS")
    print("="*70)
    
    passed = 0
    total = len(test_cases)
    
    for i, test in enumerate(test_cases, 1):
        query = test["query"]
        relevant_doc = test["relevant"]
        irrelevant_doc = test["irrelevant"]
        
        print(f"\n{'─'*70}")
        print(f"Test {i}/{total}: {query}")
        print(f"{'─'*70}")
        
        # Encode
        query_emb = model.encode([query], convert_to_tensor=True)
        relevant_emb = model.encode([relevant_doc], convert_to_tensor=True)
        irrelevant_emb = model.encode([irrelevant_doc], convert_to_tensor=True)
        
        # Calculate similarities
        relevant_score = util.pytorch_cos_sim(query_emb, relevant_emb).item()
        irrelevant_score = util.pytorch_cos_sim(query_emb, irrelevant_emb).item()
        
        # Check if relevant doc scores higher than irrelevant
        success = relevant_score > irrelevant_score
        
        if success:
            passed += 1
            status = "✅ PASS"
        else:
            status = "❌ FAIL"
        
        print(f"\n{status}")
        print(f"  🟢 Relevant Score:   {relevant_score:.4f}")
        print(f"  🔴 Irrelevant Score: {irrelevant_score:.4f}")
        print(f"  📊 Difference:       {relevant_score - irrelevant_score:.4f}")
        
        if success:
            quality = "Excellent" if relevant_score - irrelevant_score > 0.2 else "Good"
            print(f"  ⭐ Quality: {quality}")
        else:
            print(f"  ⚠️  Model failed to distinguish semantic relevance!")
        
        # Show preview
        print(f"\n  💬 Relevant: {relevant_doc[:80]}...")
        print(f"  🚫 Irrelevant: {irrelevant_doc[:80]}...")
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"\n✅ Passed: {passed}/{total} ({100*passed/total:.0f}%)")
    print(f"❌ Failed: {total-passed}/{total}")
    
    if passed == total:
        print("\n🎉 EXCELLENT! Model is semantically accurate.")
        print("   Your vector store will retrieve relevant results.")
    elif passed >= total * 0.8:
        print("\n✅ GOOD! Model performs well but has room for improvement.")
    else:
        print("\n⚠️  WARNING! Model may not retrieve semantically relevant results.")
        print("   Consider using a different embedding model.")
    
    print("="*70)
    
    return passed == total


if __name__ == "__main__":
    print("\n🧪 Testing default model (MPNet)...")
    test_semantic_quality("sentence-transformers/all-mpnet-base-v2")
    
    # Optionally test the old model for comparison
    print("\n" + "="*70)
    print("COMPARISON TEST - Old Model (MiniLM)")
    print("="*70)
    test_semantic_quality("all-MiniLM-L6-v2")
