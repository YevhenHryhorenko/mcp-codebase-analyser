FROM python:3.12-slim

ARG PORT=8050

WORKDIR /app

# Install system dependencies for git and healthcheck
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install uv

# Copy the MCP server files
COPY pyproject.toml .
COPY src/ ./src/

# Install packages
RUN python -m venv .venv
RUN uv pip install -e .

# Create directories for cache and database
RUN mkdir -p /app/repo_cache /app/chroma_db

# Set environment variables for defaults
ENV REPO_CACHE_DIR=/app/repo_cache
ENV CHROMA_PERSIST_DIR=/app/chroma_db

EXPOSE ${PORT}

# Command to run the MCP server
CMD ["uv", "run", "src/main.py"]