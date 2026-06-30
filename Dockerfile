FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY pyproject.toml README.md ./
COPY src ./src
COPY data ./data
COPY tests ./tests

ENV PYTHONPATH=/app/src

EXPOSE 8000

CMD ["uvicorn", "agentic_ops_copilot.api:app", "--host", "0.0.0.0", "--port", "8000"]
