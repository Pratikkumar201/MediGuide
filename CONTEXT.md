# MediGuide Coding Standards

This document outlines the permanent coding standards and constraints for the MediGuide project. All development must strictly adhere to these rules.

## 1. Project Overview
- **Project Name:** MediGuide
- **Description:** A personal AI medication management agent designed for the Kaggle 5-Day AI Agents Intensive Capstone (Concierge Agents track).

## 2. API & Authentication
- **NEVER** use Vertex AI (`google.cloud.aiplatform`, `google.environ["GOOGLE_GENAI_USE_VERTEXAI"]`, etc.) or `google.auth.default()`.
- **Authentication:** Use `GEMINI_API_KEY` from the `.env` file via `python-dotenv` instead.
- **Action Item:** Ensure all Vertex AI references are removed from `agent.py` and other modules.

## 3. Secret Management
- **NEVER** hardcode API keys, credentials, or secrets in the codebase.
- Always use `os.getenv()` or `os.environ` after loading environment variables with `python-dotenv`.

## 4. Model Selection
- The model to use is always **`gemini-2.0-flash`**.
- **NEVER** change this model target unless explicitly instructed by the user.

## 5. Python Code Quality
- All new Python files must use **type hints** for all function arguments and return values.
- All functions must have clear, descriptive **docstrings**.

## 6. Agent Tools
- All agent tools must be registered as **ADK FunctionTools**.

## 7. Input Sanitization
- Implement input sanitization: strip prompt injection patterns before passing user input to any LLM.

## 8. Topic Constraints
- The agent must **only** answer questions related to medications, symptoms, and health.
- All other topics must be refused politely.

## 9. Audit Logging
- Log all agent actions to `logs/audit.log` with a timestamp and action preview.

## 10. Deployment
- For HuggingFace Spaces deployment, the main entry point will be `app.py` at the root level using **Gradio**.
