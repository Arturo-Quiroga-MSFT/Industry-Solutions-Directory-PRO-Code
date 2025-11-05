"""
Interactive Chat Client for Industry Solutions Directory
Provides a command-line interface to query the backend API
"""

import requests
import json
import uuid
from datetime import datetime
from typing import Optional


class InteractiveChatClient:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session_id = f"interactive-{uuid.uuid4().hex[:8]}"
        self.chat_endpoint = f"{base_url}/api/chat"
        
    def check_health(self) -> bool:
        """Check if the backend API is available"""
        try:
            response = requests.get(f"{self.base_url}/api/health", timeout=5)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False
    
    def send_message(self, message: str) -> Optional[dict]:
        """Send a message to the chat API"""
        try:
            payload = {
                "message": message,
                "session_id": self.session_id
            }
            
            response = requests.post(
                self.chat_endpoint,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ Error: API returned status code {response.status_code}")
                return None
                
        except requests.exceptions.Timeout:
            print("❌ Error: Request timed out. The backend may be processing a complex query.")
            return None
        except requests.exceptions.RequestException as e:
            print(f"❌ Error: Failed to connect to API: {str(e)}")
            return None
    
    def display_response(self, data: dict):
        """Display the response in a clean, formatted way"""
        print("\n" + "="*80)
        print("RESPONSE:")
        print("="*80)
        print(data.get("response", "No response received"))
        
        citations = data.get("citations", [])
        if citations:
            print("\n" + "="*80)
            print(f"CITATIONS ({len(citations)} solutions found):")
            print("="*80)
            
            for i, citation in enumerate(citations, 1):
                print(f"\n{i}. {citation.get('solution_name', 'Unknown Solution')}")
                print(f"   Partner: {citation.get('partner_name', 'Unknown Partner')}")
                print(f"   Relevance Score: {citation.get('relevance_score', 0):.4f}")
                
                # Display truncated description
                description = citation.get('description', 'No description available')
                # Remove HTML tags for cleaner display
                import re
                clean_description = re.sub('<[^<]+?>', '', description)
                clean_description = clean_description.replace('&#160;', ' ').strip()
                
                # Truncate if too long
                if len(clean_description) > 200:
                    clean_description = clean_description[:200] + "..."
                
                print(f"   Description: {clean_description}")
                print(f"   URL: {citation.get('url', 'No URL available')}")
        
        print("\n" + "="*80 + "\n")
    
    def run(self):
        """Run the interactive chat session"""
        print("="*80)
        print("INDUSTRY SOLUTIONS DIRECTORY - INTERACTIVE CHAT")
        print("="*80)
        print(f"Session ID: {self.session_id}")
        print(f"Backend URL: {self.base_url}")
        print()
        
        # Check if backend is available
        print("Checking backend availability...")
        if not self.check_health():
            print("❌ Error: Backend API is not available.")
            print("   Please ensure the backend is running with:")
            print("   cd backend && python -m uvicorn app.main:app --reload")
            return
        
        print("✅ Backend is online and ready!")
        print()
        print("="*80)
        print("INSTRUCTIONS:")
        print("- Type your question and press Enter")
        print("- Type 'quit', 'exit', or 'q' to end the session")
        print("- Type 'new' to start a new session")
        print("- Type 'help' for example queries")
        print("="*80)
        print()
        
        while True:
            try:
                # Get user input
                user_input = input("You: ").strip()
                
                if not user_input:
                    continue
                
                # Handle commands
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("\n👋 Thank you for using Industry Solutions Directory Chat!")
                    break
                
                if user_input.lower() == 'new':
                    self.session_id = f"interactive-{uuid.uuid4().hex[:8]}"
                    print(f"\n🔄 Started new session: {self.session_id}\n")
                    continue
                
                if user_input.lower() == 'help':
                    self.show_examples()
                    continue
                
                # Send message to API
                print("\n🔍 Searching for solutions...")
                result = self.send_message(user_input)
                
                if result:
                    self.display_response(result)
                
            except KeyboardInterrupt:
                print("\n\n👋 Session interrupted. Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ Unexpected error: {str(e)}")
                continue
    
    def show_examples(self):
        """Display example queries"""
        print("\n" + "="*80)
        print("EXAMPLE QUERIES:")
        print("="*80)
        print()
        print("Financial Services:")
        print("  - What financial services solutions help with risk management?")
        print("  - Show me anti-money laundering solutions")
        print("  - What solutions help with regulatory compliance?")
        print()
        print("Healthcare:")
        print("  - Show me AI-powered healthcare solutions")
        print("  - What solutions improve patient engagement?")
        print("  - Electronic health record solutions")
        print()
        print("Manufacturing:")
        print("  - What manufacturing solutions use IoT and AI?")
        print("  - Show me predictive maintenance solutions")
        print("  - Supply chain optimization for manufacturing")
        print()
        print("Education:")
        print("  - What solutions help with student engagement?")
        print("  - Campus management solutions")
        print("  - Fundraising solutions for higher education")
        print()
        print("Retail:")
        print("  - Customer experience solutions for retail")
        print("  - Inventory management solutions")
        print("  - Point of sale systems")
        print()
        print("Energy:")
        print("  - Sustainability solutions for energy companies")
        print("  - Asset management for oil and gas")
        print("  - Smart grid solutions")
        print()
        print("="*80 + "\n")


def main():
    """Main entry point"""
    client = InteractiveChatClient()
    client.run()


if __name__ == "__main__":
    main()
