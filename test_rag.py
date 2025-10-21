"""
Test RAG System with College Data
"""

from src.rag_system import CollegeRAG

def main():
    print("="*70)
    print("COLLEGE AI - RAG SYSTEM TEST")
    print("="*70)
    
    # Initialize RAG system (auto-loads vector store with re-ranker)
    print("\n[STEP 1] Initializing RAG system...")
    rag = CollegeRAG(
        llm_provider="groq",
        llm_model="llama-3.3-70b-versatile",  # Updated to active model
        use_reranker=True,  # Enable CrossEncoder re-ranking
        auto_build=True     # Auto-build vector store if missing
    )
    
    print("\n✅ RAG system ready!\n")
    
    # Test queries about your college
    test_queries = [
        "What are the placement statistics?",
        "Tell me about the computer science department",
        "What facilities are available on campus?",
        "How do I apply for admission?"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print("\n" + "="*70)
        print(f"TEST {i}/{len(test_queries)}")
        print("="*70)
        
        # Get answer with sources
        result = rag.ask(query, top_k=3, include_sources=True)
        
        print(f"\n❓ Question: {query}")
        print(f"\n💡 Answer:\n{result['answer']}")
        
        # Show sources
        print(f"\n📚 Based on {len(result['sources'])} documents:")
        for src in result['sources']:
            rerank = f"Rerank: {src['rerank_score']:.3f}" if src['rerank_score'] else "No rerank"
            print(f"  • {src['category']}/{src['filename']}")
            print(f"    FAISS Distance: {src['distance']:.3f} | {rerank}")
    
    print("\n" + "="*70)
    print("✅ ALL TESTS COMPLETE!")
    print("="*70)
    
    # Interactive mode
    print("\n" + "="*70)
    print("INTERACTIVE MODE - Ask your own questions!")
    print("Type 'exit' to quit")
    print("="*70)
    
    while True:
        print()
        user_query = input("Your Question: ").strip()
        
        if user_query.lower() in ['exit', 'quit', 'bye', '']:
            print("\n👋 Goodbye!")
            break
        
        try:
            answer = rag.chat(user_query, top_k=3)
            print(f"\n🤖 Answer:\n{answer}\n")
        except Exception as e:
            print(f"\n❌ Error: {e}\n")


if __name__ == "__main__":
    main()
