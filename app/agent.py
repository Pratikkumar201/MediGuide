# ruff: noqa
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

import os
from dotenv import load_dotenv
from typing import Optional

# Import ADK core constructs
from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.tools import FunctionTool
from google.adk.agents.llm_agent import CallbackContext
from google.genai import types

# Import tools and security helpers
from app.medication_tools import add_medication, get_medications, get_todays_schedule, log_symptom, get_symptom_history
from app.openfda_tool import get_drug_info, check_drug_interaction
from app.security import sanitize_input, is_medical_query, log_action

# Load local environment variables
load_dotenv()
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "False"

# ============================================================================
# MULTI-AGENT ARCHITECTURE PATTERN
#
# This file implements a hierarchical multi-agent pattern.
# - A root orchestrator (mediguide) is the user-facing agent.
# - The orchestrator routes user queries dynamically to one of three specialized sub-agents
#   (medication_scheduler, drug_qa, symptom_tracker) using tool transfer.
# - A pre-execution hook (before_agent_callback) is configured to enforce security and guardrails,
#   such as input sanitization, health topic validation, and custom first-turn onboarding.
# ============================================================================

# Wrapping imported python tools as ADK FunctionTools (Coding Standard 6)
add_medication_tool = FunctionTool(add_medication)
get_medications_tool = FunctionTool(get_medications)
get_todays_schedule_tool = FunctionTool(get_todays_schedule)

get_drug_info_tool = FunctionTool(get_drug_info)
check_drug_interaction_tool = FunctionTool(check_drug_interaction)

log_symptom_tool = FunctionTool(log_symptom)
get_symptom_history_tool = FunctionTool(get_symptom_history)


# AGENT 1: scheduler_agent
scheduler_agent = Agent(
    name="medication_scheduler",
    model="gemini-2.0-flash",
    tools=[add_medication_tool, get_medications_tool, get_todays_schedule_tool],
    instruction=(
        "You are a medication schedule manager. Help users add medications and check their daily schedule. "
        "Ask for: drug name, dosage (e.g. 500mg), frequency (once/twice/three times daily), "
        "time of day (morning/afternoon/evening/night), and any notes. Always confirm before adding. "
        "Only discuss medication scheduling - for drug safety questions tell the user to ask about drug interactions instead."
    )
)

# AGENT 2: drug_qa_agent  
drug_qa_agent = Agent(
    name="drug_qa",
    model="gemini-2.0-flash",
    tools=[get_drug_info_tool, check_drug_interaction_tool],
    instruction=(
        "You are a medication safety assistant. Use FDA data to answer questions about drug interactions, warnings, and dosages. "
        "ALWAYS end every response with: 'Please consult your doctor or pharmacist before making any medication decisions.' "
        "Only answer medication-related questions."
    )
)

# AGENT 3: symptom_agent
symptom_agent = Agent(
    name="symptom_tracker",
    model="gemini-2.0-flash",
    tools=[log_symptom_tool, get_symptom_history_tool],
    instruction=(
        "You are a symptom tracker. Help users log daily symptoms (ask for symptom description and severity 1-10) "
        "and provide weekly summaries. Always recommend seeing a doctor for severe symptoms (severity 7+). "
        "Only discuss symptom tracking."
    )
)


# Security & Onboarding pre-agent callback
def before_agent_callback(callback_context: CallbackContext) -> Optional[types.Content]:
    """Sanitizes input and enforces the medical-topic guardrail before routing.

    Strips prompt injection patterns, logs the action, and refuses clearly
    non-medical queries. Returns None to let the agent handle everything else.

    Args:
        callback_context: The context containing details about the active conversation turn.

    Returns:
        Optional[types.Content]: Refusal message if the query is off-topic, or None to continue.
    """
    user_content = callback_context.user_content
    user_text = ""
    if user_content and user_content.parts:
        user_text = "".join(part.text for part in user_content.parts if part.text)

    # 1. Sanitize user input (strip common prompt injections)
    sanitized = sanitize_input(user_text)

    # 2. Log the action
    log_action("mediguide", f"Received query: {sanitized}")

    # 3. Refuse clearly non-medical queries
    if not is_medical_query(sanitized):
        log_action("mediguide", "Refused non-medical topic query")
        return types.Content(
            role="model",
            parts=[types.Part.from_text(
                text=(
                    "I'm sorry, I can only help you with questions related to medications, symptoms, and health. "
                    "Please ask a question about medication schedules, drug safety, or symptom tracking!"
                )
            )]
        )

    # 4. Allow the agent to handle the query normally
    return None


# Root orchestrator
root_agent = Agent(
    name="mediguide",
    model="gemini-2.0-flash",
    sub_agents=[scheduler_agent, drug_qa_agent, symptom_agent],
    before_agent_callback=before_agent_callback,
    instruction=(
        "You are MediGuide, a personal AI medication management assistant.\n\n"
        "Route requests to the right specialist:\n"
        "- Questions about adding medications, schedule, what to take today → transfer to medication_scheduler\n"
        "- Questions about drug interactions, side effects, warnings, FDA info → transfer to drug_qa\n"
        "- Questions about logging symptoms, how I've been feeling, symptom history → transfer to symptom_tracker\n\n"
        "Before routing, always:\n"
        "1. Check if the query is health/medication related\n"
        "2. Greet new users warmly and explain you can help with: medication schedules, drug safety questions, and symptom tracking\n"
        "3. For completely unrelated topics, politely decline and redirect to your health capabilities\n\n"
        "Welcome message for first interaction: 'Welcome to MediGuide! I am your personal AI medication assistant. "
        "I can help you: 💊 Manage your medication schedule, 🔍 Check drug interactions and safety info, 📋 Track your symptoms. "
        "What would you like help with today?'"
    )
)

# App instance
app = App(
    root_agent=root_agent,
    name="app",
)
