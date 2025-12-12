"""Gradio UI for the Industry Solutions Directory chat experience."""

from __future__ import annotations

import json
import os
import re
import uuid
from typing import Generator, List, Optional, Tuple

import gradio as gr
import requests


DEFAULT_BACKEND_URL = "http://localhost:8000"
SESSION_PREFIX = "gradio"
HEALTH_TIMEOUT_SECONDS = 5
STREAM_TIMEOUT_SECONDS = 90


class ChatClient:
    """Minimal client that talks to the backend streaming endpoint."""

    def __init__(self, base_url: Optional[str] = None) -> None:
        raw_url = base_url or os.getenv("BACKEND_API_URL", DEFAULT_BACKEND_URL)
        self.base_url = raw_url.rstrip("/")
        self.chat_stream_endpoint = f"{self.base_url}/api/chat/stream"
        self.health_endpoint = f"{self.base_url}/api/health"

    def check_health(self) -> bool:
        try:
            response = requests.get(self.health_endpoint, timeout=HEALTH_TIMEOUT_SECONDS)
        except requests.RequestException:
            return False
        return response.status_code == 200

    def send_message_stream(self, message: str, session_id: str) -> Generator[dict, None, None]:
        payload = {"message": message, "session_id": session_id}
        headers = {"Content-Type": "application/json"}

        try:
            response = requests.post(
                self.chat_stream_endpoint,
                json=payload,
                headers=headers,
                stream=True,
                timeout=STREAM_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
        except requests.HTTPError as exc:
            status = exc.response.status_code if exc.response else "unknown"
            yield {"type": "error", "error": f"Backend returned HTTP {status}."}
            return
        except requests.RequestException as exc:
            yield {"type": "error", "error": f"Connection error: {exc}"}
            return

        for raw_line in response.iter_lines(decode_unicode=True):
            if not raw_line:
                continue
            line = raw_line.strip()
            if not line.startswith("data:"):
                continue

            data_str = line.split("data:", 1)[1].strip()
            if not data_str:
                continue

            try:
                event = json.loads(data_str)
            except json.JSONDecodeError:
                continue

            yield event


def clean_html(text: str) -> str:
    cleaned = re.sub(r"<[^>]+>", "", text or "")
    replacements = {
        "&#160;": " ",
        "&nbsp;": " ",
        "&#8217;": "'",
        "&rsquo;": "'",
        "&#8211;": "-",
        "&ndash;": "-",
        "&#8212;": "-",
        "&mdash;": "-",
    }
    for token, replacement in replacements.items():
        cleaned = cleaned.replace(token, replacement)
    return cleaned.strip()


def format_citations(citations: List[dict]) -> str:
    if not citations:
        return ""

    lines = ["\n\n### 📚 Related Solutions\n"]
    for index, citation in enumerate(citations, start=1):
        name = citation.get("solution_name", "Unknown Solution")
        partner = citation.get("partner_name", "Unknown Partner")
        description = clean_html(citation.get("description", "No description available"))
        if len(description) > 200:
            description = f"{description[:200]}..."
        score = citation.get("relevance_score")
        url = citation.get("url", "")

        lines.append(f"**{index}. {name}**")
        lines.append(f"- **Partner:** {partner}")
        if isinstance(score, (int, float)):
            lines.append(f"- **Relevance:** {score:.4f}")
        lines.append(f"- **Description:** {description}")
        if url:
            lines.append(f"- [🔗 View Solution]({url})")
        lines.append("")

    return "\n".join(lines)


def format_follow_up(questions: List[str]) -> str:
    if not questions:
        return ""

    formatted = ["\n\n### 💬 Suggested Follow-up Questions\n"]
    for index, question in enumerate(questions, start=1):
        formatted.append(f"{index}. {question}")
    return "\n".join(formatted)


def new_session_id() -> str:
    return f"{SESSION_PREFIX}-{uuid.uuid4().hex[:8]}"


def session_label(session_id: str) -> str:
    return f"Session ID: `{session_id}`"


def stream_chat(
    message: str,
    history: List[Tuple[str, str]],
    session_id: str,
) -> Generator[Tuple[List[Tuple[str, str]], str, str], None, None]:
    message = (message or "").strip()
    history = list(history or [])
    session_id = session_id or new_session_id()

    if not message:
        yield history, session_id, session_label(session_id)
        return

    history.append((message, ""))
    yield history, session_id, session_label(session_id)

    client = ChatClient()
    if not client.check_health():
        history[-1] = (
            message,
            "❌ **Error:** Backend API is not reachable. Verify the backend service URL and try again.",
        )
        yield history, session_id, session_label(session_id)
        return

    response_chunks: List[str] = []
    citations: List[dict] = []
    follow_up_questions: List[str] = []

    for event in client.send_message_stream(message, session_id):
        event_type = event.get("type")

        if event_type == "session":
            session_id = event.get("session_id", session_id)
            yield history, session_id, session_label(session_id)
            continue

        if event_type == "citations":
            citations = event.get("citations", [])
            continue

        if event_type == "follow_up":
            follow_up_questions = event.get("questions", [])
            continue

        if event_type == "content":
            chunk = event.get("content", "")
            if chunk:
                response_chunks.append(chunk)
                history[-1] = (message, "".join(response_chunks) + "▌")
                yield history, session_id, session_label(session_id)
            continue

        if event_type == "error":
            error_message = event.get("error", "Unexpected error")
            history[-1] = (message, f"❌ **Error:** {error_message}")
            yield history, session_id, session_label(session_id)
            return

        if event_type == "done":
            break

    final_response = "".join(response_chunks)
    if not final_response:
        final_response = "⚠️ The backend did not return any content."

    final_response += format_citations(citations)
    final_response += format_follow_up(follow_up_questions)

    history[-1] = (message, final_response)
    yield history, session_id, session_label(session_id)


def reset_session() -> Tuple[List[Tuple[str, str]], str, str]:
    session_id = new_session_id()
    return [], session_id, session_label(session_id)


def check_backend_status() -> str:
    client = ChatClient()
    if client.check_health():
        return f"✅ Backend is connected\n\n**Endpoint:** `{client.base_url}`"
    return f"❌ Backend is not available\n\n**Endpoint:** `{client.base_url}`"


EXAMPLE_QUESTIONS = [
    # Industry-focused queries
    "What AI solutions are available for healthcare patient engagement?",
    "Show me financial risk management solutions",
    "Find retail customer experience solutions",
    # Technology-focused queries
    "What Cloud and AI Platform solutions are available?",
    "Show me Security solutions for data protection",
    "What AI Business Solutions help with automation?",
    # Combined queries
    "What IoT and AI solutions help with manufacturing?",
    "Find AI security solutions for healthcare",
]


custom_css = """
.gradio-container {
    max-width: 100% !important;
    padding: 16px !important;
}

.example-btn {
    border-radius: 8px;
    padding: 10px;
    text-align: left;
}

.example-btn:hover {
    border-color: #0078d4;
}
"""


def create_example_handler(example_text: str):
    """Create a generator function that runs stream_chat with a pre-filled prompt."""
    def handler(history: List[Tuple[str, str]], session_id: str):
        yield from stream_chat(example_text, history, session_id)
    return handler


def build_interface() -> gr.Blocks:
    with gr.Blocks(
        title="Industry Solutions Directory Chat",
        theme=gr.themes.Soft(primary_hue="blue", secondary_hue="purple"),
        css=custom_css,
    ) as demo:
        initial_session_id = new_session_id()
        session_state = gr.State(value=initial_session_id)

        gr.HTML(
            """
            <div style="text-align: center; margin-bottom: 16px; padding: 24px; background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);">
                <div style="display: flex; align-items: center; justify-content: center; gap: 16px;">
                    <img src="https://upload.wikimedia.org/wikipedia/commons/4/44/Microsoft_logo.svg" alt="Microsoft" style="height: 40px;">
                    <div style="font-size: 30px; font-weight: 600; color: #0078d4;">|</div>
                    <div style="font-size: 30px; font-weight: 600; color: #262626;">Industry Solutions Directory</div>
                </div>
            </div>
            """
        )

        gr.Markdown(
            """
            ### 🎯 Discover Microsoft Partner Solutions with AI-powered guidance
            
            **Browse by Industry** (Healthcare, Education, Financial Services, Manufacturing, Retail, etc.) **OR by Technology** (AI Business Solutions, Cloud & AI Platforms, Security) - or combine both!
            
            Ask questions like:
            - "What AI solutions help with healthcare patient engagement?"
            - "Show me Cloud and AI Platform solutions"
            - "Find Security solutions for financial services"
            """
        )

        with gr.Row():
            with gr.Column(scale=4):
                chatbot = gr.Chatbot(
                    label="Chat",
                    height=680,
                    show_label=False,
                    avatar_images=(
                        None,
                        "https://img-prod-cms-rt-microsoft-com.akamaized.net/cms/api/am/imageFileData/RE1Mu3b?ver=5c31",
                    ),
                )

                with gr.Row():
                    message_box = gr.Textbox(
                        placeholder="Ask about solutions by industry, technology, or both...",
                        show_label=False,
                        scale=9,
                    )
                    send_button = gr.Button("Send", variant="primary", scale=1)

                new_session_button = gr.Button("🔄 New Session", variant="secondary")

            with gr.Column(scale=1):
                gr.Markdown("### 💡 Example Questions")
                example_buttons = []
                for example in EXAMPLE_QUESTIONS:
                    example_button = gr.Button(example, elem_classes=["example-btn"], size="sm")
                    example_buttons.append((example_button, example))

                gr.Markdown("---")

                gr.Markdown("### 📊 Session Info")
                session_display = gr.Markdown(session_label(initial_session_id))

                gr.Markdown("---")

                gr.Markdown("### 🔌 Backend Status")
                status_display = gr.Markdown("Checking...")
                status_button = gr.Button("Check Status", size="sm")

                gr.Markdown("---")

                gr.Markdown(
                    """
                    ### ℹ️ About
                    
                    **Search 500+ Microsoft Partner Solutions**
                    
                    Browse by:
                    - 🏢 **Industry**: Healthcare, Education, Financial Services, Manufacturing, Retail, Government, and more
                    - 💻 **Technology**: AI Business Solutions, Cloud & AI Platforms, Security
                    - 🔀 **Combined**: Technology + Industry (e.g., "AI for healthcare")
                    
                    Powered by Azure OpenAI, Azure AI Search, and Cosmos DB.
                    """
                )

        gr.Markdown(
            """
            ---
            **Industry Solutions Directory** | Powered by Azure OpenAI & AI Search | Built by Microsoft Industry Solutions
            """
        )

        message_box.submit(
            fn=stream_chat,
            inputs=[message_box, chatbot, session_state],
            outputs=[chatbot, session_state, session_display],
        ).then(lambda: "", outputs=[message_box])

        send_button.click(
            fn=stream_chat,
            inputs=[message_box, chatbot, session_state],
            outputs=[chatbot, session_state, session_display],
        ).then(lambda: "", outputs=[message_box])

        new_session_button.click(
            fn=reset_session,
            outputs=[chatbot, session_state, session_display],
        ).then(check_backend_status, outputs=[status_display])

        for button, example in example_buttons:
            button.click(
                fn=create_example_handler(example),
                inputs=[chatbot, session_state],
                outputs=[chatbot, session_state, session_display],
            ).then(lambda: "", outputs=[message_box])

        status_button.click(fn=check_backend_status, outputs=[status_display])
        demo.load(fn=check_backend_status, outputs=[status_display])

    return demo


if __name__ == "__main__":
    gradio_app = build_interface()
    gradio_app.queue()
    gradio_app.launch(server_name="0.0.0.0", server_port=7860, share=False, show_error=True)
