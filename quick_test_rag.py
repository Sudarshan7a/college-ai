"""
Quick RAG Test - Single Query
"""

from src.rag_system import CollegeRAG

print("Initializing RAG system...")
rag = CollegeRAG(
    llm_provider="groq",
    llm_model="llama-3.3-70b-versatile",
    use_reranker=True
)

print("\n" + "="*60)
query = "What are the placement statistics?"
print(f"Question: {query}")
print("="*60)

answer = rag.chat(query, top_k=3)
print(f"\nAnswer:\n{answer}")
