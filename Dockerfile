FROM python:3.12.9-alpine3.21

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN mkdir -p /app/templates \
    && adduser --disabled-password --gecos "" appuser \
    && chown -R appuser:appuser /app

COPY --chown=appuser:appuser . .

VOLUME [ "/app/config" ]

USER appuser

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
