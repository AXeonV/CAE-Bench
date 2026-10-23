FROM caeoj-bempp20-runtime:base
COPY tests/agent.zip /tmp/agent.zip
RUN python -m zipfile -e /tmp/agent.zip /app && python -m pip install --no-cache-dir /app && mkdir -p /app/submission
COPY tests /tests
COPY exafmm.py fmm_assembler.py helpers.py /probe/
COPY backend_probe.py /opt/backend_probe.py
