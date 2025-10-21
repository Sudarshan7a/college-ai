"""
Test script for College AI Backend API
Tests all endpoints with sample requests
"""
import requests
import json
import time
from typing import Dict, Any

# Base URL
BASE_URL = "http://localhost:8000"

# ANSI color codes
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'


def print_header(text: str):
    """Print a formatted header"""
    print(f"\n{'='*60}")
    print(f"{BLUE}{text}{RESET}")
    print('='*60)


def print_success(text: str):
    """Print success message"""
    print(f"{GREEN}✅ {text}{RESET}")


def print_error(text: str):
    """Print error message"""
    print(f"{RED}❌ {text}{RESET}")


def print_info(text: str):
    """Print info message"""
    print(f"{YELLOW}ℹ️  {text}{RESET}")


def test_root():
    """Test root endpoint"""
    print_header("TEST 1: Root Endpoint")
    
    try:
        response = requests.get(f"{BASE_URL}/")
        response.raise_for_status()
        
        data = response.json()
        print_success("Root endpoint working")
        print(json.dumps(data, indent=2))
        return True
    except Exception as e:
        print_error(f"Root endpoint failed: {e}")
        return False


def test_health():
    """Test health check endpoint"""
    print_header("TEST 2: Health Check")
    
    try:
        response = requests.get(f"{BASE_URL}/api/health")
        response.raise_for_status()
        
        data = response.json()
        print_success("Health check successful")
        print(f"  Status: {data.get('status')}")
        print(f"  Models Loaded: {data.get('models_loaded')}")
        print(f"  Uptime: {data.get('uptime_seconds'):.2f}s")
        print(f"  Vector Store: {data.get('vector_store_ready')}")
        print(f"  LLM Ready: {data.get('llm_ready')}")
        print(f"  Total Vectors: {data.get('total_vectors')}")
        
        if data.get('status') == 'healthy':
            print_success("Server is healthy!")
            return True
        else:
            print_error("Server is unhealthy")
            return False
    except Exception as e:
        print_error(f"Health check failed: {e}")
        return False


def test_search(query: str, top_k: int = 3):
    """Test search endpoint"""
    print_header(f"TEST 3: Search - '{query}'")
    
    try:
        payload = {
            "query": query,
            "top_k": top_k
        }
        
        start_time = time.time()
        response = requests.post(
            f"{BASE_URL}/api/search",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        client_time = time.time() - start_time
        
        response.raise_for_status()
        data = response.json()
        
        print_success(f"Search completed in {client_time:.3f}s (client) / {data.get('processing_time', 0):.3f}s (server)")
        print(f"\n🔍 Query: {data.get('query')}")
        print(f"📊 Found {len(data.get('results', []))} results:\n")
        
        for i, result in enumerate(data.get('results', [])[:3], 1):
            print(f"{i}. [{result.get('category')}] {result.get('filename')}")
            print(f"   Distance: {result.get('distance'):.3f}")
            if result.get('rerank_score'):
                print(f"   Rerank Score: {result.get('rerank_score'):.3f}")
            print(f"   Text: {result.get('text', '')[:150]}...")
            print()
        
        return True
    except Exception as e:
        print_error(f"Search failed: {e}")
        if hasattr(e, 'response'):
            print(f"   Response: {e.response.text}")
        return False


def test_query(query: str, top_k: int = 3):
    """Test query endpoint (full RAG)"""
    print_header(f"TEST 4: RAG Query - '{query}'")
    
    try:
        payload = {
            "query": query,
            "top_k": top_k,
            "include_sources": True
        }
        
        start_time = time.time()
        response = requests.post(
            f"{BASE_URL}/api/query",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        client_time = time.time() - start_time
        
        response.raise_for_status()
        data = response.json()
        
        print_success(f"Query completed in {client_time:.3f}s (client) / {data.get('processing_time', 0):.3f}s (server)")
        print(f"\n🔍 Query: {data.get('query')}")
        print(f"🤖 Model: {data.get('model_used')}")
        print(f"\n💬 Answer:")
        print(f"{data.get('answer')}\n")
        
        print(f"📚 Sources ({len(data.get('sources', []))}):")
        for i, source in enumerate(data.get('sources', []), 1):
            print(f"  {i}. [{source.get('category')}] {source.get('filename')}")
            print(f"     Distance: {source.get('distance'):.3f}")
            if source.get('rerank_score'):
                print(f"     Rerank Score: {source.get('rerank_score'):.3f}")
        
        return True
    except Exception as e:
        print_error(f"Query failed: {e}")
        if hasattr(e, 'response'):
            print(f"   Response: {e.response.text}")
        return False


def test_stats():
    """Test stats endpoint"""
    print_header("TEST 5: Server Statistics")
    
    try:
        response = requests.get(f"{BASE_URL}/api/stats")
        response.raise_for_status()
        
        data = response.json()
        print_success("Stats retrieved")
        print(f"  Total Queries: {data.get('total_queries')}")
        print(f"  Avg Response Time: {data.get('avg_response_time'):.3f}s")
        print(f"  Uptime: {data.get('uptime_seconds'):.2f}s")
        
        vs_info = data.get('vector_store_info', {})
        if vs_info:
            print(f"\n  Vector Store:")
            print(f"    Vectors: {vs_info.get('total_vectors')}")
            print(f"    Dimension: {vs_info.get('dimension')}")
            print(f"    Model: {vs_info.get('model')}")
            print(f"    Reranker: {vs_info.get('reranker_enabled')}")
        
        return True
    except Exception as e:
        print_error(f"Stats failed: {e}")
        return False


def run_all_tests():
    """Run all API tests"""
    print("\n" + "="*60)
    print(f"{BLUE}🧪 COLLEGE AI API TEST SUITE{RESET}")
    print("="*60)
    print(f"{YELLOW}Testing API at: {BASE_URL}{RESET}")
    
    # Check if server is running
    try:
        requests.get(BASE_URL, timeout=2)
    except Exception:
        print_error("Server is not running!")
        print_info("Start the server with: python server.py")
        print_info("Or: uvicorn server:app --reload")
        return
    
    results = []
    
    # Run tests
    results.append(("Root", test_root()))
    time.sleep(0.5)
    
    results.append(("Health", test_health()))
    time.sleep(0.5)
    
    results.append(("Search", test_search("What are the placement statistics?")))
    time.sleep(0.5)
    
    results.append(("RAG Query 1", test_query("What are the placement statistics?")))
    time.sleep(0.5)
    
    results.append(("RAG Query 2", test_query("Tell me about CSE department")))
    time.sleep(0.5)
    
    results.append(("Stats", test_stats()))
    
    # Summary
    print_header("TEST SUMMARY")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = f"{GREEN}✅ PASS{RESET}" if result else f"{RED}❌ FAIL{RESET}"
        print(f"  {name}: {status}")
    
    print(f"\n{'='*60}")
    if passed == total:
        print_success(f"ALL TESTS PASSED ({passed}/{total})")
    else:
        print_error(f"SOME TESTS FAILED ({passed}/{total} passed)")
    print('='*60 + '\n')


if __name__ == "__main__":
    run_all_tests()
