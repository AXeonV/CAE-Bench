FROM --platform=linux/amd64 caeoj-bempp20-runtime:base
WORKDIR /app
COPY agent.zip /tmp/agent.zip
COPY requirements.txt /tmp/requirements.txt
RUN python -m zipfile -e /tmp/agent.zip /app \
    && python -m pip install --no-cache-dir /app -r /tmp/requirements.txt \
    && mkdir -p /app/submission
