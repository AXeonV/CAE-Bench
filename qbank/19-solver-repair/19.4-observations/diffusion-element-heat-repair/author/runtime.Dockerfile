FROM caeoj-python314-pinned:repair22
ENV DEBIAN_FRONTEND=noninteractive PYBAMM_DISABLE_TELEMETRY=true PYTHONUNBUFFERED=1
RUN apt-get update && apt-get install -y --no-install-recommends cmake ninja-build g++ libgomp1 util-linux libgl1 libglu1-mesa libxrender1 libxcursor1 libxfixes3 libxft2 libfontconfig1 libxinerama1 && rm -rf /var/lib/apt/lists/*
COPY source /opt/pybamm-build/source
RUN SETUPTOOLS_SCM_PRETEND_VERSION=0.0.0 pip install --no-cache-dir -e /opt/pybamm-build/source/packages/pybamm
COPY CMakeLists.txt /opt/repair-cmake/CMakeLists.txt
COPY driver.py /opt/repair-driver/driver.py
RUN cmake -S /opt/repair-cmake -B /opt/pybamm-build -G Ninja && cmake --build /opt/pybamm-build --target repair_sources && useradd -m -u 1000 solver && chown -R 1000:1000 /opt/pybamm-build
RUN PYBAMM_DISABLE_TELEMETRY=true python -c "import pybamm; print(pybamm.__version__)"
