# syntax=docker/dockerfile:1

# ---------- base: shared by every stage ----------
FROM python:3.12-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
WORKDIR /app
RUN useradd --create-home --uid 1000 appuser

# ---------- api-deps: CPU-only torch + API libraries ----------
FROM base AS api-deps
RUN pip install --no-cache-dir torch==2.14.1 --index-url https://download.pytorch.org/whl/cpu
COPY requirements/base.txt requirements/api.txt requirements/
RUN pip install --no-cache-dir -r requirements/api.txt

# ---------- trainer: builds the classifier artifacts ----------
FROM api-deps AS trainer
COPY data/ data/
COPY training/ training/
RUN python training/train_intents.py && chmod -R a+rX artifacts

# ---------- test: pytest, with the trained artifacts ----------
FROM api-deps AS test
COPY requirements/dev.txt requirements/
RUN pip install --no-cache-dir -r requirements/dev.txt
COPY --from=trainer /app/artifacts artifacts/
COPY pyproject.toml .
COPY skydesk/ skydesk/
COPY tests/ tests/
CMD ["python", "-m", "pytest", "-q"]

# ---------- api: the runtime image ----------
FROM api-deps AS api
ENV HF_HUB_OFFLINE=1
COPY --from=trainer /app/artifacts artifacts/
COPY skydesk/ skydesk/
USER appuser
EXPOSE 8000
CMD ["uvicorn", "skydesk.api.main:app", "--host", "0.0.0.0", "--port", "8000"]


# ---------- worker: the GPU drafting service ----------
FROM base AS worker
ARG TORCH_INDEX=https://download.pytorch.org/whl/cu126
RUN pip install --no-cache-dir torch==2.14.1 --index-url $TORCH_INDEX
COPY requirements/base.txt requirements/worker.txt requirements/
RUN pip install --no-cache-dir -r requirements/worker.txt
RUN mkdir /models && chown appuser:appuser /models
ENV HF_HOME=/models
COPY skydesk/ skydesk/
USER appuser
CMD ["python", "-m", "skydesk.worker.main"]