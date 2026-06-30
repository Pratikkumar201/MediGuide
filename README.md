---
title: MediGuide
emoji: 💊
colorFrom: blue
colorTo: green
sdk: gradio
sdk_version: "4.44.0"
app_file: app.py
pinned: false
---

# MediGuide - Personal AI Medication Management Agent

Capstone project for Kaggle 5-Day AI Agents Intensive Vibe Coding Course with Google

## What it does
MediGuide is a multi-agent AI system built with Google ADK that helps you manage medications, check drug safety, and track symptoms through a conversational Gradio interface.

## Architecture
User -> Gradio UI -> MediGuide Root Agent (Orchestrator)
                         |              |                |
              SchedulerAgent      DrugQAAgent      SymptomAgent
                    |                  |                |
               SQLite DB          OpenFDA MCP        SQLite DB

## Course Concepts Demonstrated
1. Multi-agent system (ADK) - Root orchestrator + 3 specialist sub-agents
2. MCP Server - OpenFDA drug database tool (Day 2)
3. Antigravity - Entire project built using vibe coding workflows
4. Security - Input sanitization, prompt injection prevention, audit logging
5. Deployability - Deployed to HuggingFace Spaces with public URL

## Setup Instructions
1. Clone this repo
2. Create .env file: GEMINI_API_KEY=your_key_here
3. Install dependencies: pip install -r requirements.txt
4. Run locally: python app.py
5. Open browser at http://localhost:7860

## Track
Concierge Agents

## Built With
- Google ADK 2.0
- Gemini 2.0 Flash
- Gradio 4.x
- OpenFDA API
- SQLite
- Python 3.11