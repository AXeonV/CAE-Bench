FROM caeoj-bempp20-deps:prototype
COPY bempp.tar.gz exafmm.tar.gz /tmp/
RUN mkdir -p /opt/upstream && tar -xzf /tmp/exafmm.tar.gz -C /opt/upstream && tar -xzf /tmp/bempp.tar.gz -C /opt/upstream
RUN PIP_NO_INDEX=1 /opt/bempp-env/bin/python -m pip install --no-deps --no-build-isolation /opt/upstream/exafmm-t-0.1.0 && PIP_NO_INDEX=1 /opt/bempp-env/bin/python -m pip install --no-deps --no-build-isolation -e /opt/upstream/bempp-cl-84345ee9ee314c85750f045c7ad38090f5ea5f26
COPY CMakeLists.txt /opt/bempp-repair-cmake/CMakeLists.txt
COPY driver.py /opt/repair-driver/driver.py
RUN /opt/bempp-env/bin/python -m compileall -q -f --invalidation-mode checked-hash /opt/upstream/bempp-cl-84345ee9ee314c85750f045c7ad38090f5ea5f26/bempp && cmake -S /opt/bempp-repair-cmake -B /opt/bempp-repair-build -G Ninja && cmake --build /opt/bempp-repair-build --target repair_sources
RUN useradd -m -u 1000 solver && chown -R 1000:1000 /opt/upstream/bempp-cl-84345ee9ee314c85750f045c7ad38090f5ea5f26 /opt/bempp-repair-build
RUN apt-get update && apt-get install -y --no-install-recommends util-linux libgl1 libxcursor1 libxfixes3 libxft2 libfontconfig1 libxinerama1 && rm -rf /var/lib/apt/lists/*
COPY offline-wheels /opt/offline-wheels
RUN python -m pip install --no-index --find-links=/opt/offline-wheels numpy==2.4.6 h5py==3.16.0 jsonschema==4.26.0 gmsh==4.15.2 setuptools==68.2.2 wheel==0.41.3 && python -c "import numpy,h5py,gmsh; gmsh.initialize(); gmsh.finalize(); print(numpy.__version__,h5py.__version__)"
ENV PIP_NO_INDEX=1 PIP_FIND_LINKS=/opt/offline-wheels
ENV OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=1 NUMBA_NUM_THREADS=4 POCL_MAX_PTHREAD_COUNT=4 NUMBA_CACHE_DIR=/tmp/numba POCL_CACHE_DIR=/tmp/pocl
WORKDIR /tmp
