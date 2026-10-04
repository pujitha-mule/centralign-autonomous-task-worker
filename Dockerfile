FROM mcr.microsoft.com/playwright/python:v1.47.0-jammy

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1

COPY requirements.txt .

RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .

ENV PORT=10000

EXPOSE 10000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import urllib.request,os; urllib.request.urlopen(f'http://127.0.0.1:{os.getenv(\"PORT\",\"10000\")}/healthz')" || exit 1

CMD ["sh", "-c", "uvicorn app:app --host 0.0.0.0 --port ${PORT}"]