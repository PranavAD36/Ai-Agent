# Dockerfile for deploying the Streamlit UI dashboard
FROM python:3.11-slim

# Install system dependencies (git is needed by GitPython for repo cloning)
RUN apt-get update && apt-get install -y \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install python packages
COPY code_review_agent/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the agent application code
COPY code_review_agent/ ./code_review_agent/

# Set PYTHONPATH so internal package imports resolve correctly
ENV PYTHONPATH=/app/code_review_agent

# Expose Streamlit default port
EXPOSE 8501

# Run the Streamlit application
CMD ["streamlit", "run", "code_review_agent/ui/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
