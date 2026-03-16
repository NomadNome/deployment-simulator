FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY pyproject.toml .
RUN pip install --no-cache-dir anthropic pydantic rich python-dotenv

# Copy source
COPY src/ src/
COPY field_tested_tactics.py .
COPY research_backed_tactics.py .

# Copy the agent server
COPY src/sandbox/agent_server.py .

EXPOSE 8080

CMD ["python", "agent_server.py"]
