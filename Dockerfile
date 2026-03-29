# GCP Cloud Run / Cloud Build friendly image (CPU-only).
FROM python:3.11-slim

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY pm_eval ./pm_eval
COPY agent ./agent
COPY artifacts ./artifacts
RUN mkdir -p logs

# Default: run eval on bundled draft (override CMD in Cloud Run for optimize loop).
CMD ["python", "-m", "pm_eval.suite", "artifacts/test_cases/aurora_prototype_testing_prompt_draft.md"]
