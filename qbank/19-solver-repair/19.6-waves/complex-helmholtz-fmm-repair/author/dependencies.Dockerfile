FROM python:3.11-slim-bookworm
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends g++ cmake ninja-build libfftw3-dev libopenblas-dev libgomp1 pocl-opencl-icd ocl-icd-opencl-dev libglu1-mesa libxrender1 libxext6 && rm -rf /var/lib/apt/lists/*
RUN python -m venv /opt/bempp-env && /opt/bempp-env/bin/python -m pip install --no-cache-dir setuptools==68.2.2 wheel==0.41.3 numpy==1.23.5 scipy==1.10.1 numba==0.57.1 llvmlite==0.40.1 pyopencl==2024.3 meshio==5.3.5 pybind11==2.12.0
ENV OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=1
