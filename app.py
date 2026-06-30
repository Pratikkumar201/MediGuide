import os
from dotenv import load_dotenv

load_dotenv()

if not os.getenv("GEMINI_API_KEY"):
    raise ValueError("GEMINI_API_KEY environment variable not set")

from app.gradio_ui import create_ui

demo = create_ui()

if __name__ == "__main__":
    demo.launch()
