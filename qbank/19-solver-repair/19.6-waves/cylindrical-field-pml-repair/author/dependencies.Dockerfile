FROM python:3.14-slim@sha256:a2b82f3c48559aa0a8446d9af49826b6e2b2016f4cd2afabfe6013ec53729170 AS deps
RUN apt-get update && apt-get install -y --no-install-recommends build-essential cmake autoconf automake libtool pkg-config libhdf5-dev libfftw3-dev libgsl-dev libharminv-dev libctl-dev liblapack-dev && rm -rf /var/lib/apt/lists/*
RUN apt-get update && apt-get install -y --no-install-recommends gfortran && rm -rf /var/lib/apt/lists/*
