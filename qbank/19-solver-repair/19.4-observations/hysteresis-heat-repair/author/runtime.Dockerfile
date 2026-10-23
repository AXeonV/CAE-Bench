FROM python:3.11-slim@sha256:b7a9e5f6a93d6d4a31f129bbd4bdee69efccb6ded0fb230d78aafaf37af98377
ENV DEBIAN_FRONTEND=noninteractive PYBAMM_DISABLE_TELEMETRY=true PYTHONUNBUFFERED=1
RUN apt-get update && apt-get install -y --no-install-recommends cmake ninja-build g++ libgomp1 util-linux libgl1 libglu1-mesa libxrender1 libxcursor1 libxfixes3 libxft2 libfontconfig1 libxinerama1 && rm -rf /var/lib/apt/lists/*
COPY source /opt/pybamm-build/source
RUN python -m venv /opt/solver-venv && SETUPTOOLS_SCM_PRETEND_VERSION=0.0.0 /opt/solver-venv/bin/pip install --no-cache-dir -e /opt/pybamm-build/source 'posthog<6'
RUN pip install --no-cache-dir 'numpy>=2,<3' h5py jsonschema==4.26.0 attrs setuptools wheel gmsh==4.15.2 && pip download --only-binary=:all: --dest /opt/offline-wheels setuptools wheel packaging
ENV PIP_NO_INDEX=1 PIP_FIND_LINKS=/opt/offline-wheels
COPY CMakeLists.txt /opt/repair-cmake/CMakeLists.txt
COPY driver.py /opt/repair-driver/driver.py
RUN cmake -S /opt/repair-cmake -B /opt/pybamm-build -G Ninja && cmake --build /opt/pybamm-build --target repair_sources && useradd -m -u 1000 solver && chown -R 1000:1000 /opt/pybamm-build
RUN /opt/solver-venv/bin/python -c "import pybamm,numpy; assert numpy.__version__.startswith('1.'); assert pybamm.__file__.startswith('/opt/pybamm-build/source/')" && python -c "import numpy,gmsh; assert numpy.__version__.startswith('2.'); assert hasattr(gmsh.lib,'gmshInitialize')"
