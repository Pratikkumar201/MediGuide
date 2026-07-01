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

FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user (required by HF Spaces)
RUN useradd -m -u 1000 user
USER user
ENV PATH="/home/user/.local/bin:$PATH"

WORKDIR /home/user/app

# Copy and install dependencies first (for layer caching)
COPY --chown=user requirements.txt .

# Install all deps from requirements.txt + a gradio version compatible with
# google-adk==2.1.0 (websockets>=15.0.1,<16).
# gradio>=4.44.0 uses gradio-client>=0.9 which supports websockets>=15.
RUN pip install --no-cache-dir \
    -r requirements.txt \
    "gradio>=4.44.0,<5.0.0" \
    "uvicorn>=0.14.0"

# Copy the rest of the application
COPY --chown=user . .

# HF Spaces Docker apps must listen on port 7860
EXPOSE 7860

# Set environment variable to tell Gradio which port to use
ENV GRADIO_SERVER_PORT=7860
ENV GRADIO_SERVER_NAME=0.0.0.0

CMD ["python", "app.py"]