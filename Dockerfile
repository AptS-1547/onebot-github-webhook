FROM python:3.12.9-alpine3.21

ARG VERSION=1.0.0

LABEL maintainer="AptS-1547 <apts-1547@esaps.net>"
LABEL version="${VERSION}"
LABEL description="A simple webhook server for GitHub to send events to a OneBot (CQHTTP) bot."
LABEL homepage="https://onebot-github-webhook.docs.ecaps.top/"
LABEL repository="https://github.com/AptS-1547/onebot-github-webhook"
LABEL license="Apache-2.0"

LABEL org.opencontainers.image.source="https://github.com/AptS-1547/onebot-github-webhook"
LABEL org.opencontainers.image.description="A simple webhook server for GitHub to send events to a OneBot (CQHTTP) bot."
LABEL org.opencontainers.image.licenses="Apache-2.0"

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN mkdir -p /app/templates \
    && adduser --disabled-password --gecos "" appuser \
    && chown -R appuser:appuser /app

COPY --chown=appuser:appuser . .

VOLUME [ "/app/templates" ]

USER appuser

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
