# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import gradio as gr
import asyncio
import warnings

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from app.agent import app as mediguide_app
from app.security import sanitize_input, log_action

# Suppress internal ADK deprecation noise for create_session_sync
warnings.filterwarnings("ignore", category=DeprecationWarning)

# ---------------------------------------------------------------------------
# ADK Session and Runner Setup
#
# The Runner connects Gradio directly to the MediGuide multi-agent
# orchestrator, bypassing FastAPI. InMemorySessionService keeps conversation
# state for the lifetime of the process.
# ---------------------------------------------------------------------------
session_service = InMemorySessionService()
runner = Runner(app=mediguide_app, session_service=session_service)

USER_ID = "gradio_user"
SESSION_ID = "gradio_session"

# Pre-create the session so the first message is not dropped
_session = session_service.create_session_sync(
    app_name="app",
    user_id=USER_ID,
    session_id=SESSION_ID,
)


async def chat_with_agent(message: str, history: list) -> str:
    """Processes the user's message through the MediGuide multi-agent orchestrator.

    Sanitizes input, logs the action, calls the ADK runner in a background
    thread (to avoid blocking the async event loop), and returns the agent's
    text response.

    Args:
        message: The raw user input text.
        history: Gradio chat history (list of [user, assistant] pairs).

    Returns:
        str: The MediGuide agent response text, or a graceful error message.
    """
    try:
        # Sanitize for prompt injection (Coding Standard 7)
        sanitized = sanitize_input(message)
        log_action("gradio_ui", f"Incoming message: {sanitized}")

        def _run_agent() -> str:
            """Runs the ADK Runner synchronously and collects response text."""
            new_message = types.Content(
                role="user",
                parts=[types.Part.from_text(text=sanitized)],
            )
            events = runner.run(
                user_id=USER_ID,
                session_id=SESSION_ID,
                new_message=new_message,
            )
            parts = []
            for event in events:
                if event.content and event.content.parts:
                    for part in event.content.parts:
                        if part.text:
                            parts.append(part.text)
            return "".join(parts)

        # Offload blocking ADK call to a thread pool to keep the async loop free
        response = await asyncio.to_thread(_run_agent)
        log_action("gradio_ui", f"Response sent: {response[:80]}")
        return response

    except Exception as exc:
        error_msg = f"⚠️ An error occurred: {exc}"
        log_action("gradio_ui", f"Error: {exc}")
        return error_msg


# ---------------------------------------------------------------------------
# Gradio UI Layout
#
# gr.themes.Soft() is passed directly to gr.Blocks() (Gradio 4.x API).
# Three tabbed ChatInterface widgets share the same chat_with_agent handler so
# the conversation context is preserved across tabs within a single session.
# ---------------------------------------------------------------------------
with gr.Blocks(theme=gr.themes.Soft(), title="MediGuide") as demo:

    # ── Header ──────────────────────────────────────────────────────────────
    gr.Markdown(
        "# 💊 MediGuide\n"
        "### Your Personal AI Medication Assistant\n"
        "*Powered by Google ADK & Gemini 2.0*"
    )

    # ── Tabs ─────────────────────────────────────────────────────────────────
    with gr.Tabs():

        # Tab 1 — Medication Schedule
        with gr.Tab("💊 Medication Schedule"):
            gr.ChatInterface(
                fn=chat_with_agent,
                examples=[
                    "Add ibuprofen 400mg twice daily in the morning",
                    "What medications do I have scheduled?",
                    "What should I take today?",
                ],
            )

        # Tab 2 — Drug Safety (FDA data via OpenFDA tool)
        with gr.Tab("🔍 Drug Safety"):
            gr.ChatInterface(
                fn=chat_with_agent,
                examples=[
                    "Is it safe to take ibuprofen with aspirin?",
                    "What are the side effects of metformin?",
                    "Check interaction between paracetamol and alcohol",
                ],
            )

        # Tab 3 — Symptom Log
        with gr.Tab("📋 Symptom Log"):
            gr.ChatInterface(
                fn=chat_with_agent,
                examples=[
                    "Log a headache, severity 6",
                    "Show my symptom history for the past week",
                    "I've been feeling nauseous after taking my morning pills",
                ],
            )

    # ── Footer ───────────────────────────────────────────────────────────────
    gr.Markdown(
        "⚠️ *MediGuide provides general information only. "
        "Always consult a healthcare professional for medical advice.*"
    )


def create_ui() -> gr.Blocks:
    """Returns the initialized Gradio Blocks demo for import by app.py.

    Returns:
        gr.Blocks: The fully configured MediGuide Gradio interface.
    """
    return demo


if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
