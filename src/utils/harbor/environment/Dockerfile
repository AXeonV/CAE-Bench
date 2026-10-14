FROM python:3.14-slim
RUN sed -i 's|http://deb.debian.org|https://deb.debian.org|g' /etc/apt/sources.list.d/debian.sources \
    && apt-get update && apt-get install -y --no-install-recommends \
    bash git curl ca-certificates g++ openmpi-bin libopenmpi-dev libhdf5-dev hdf5-tools libglu1-mesa libgl1 util-linux \
    libxrender1 libxcursor1 libxfixes3 libxft2 libfontconfig1 libxinerama1 libgomp1 \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --uid 1000 --create-home solver
WORKDIR /app
COPY agent.zip /tmp/agent.zip
COPY requirements.txt /tmp/requirements.txt
RUN python -m zipfile -e /tmp/agent.zip /app \
    && python -m pip install --no-cache-dir /app -r /tmp/requirements.txt \
    && mkdir -p /app/submission
