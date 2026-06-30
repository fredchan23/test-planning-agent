FROM python:3.12-slim

WORKDIR /app

# Install system dependencies if any are needed
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy pyproject.toml and source code
COPY pyproject.toml .
COPY test_planner_agent/ test_planner_agent/

# Install python packages using pip
RUN pip install --no-cache-dir .

EXPOSE 8080

CMD ["python", "-m", "test_planner_agent.app"]
