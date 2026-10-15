# syntax=docker/dockerfile:1

# ---------- base: shared by every stage ----------
FROM python:3.12-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
WORKDIR /app
RUN useradd --create-home --uid 1000 appuser

# ---------- api-deps: the API's libraries ----------
FROM base AS api-deps
# TODO(Lab 2): copy the requirements folder before the code, so the install layer stays cached
COPY requirements/ requirements/
RUN pip install --no-cache-dir -r requirements/api.txt

# ---------- test: pytest on Python 3.12, whatever your machine runs ----------
FROM api-deps AS test
RUN pip install --no-cache-dir -r requirements/dev.txt
COPY pyproject.toml .
COPY skydesk/ skydesk/
COPY tests/ tests/
CMD ["python", "-m", "pytest", "-q"]

# ---------- api: the runtime image ----------
FROM api-deps AS api
COPY skydesk/ skydesk/
USER appuser
EXPOSE 8000
# TODO(Lab 2): exec form: uvicorn serving skydesk.api.main:app on host 0.0.0.0, port 8000
CMD ["uvicorn", "skydesk.api.main:app", "--host", "0.0.0.0", "--port", "8000"]