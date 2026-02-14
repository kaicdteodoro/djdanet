FROM python:3.12-slim AS base

RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

FROM base AS dependencies

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM dependencies AS runtime

COPY app/ ./app/

RUN groupadd -g 1000 djdanet && \
    useradd -u 1000 -g djdanet -m djdanet && \
    mkdir -p /app/downloads && \
    chown -R djdanet:djdanet /app

USER djdanet

ENTRYPOINT ["python", "-m", "app.cli.main"]
