"""
Streamlit UI for Industry Solutions Directory Chat
"""

import streamlit as st
import requests
import uuid
import re
import os
from typing import Optional


# Page configuration
st.set_page_config(
    page_title="Industry Solutions Directory",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Industry-specific image URLs from Microsoft
INDUSTRY_IMAGES = {
    "Financial Services": "https://www.microsoft.com/en-us/industry/financial-services/media/financial-services-hero.jpg",
    "Healthcare": "https://www.microsoft.com/en-us/industry/health/media/healthcare-hero.jpg",
    "Manufacturing": "https://www.microsoft.com/en-us/industry/manufacturing/media/manufacturing-hero.jpg",
    "Education": "https://www.microsoft.com/en-us/education/media/education-hero.jpg",
    "Retail": "https://www.microsoft.com/en-us/industry/retail-consumer-goods/media/retail-hero.jpg",
    "Energy": "https://www.microsoft.com/en-us/industry/energy/media/energy-hero.jpg"
}

# Industry icons (emojis for better cross-platform support)
INDUSTRY_ICONS = {
    "Financial Services": "💰",
    "Healthcare": "🏥",
    "Manufacturing": "🏭",
    "Education": "📚",
    "Retail": "🛍️",
    "Energy": "⚡"
}

# Custom CSS for better styling with Microsoft branding
st.markdown("""
<style>
    /* Remove max-width constraint to use full available space */
    .main .block-container {
        max-width: 100%;
        padding-left: 2rem;
        padding-right: 2rem;
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    }
    
    /* Header styling */
    .app-header {
        background: linear-gradient(90deg, #0078d4 0%, #50e6ff 100%);
        padding: 2rem;
        border-radius: 0.5rem;
        margin-bottom: 2rem;
        text-align: center;
        color: white;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    .app-header h1 {
        color: white;
        font-size: 2.5rem;
        margin: 0;
        font-weight: 600;
    }
    
    .app-header p {
        color: #f0f0f0;
        font-size: 1.1rem;
        margin-top: 0.5rem;
    }
    
    .chat-message {
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .user-message {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-left: 4px solid #4c51bf;
    }
    .assistant-message {
        background-color: #ffffff;
        border-left: 4px solid #0078d4;
    }
    .citation-card {
        background-color: #fff;
        border: 1px solid #ddd;
        border-radius: 0.5rem;
        padding: 1rem;
        margin-bottom: 0.5rem;
        transition: transform 0.2s;
    }
    .citation-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.15);
    }
    .citation-title {
        font-weight: bold;
        color: #0078d4;
        font-size: 1.1rem;
    }
    .citation-partner {
        color: #666;
        font-size: 0.9rem;
    }
    .relevance-score {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 0.3rem 0.7rem;
        border-radius: 0.3rem;
        font-size: 0.8rem;
        font-weight: bold;
    }
    
    /* Industry category styling */
    .industry-category {
        padding: 0.5rem;
        margin: 0.5rem 0;
        border-radius: 0.3rem;
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    }
    
    /* Sidebar enhancements */
    .sidebar .sidebar-content {
        background-color: #f8f9fa;
    }
    
    /* Microsoft logo placeholder */
    .ms-logo {
        text-align: center;
        padding: 1rem;
        background: white;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)


class ChatClient:
    """Client for interacting with the backend API"""
    
    def __init__(self, base_url: str = None):
        # Use environment variable if available, otherwise default to localhost
        self.base_url = base_url or os.getenv("BACKEND_API_URL", "http://localhost:8000")
        self.chat_endpoint = f"{self.base_url}/api/chat"
        self.health_endpoint = f"{self.base_url}/api/health"
        self.history_endpoint = f"{self.base_url}/api/chat/history"
        self.summary_endpoint = f"{self.base_url}/api/chat/summary"
        self.export_endpoint = f"{self.base_url}/api/chat/export"
    
    def check_health(self) -> bool:
        """Check if the backend API is available"""
        try:
            response = requests.get(self.health_endpoint, timeout=5)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False
    
    def send_message(self, message: str, session_id: str) -> Optional[dict]:
        """Send a message to the chat API"""
        try:
            payload = {
                "message": message,
                "session_id": session_id
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
                st.error(f"API returned status code {response.status_code}")
                return None
                
        except requests.exceptions.Timeout:
            st.error("Request timed out. The backend may be processing a complex query.")
            return None
        except requests.exceptions.RequestException as e:
            st.error(f"Failed to connect to API: {str(e)}")
            return None
    
    def get_history(self, session_id: str) -> Optional[list]:
        """Get chat history for a session"""
        try:
            response = requests.get(
                f"{self.history_endpoint}/{session_id}",
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get("messages", [])
            return None
        except requests.exceptions.RequestException:
            return None
    
    def get_summary(self, session_id: str) -> Optional[dict]:
        """Generate a conversation summary"""
        try:
            response = requests.post(
                f"{self.summary_endpoint}/{session_id}",
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                st.error(f"Failed to generate summary: {response.status_code}")
                return None
        except requests.exceptions.RequestException as e:
            st.error(f"Failed to generate summary: {str(e)}")
            return None
    
    def export_conversation(self, session_id: str, format: str = "markdown") -> Optional[dict]:
        """Export conversation as downloadable file"""
        try:
            response = requests.get(
                f"{self.export_endpoint}/{session_id}",
                params={"format": format},
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                st.error(f"Failed to export conversation: {response.status_code}")
                return None
        except requests.exceptions.RequestException as e:
            st.error(f"Failed to export conversation: {str(e)}")
            return None


def clean_html(text: str) -> str:
    """Remove HTML tags from text"""
    clean_text = re.sub('<[^<]+?>', '', text)
    clean_text = clean_text.replace('&#160;', ' ').replace('&nbsp;', ' ')
    clean_text = clean_text.replace('&#8217;', "'").replace('&rsquo;', "'")
    clean_text = clean_text.replace('&#8211;', '-').replace('&ndash;', '-')
    clean_text = clean_text.replace('&#8212;', '—').replace('&mdash;', '—')
    return clean_text.strip()


def display_citation(citation: dict, index: int):
    """Display a citation card with visual enhancements"""
    with st.expander(f"📄 {citation.get('solution_name', 'Unknown Solution')}", expanded=False):
        # Add solution icon/thumbnail placeholder
        col_img, col_content = st.columns([1, 4])
        
        with col_img:
            # Use a generic partner/solution icon
            st.markdown("""
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                        padding: 1rem; border-radius: 0.5rem; text-align: center;">
                <span style="font-size: 2rem;">🎯</span>
            </div>
            """, unsafe_allow_html=True)
        
        with col_content:
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown(f"**Partner:** {citation.get('partner_name', 'Unknown Partner')}")
            
            with col2:
                score = citation.get('relevance_score', 0)
                st.markdown(f"<span class='relevance-score'>Score: {score:.4f}</span>", unsafe_allow_html=True)
        
        # Clean and display description
        description = citation.get('description', 'No description available')
        clean_desc = clean_html(description)
        
        if len(clean_desc) > 300:
            clean_desc = clean_desc[:300] + "..."
        
        st.markdown(f"_{clean_desc}_")
        
        url = citation.get('url', '')
        if url:
            st.markdown(f"[🔗 Search for this solution on Microsoft Solutions Directory]({url})")
            st.caption("💡 Tip: Click the link to search, then select the solution from the results to view full details.")


def display_message(message: dict, is_user: bool = False):
    """Display a chat message"""
    if is_user:
        st.markdown(f"""
        <div class="chat-message user-message">
            <strong>You:</strong><br/>
            {message.get('content', '')}
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="chat-message assistant-message">
            <strong>Assistant:</strong><br/>
            {message.get('content', '')}
        </div>
        """, unsafe_allow_html=True)
        
        # Display follow-up questions if available
        follow_up_questions = message.get('follow_up_questions', [])
        if follow_up_questions:
            st.markdown("#### 💬 Follow-up Questions")
            st.caption("Click a question to continue the conversation:")
            
            # Display questions as clickable pills in columns
            cols = st.columns(min(len(follow_up_questions), 2))
            for i, question in enumerate(follow_up_questions):
                with cols[i % 2]:
                    # Use unique key based on message index and question index
                    msg_idx = st.session_state.messages.index(message)
                    button_key = f"followup_{msg_idx}_{i}"
                    if st.button(
                        f"❓ {question}", 
                        key=button_key, 
                        use_container_width=True,
                        type="secondary"
                    ):
                        # Store the selected question to be processed
                        st.session_state.selected_followup = question
                        st.rerun()
        
        # Display citations if available
        citations = message.get('citations', [])
        if citations:
            st.markdown("### 📚 Related Solutions")
            for i, citation in enumerate(citations, 1):
                display_citation(citation, i)


def sidebar():
    """Render the sidebar"""
    with st.sidebar:
        # Microsoft branding
        st.markdown("""
        <div class="ms-logo">
            <img src="https://img-prod-cms-rt-microsoft-com.akamaized.net/cms/api/am/imageFileData/RE1Mu3b?ver=5c31" 
                 alt="Microsoft Logo" style="width: 150px; margin-bottom: 0.5rem;">
        </div>
        """, unsafe_allow_html=True)
        
        st.title("🏢 Industry Solutions Directory")
        st.markdown("---")
        
        # Session management
        st.subheader("Session Management")
        
        if st.button("🔄 New Session", use_container_width=True):
            st.session_state.session_id = f"streamlit-{uuid.uuid4().hex[:8]}"
            st.session_state.messages = []
            st.rerun()
        
        st.caption(f"Session ID: `{st.session_state.get('session_id', 'N/A')}`")
        
        st.markdown("---")
        
        # Example queries
        st.subheader("💡 Example Questions")
        
        examples = {
            "Financial Services": [
                "What financial services solutions help with risk management?",
                "Show me anti-money laundering solutions"
            ],
            "Healthcare": [
                "Show me AI-powered healthcare solutions",
                "What solutions improve patient engagement?"
            ],
            "Manufacturing": [
                "What manufacturing solutions use IoT and AI?",
                "Show me predictive maintenance solutions"
            ],
            "Education": [
                "What solutions help with student engagement?",
                "Fundraising solutions for higher education"
            ],
            "Retail": [
                "Customer experience solutions for retail",
                "Inventory management solutions"
            ],
            "Energy": [
                "Sustainability solutions for energy companies",
                "Smart grid solutions"
            ]
        }
        
        for category, questions in examples.items():
            icon = INDUSTRY_ICONS.get(category, "📁")
            with st.expander(f"{icon} {category}"):
                for question in questions:
                    if st.button(question, key=question, use_container_width=True):
                        st.session_state.selected_question = question
                        st.rerun()
        
        st.markdown("---")
        
        # Backend status
        st.subheader("🔌 Backend Status")
        client = ChatClient()
        if client.check_health():
            st.success("✅ Connected")
        else:
            st.error("❌ Disconnected")
            st.caption("Make sure backend is running:")
            st.code("cd backend && python -m uvicorn app.main:app --reload", language="bash")
        
        st.markdown("---")
        
        # Info
        st.subheader("ℹ️ About")
        st.caption("""
        This chat interface helps you discover Microsoft partner solutions 
        across various industries including Financial Services, Healthcare, 
        Manufacturing, Education, Retail, and more.
        """)


def main():
    """Main application"""
    
    # Initialize session state
    if 'session_id' not in st.session_state:
        st.session_state.session_id = f"streamlit-{uuid.uuid4().hex[:8]}"
    
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    
    if 'selected_question' not in st.session_state:
        st.session_state.selected_question = None
    
    if 'selected_followup' not in st.session_state:
        st.session_state.selected_followup = None
    
    # Render sidebar
    sidebar()
    
    # Main content with header banner
    st.markdown("""
    <div class="app-header">
        <h1>💬 Industry Solutions Chat</h1>
        <p>Discover Microsoft partner solutions powered by AI • Serving 50+ industries worldwide</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Display chat history
    chat_container = st.container()
    with chat_container:
        if not st.session_state.messages:
            # Welcome message with visual elements
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                st.markdown("""
                <div style="text-align: center; padding: 2rem; background: white; border-radius: 1rem; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                    <img src="https://img-prod-cms-rt-microsoft-com.akamaized.net/cms/api/am/imageFileData/RWfkqT?ver=2740" 
                         alt="Solutions" style="width: 200px; margin-bottom: 1rem; border-radius: 0.5rem;">
                    <h3 style="color: #0078d4;">👋 Welcome to Industry Solutions Directory!</h3>
                    <p style="color: #666;">Ask me about Microsoft partner solutions or select an example question from the sidebar.</p>
                    <p style="color: #999; font-size: 0.9rem;">Powered by Azure OpenAI & Cognitive Search</p>
                </div>
                """, unsafe_allow_html=True)
        else:
            for msg in st.session_state.messages:
                display_message(msg, is_user=msg.get('role') == 'user')
    
    # Conversation Actions (only show if there are messages)
    if st.session_state.messages:
        st.markdown("---")
        st.subheader("📋 Conversation Actions")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📝 Generate Summary", use_container_width=True):
                with st.spinner("Generating summary..."):
                    client = ChatClient()
                    summary_result = client.get_summary(st.session_state.session_id)
                    
                    if summary_result:
                        st.session_state.summary = summary_result
                        st.success("✅ Summary generated!")
                        st.rerun()
        
        with col2:
            download_format = st.selectbox("Format", ["Markdown", "Text"], label_visibility="collapsed")
            if st.button("💾 Download Conversation", use_container_width=True):
                with st.spinner("Preparing download..."):
                    client = ChatClient()
                    export_result = client.export_conversation(
                        st.session_state.session_id, 
                        download_format.lower()
                    )
                    
                    if export_result:
                        st.download_button(
                            label=f"⬇️ Download as {download_format}",
                            data=export_result.get('content', ''),
                            file_name=export_result.get('filename', f'conversation.{download_format.lower()}'),
                            mime='text/markdown' if download_format == 'Markdown' else 'text/plain',
                            use_container_width=True
                        )
        
        # Display summary if generated
        if 'summary' in st.session_state and st.session_state.summary:
            with st.expander("📄 Conversation Summary", expanded=True):
                st.markdown(st.session_state.summary.get('summary', ''))
                st.caption(f"Based on {st.session_state.summary.get('message_count', 0)} messages")
    
    # Chat input
    st.markdown("---")
    
    # Check if a question was selected from sidebar or follow-up
    initial_value = ""
    if st.session_state.selected_question:
        initial_value = st.session_state.selected_question
        st.session_state.selected_question = None
    elif st.session_state.selected_followup:
        initial_value = st.session_state.selected_followup
        st.session_state.selected_followup = None
    
    user_input = st.chat_input("Type your question here...", key="chat_input")
    
    # If we have initial value, use it
    if initial_value and not user_input:
        user_input = initial_value
    
    if user_input:
        # Add user message to history
        st.session_state.messages.append({
            'role': 'user',
            'content': user_input
        })
        
        # Show thinking spinner
        with st.spinner("🔍 Searching for solutions..."):
            client = ChatClient()
            result = client.send_message(user_input, st.session_state.session_id)
        
        if result:
            # Add assistant response to history with follow-up questions
            st.session_state.messages.append({
                'role': 'assistant',
                'content': result.get('response', ''),
                'citations': result.get('citations', []),
                'follow_up_questions': result.get('follow_up_questions', [])
            })
        
        # Rerun to display new messages
        st.rerun()


if __name__ == "__main__":
    main()
