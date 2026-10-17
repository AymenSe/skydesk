# syntax=docker/dockerfile:1

# ---------- base: shared by every stage ----------
FROM python:3.12-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
WORKDIR /app
RUN useradd --create-home --uid 1000 appuser

# ---------- api-deps: CPU-only torch + API libraries ----------
FROM base AS api-deps
# TODO(Lab 4): install torch from PyTorch's CPU-only package index
RUN pip install --no-cache-dir torch==2.14.1 --index-url https://download.pytorch.org/whl/cpu
# Copy only what this layer needs, so editing dev.txt doesn't reinstall the API libraries
COPY requirements/base.txt requirements/api.txt requirements/
RUN pip install --no-cache-dir -r requirements/api.txt

# ---------- trainer: builds the classifier artifacts ----------
FROM api-deps AS trainer
COPY data/ data/
COPY training/ training/
# TODO(Lab 4): run the training script; a failed quality gate fails the build
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
# Never contact the Hugging Face Hub at runtime; everything needed is baked in
ENV HF_HUB_OFFLINE=1
# TODO(Lab 4): copy only the trained artifacts out of the trainer stage
COPY --from=trainer /app/artifacts artifacts/
COPY skydesk/ skydesk/
USER appuser
EXPOSE 8000
CMD ["uvicorn", "skydesk.api.main:app", "--host", "0.0.0.0", "--port", "8000"]