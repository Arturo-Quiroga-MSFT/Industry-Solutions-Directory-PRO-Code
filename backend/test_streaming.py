"""
Test script for streaming chat endpoint
"""
import requests
import json


def test_streaming():
    """Test the streaming chat endpoint"""
    url = "http://localhost:8000/api/chat/stream"
    
    payload = {
        "message": "What healthcare AI solutions are available?",
        "session_id": "test-streaming-001"
    }
    
    print("🚀 Testing streaming endpoint...")
    print(f"URL: {url}")
    print(f"Message: {payload['message']}\n")
    
    try:
        response = requests.post(
            url,
            json=payload,
            headers={"Content-Type": "application/json"},
            stream=True,
            timeout=60
        )
        
        if response.status_code != 200:
            print(f"❌ Error: Status code {response.status_code}")
            print(response.text)
            return
        
        print("✅ Connected! Streaming response:\n")
        print("=" * 80)
        
        full_content = ""
        citations = []
        follow_up = []
        session_id = None
        
        for line in response.iter_lines():
            if line:
                line = line.decode('utf-8')
                if line.startswith('data: '):
                    try:
                        data = json.loads(line[6:])  # Remove 'data: ' prefix
                        event_type = data.get('type')
                        
                        if event_type == 'session':
                            session_id = data.get('session_id')
                            print(f"📋 Session ID: {session_id}\n")
                        
                        elif event_type == 'citations':
                            citations = data.get('citations', [])
                            print(f"📚 Found {len(citations)} citations\n")
                        
                        elif event_type == 'content':
                            content = data.get('content', '')
                            full_content += content
                            print(content, end='', flush=True)
                        
                        elif event_type == 'follow_up':
                            follow_up = data.get('questions', [])
                        
                        elif event_type == 'done':
                            print("\n\n✅ Stream complete!")
                            break
                        
                        elif event_type == 'error':
                            print(f"\n\n❌ Error: {data.get('error')}")
                            break
                    
                    except json.JSONDecodeError as e:
                        print(f"\n⚠️  Failed to parse JSON: {e}")
                        continue
        
        print("=" * 80)
        print(f"\n📊 Summary:")
        print(f"  • Session ID: {session_id}")
        print(f"  • Response length: {len(full_content)} characters")
        print(f"  • Citations: {len(citations)}")
        print(f"  • Follow-up questions: {len(follow_up)}")
        
        if citations:
            print(f"\n📚 Citations:")
            for i, citation in enumerate(citations, 1):
                print(f"  {i}. {citation.get('solution_name')} by {citation.get('partner_name')}")
                print(f"     Relevance: {citation.get('relevance_score', 0):.4f}")
        
        if follow_up:
            print(f"\n💬 Follow-up questions:")
            for i, question in enumerate(follow_up, 1):
                print(f"  {i}. {question}")
        
        print("\n🎉 Test completed successfully!")
        
    except requests.exceptions.Timeout:
        print("❌ Request timed out")
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")


if __name__ == "__main__":
    test_streaming()
