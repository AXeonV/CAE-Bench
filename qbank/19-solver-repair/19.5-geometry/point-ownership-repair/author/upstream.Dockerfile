FROM python:3.14.8-slim@sha256:a2b82f3c48559aa0a8446d9af49826b6e2b2016f4cd2afabfe6013ec53729170
RUN apt-get update && apt-get install -y --no-install-recommends g++ cmake ninja-build libopenmpi-dev openmpi-bin libhdf5-openmpi-dev libboost-dev libpugixml-dev libspdlog-dev libopenblas-dev libscotch-dev libptscotch-dev && rm -rf /var/lib/apt/lists/*
COPY baseline.tar.gz basix.tar.gz ffcx.tar.gz /tmp/
RUN mkdir -p /opt/upstream && tar -xzf /tmp/baseline.tar.gz -C /opt/upstream && tar -xzf /tmp/basix.tar.gz -C /opt/upstream && tar -xzf /tmp/ffcx.tar.gz -C /opt/upstream
RUN cmake -S /opt/upstream/basix-0005e60fe56c8ff6e7436dc6c7ddba677e408b43/cpp -B /opt/basix-build -G Ninja -DCMAKE_BUILD_TYPE=Release && cmake --build /opt/basix-build --parallel 2 && cmake --install /opt/basix-build
RUN cmake -S /opt/upstream/ffcx-76744fe1e6de4aad30f8d3db3dd5f57562472924/cmake -B /opt/ufcx-build -G Ninja && cmake --install /opt/ufcx-build
COPY SCOTCHConfig.cmake SCOTCHConfigVersion.cmake /opt/scotch-cmake/
RUN test "$(dpkg-query -W -f='${Version}' libscotch-dev)" = 7.0.7-1
RUN cmake -S /opt/upstream/dolfinx-2d6d22a8c2cc9d3488f8910238e9740c6247f83b/cpp -B /opt/dolfinx-build -G Ninja -DCMAKE_BUILD_TYPE=Release -DDOLFINX_ENABLE_PETSC:BOOL=OFF -DDOLFINX_ENABLE_SLEPC:BOOL=OFF -DDOLFINX_ENABLE_ADIOS2:BOOL=OFF -DDOLFINX_ENABLE_SCOTCH:BOOL=ON -DSCOTCH_DIR=/opt/scotch-cmake -DDOLFINX_UFCX_PYTHON=OFF -DDOLFINX_BASIX_PYTHON=OFF && cmake --build /opt/dolfinx-build --parallel 2 && cmake --install /opt/dolfinx-build && ldconfig
RUN useradd -m -u 1000 solver
