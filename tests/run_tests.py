import sys
import os
import json
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hackgpt.rag import RAGEngine
from hackgpt.llm import run_llm
from hackgpt.prompt import build_prompt

def run_tests(test_file="tests/test_queries.json"):
    """Run regression tests"""
    print("="*50)
    print("Running Regression Tests")
    print("="*50 + "\n")
    
    # Load tests
    with open(test_file, "r") as f:
        tests = json.load(f)
    
    # Initialize RAG
    rag = RAGEngine()
    
    results = []
    
    for test in tests:
        print(f"\n[TEST] {test['id']}")
        print(f"Query: {test['query'][:100]}...")
        
        start_time = time.time()
        
        # Retrieve context
        chunks = rag.retrieve(test['query'], k=3)
        avg_confidence = sum(c.get('similarity_score', 0) for c in chunks) / len(chunks) if chunks else 0
        confidence_level = "HIGH" if avg_confidence > 0.7 else "MEDIUM" if avg_confidence > 0.5 else "LOW"
        
        # Format context
        context_text = ""
        for i, c in enumerate(chunks):
            source = c.get("file") or c.get("url") or c.get("path") or "unknown"
            context_text += f"-- Source {i+1} ({source}):\n{c['text']}\n\n"
        
        # Generate response
        prompt = build_prompt(context_text, test['query'], confidence_level)
        response = run_llm(prompt, stream=False)
        
        response_time = time.time() - start_time
        
        # Check keywords
        keywords_found = [kw for kw in test['expected_keywords'] if kw.lower() in response.lower()]
        keyword_coverage = len(keywords_found) / len(test['expected_keywords']) * 100
        
        # Check confidence threshold
        confidence_met = (
            (test['confidence_threshold'] == "HIGH" and confidence_level in ["HIGH", "MEDIUM"]) or
            (test['confidence_threshold'] == "MEDIUM" and confidence_level in ["HIGH", "MEDIUM", "LOW"]) or
            (test['confidence_threshold'] == "LOW")
        )
        
        result = {
            "test_id": test['id'],
            "confidence": confidence_level,
            "confidence_met": confidence_met,
            "keyword_coverage": keyword_coverage,
            "response_time": response_time,
            "passed": confidence_met and keyword_coverage >= 60
        }
        
        results.append(result)
        
        print(f"  Confidence: {confidence_level} (expected: {test['confidence_threshold']})")
        print(f"  Keyword Coverage: {keyword_coverage:.1f}% ({len(keywords_found)}/{len(test['expected_keywords'])})")
        print(f"  Response Time: {response_time:.2f}s")
        print(f"  Status: {'✅ PASS' if result['passed'] else '❌ FAIL'}")
    
    # Summary
    print("\n" + "="*50)
    print("Test Summary")
    print("="*50)
    passed = sum(1 for r in results if r['passed'])
    total = len(results)
    print(f"Passed: {passed}/{total} ({passed/total*100:.1f}%)")
    print(f"Avg Response Time: {sum(r['response_time'] for r in results)/total:.2f}s")
    
    # Save results
    os.makedirs("tests/results", exist_ok=True)
    with open("tests/results/latest.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\nResults saved to: tests/results/latest.json")

if __name__ == "__main__":
    run_tests()
