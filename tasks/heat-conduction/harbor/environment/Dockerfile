FROM python:3.14-slim
RUN apt-get update && apt-get install -y --no-install-recommends \
    bash git curl ca-certificates libglu1-mesa libgl1 util-linux \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --uid 1000 --create-home solver
WORKDIR /app
COPY agent.zip /tmp/agent.zip
RUN python -m zipfile -e /tmp/agent.zip /app \
    && python -m pip install --no-cache-dir /app scipy==1.18.1 \
    && mkdir -p /app/submission
