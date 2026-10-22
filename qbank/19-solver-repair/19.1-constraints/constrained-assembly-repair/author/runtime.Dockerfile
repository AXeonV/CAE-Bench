FROM --platform=linux/amd64 python:3.14-slim
RUN sed -i 's|http://deb.debian.org|https://deb.debian.org|g' /etc/apt/sources.list.d/debian.sources \
    && apt-get update && apt-get install -y --no-install-recommends \
    bash git curl ca-certificates g++ cmake ninja-build libeigen3-dev util-linux \
    libglu1-mesa libgl1 libgomp1 \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --uid 1000 --create-home solver
COPY source/ /opt/chrono-source/
RUN cmake -S /opt/chrono-source -B /opt/chrono-build -G Ninja \
      -DCMAKE_BUILD_TYPE=Release -DBUILD_DEMOS=OFF -DBUILD_TESTING=OFF \
      -DCH_ENABLE_MODULE_FEA=OFF -DCH_ENABLE_OPENMP=OFF \
    && cmake --build /opt/chrono-build --target Chrono_core -j4
RUN cmake --build /opt/chrono-build --target ChronoModels_robot -j4
COPY driver/ /opt/assembly-driver/
RUN cmake -S /opt/assembly-driver -B /opt/driver-build -G Ninja \
      -DChrono_DIR=/opt/chrono-build/cmake -DCMAKE_BUILD_TYPE=Release \
    && cmake --build /opt/driver-build -j4
RUN apt-get update && apt-get install -y --no-install-recommends \
      libxrender1 libxcursor1 libxfixes3 libxft2 libfontconfig1 libxinerama1 \
    && rm -rf /var/lib/apt/lists/*
ENV LD_LIBRARY_PATH=/opt/chrono-build/lib
WORKDIR /app
