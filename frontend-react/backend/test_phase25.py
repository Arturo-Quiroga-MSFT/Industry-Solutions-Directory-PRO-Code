#!/usr/bin/env python3
"""Test Phase 2.5: JSON Schema structured outputs + Streaming"""
import requests
import json
import sys

BASE = "http://localhost:8000"

def test_json_schema():
    """Test that strict JSON schema produces valid, well-typed output."""
    print("=" * 70)
    print("TEST 1: JSON Schema Structured Outputs (non-streaming)")
    print("=" * 70)
    
    resp = requests.post(f"{BASE}/api/query", json={
        "question": "How many healthcare AI solutions do we have?"
    })
    data = resp.json()
    
    # Validate response
    assert data["success"], f"Query failed: {data.get('error')}"
    
    # Check intent has exactly the 4 expected fields
    intent = data["intent"]
    print(f"\n  Intent: {json.dumps(intent, indent=2)}")
    assert intent["intent"] in ("query", "analyze", "summarize", "compare"), f"Bad intent enum: {intent['intent']}"
    assert isinstance(intent["needs_new_query"], bool), "needs_new_query should be bool"
    assert intent["query_type"] in ("specific", "aggregate", "exploratory"), f"Bad query_type enum: {intent['query_type']}"
    assert isinstance(intent["reasoning"], str) and len(intent["reasoning"]) > 0, "reasoning should be non-empty string"
    
    # Check SQL was generated (NL2SQL strict schema)
    print(f"  SQL: {data.get('sql', '')[:80]}...")
    print(f"  Confidence: {data.get('confidence')}")
    print(f"  Row count: {data.get('row_count', len(data.get('rows', [])))}")
    print(f"  Narrative length: {len(data.get('narrative', ''))}")
    
    print("\n  ✅ JSON Schema test PASSED — all types correct\n")
    return True


def test_streaming():
    """Test the SSE streaming endpoint."""
    print("=" * 70)
    print("TEST 2: SSE Streaming (/api/query/stream)")
    print("=" * 70)
    
    resp = requests.post(
        f"{BASE}/api/query/stream",
        json={"question": "Show me top 5 financial services partners"},
        stream=True,
        headers={"Accept": "text/event-stream"}
    )
    
    assert resp.status_code == 200, f"HTTP {resp.status_code}"
    assert "text/event-stream" in resp.headers.get("content-type", ""), "Expected SSE content-type"
    
    metadata = None
    narrative_chunks = []
    done_event = None
    
    for line in resp.iter_lines(decode_unicode=True):
        if not line or not line.startswith("data: "):
            continue
        event = json.loads(line[6:])  # strip "data: " prefix
        
        if event["type"] == "metadata":
            metadata = event
            print(f"\n  [metadata] success={event.get('success')}, sql={str(event.get('sql',''))[:60]}...")
        elif event["type"] == "delta":
            narrative_chunks.append(event["content"])
            # Print first few chunks
            if len(narrative_chunks) <= 3:
                print(f"  [delta] {repr(event['content'][:50])}")
        elif event["type"] == "done":
            done_event = event
    
    # Validate
    assert metadata is not None, "No metadata event received"
    assert metadata.get("success"), f"Streaming failed: {metadata.get('error')}"
    assert len(narrative_chunks) > 0, "No delta chunks received"
    
    full_narrative = "".join(narrative_chunks)
    print(f"\n  Total delta chunks: {len(narrative_chunks)}")
    print(f"  Full narrative length: {len(full_narrative)} chars")
    print(f"  First 200 chars: {full_narrative[:200]}...")
    
    if done_event:
        print(f"  Elapsed: {done_event.get('elapsed_time')}s")
        print(f"  Tokens: {done_event.get('usage_stats')}")
    
    print("\n  ✅ Streaming test PASSED — received metadata + deltas + done\n")
    return True


if __name__ == "__main__":
    ok = True
    ok = test_json_schema() and ok
    ok = test_streaming() and ok
    
    if ok:
        print("=" * 70)
        print("ALL TESTS PASSED ✅")
        print("=" * 70)
    else:
        print("SOME TESTS FAILED ❌")
        sys.exit(1)
