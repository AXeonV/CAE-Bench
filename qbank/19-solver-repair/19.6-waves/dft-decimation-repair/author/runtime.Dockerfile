FROM caeoj-sdk-dependencies:7aaa57e9b8c10109 AS sdk
FROM caeoj-meep-deps:repair22
ADD source.tar.gz /opt/meep-upstream/
WORKDIR /opt/meep-upstream/meep-ccb3c372dc34ca75ce01f99c2b50e0e89ad0a203
RUN autoreconf --install --force && mkdir -p /opt/meep-repair-build/upstream && cd /opt/meep-repair-build/upstream && /opt/meep-upstream/meep-ccb3c372dc34ca75ce01f99c2b50e0e89ad0a203/configure --without-mpi --without-scheme --without-python --without-libctl --prefix=/opt/meep-install CXXFLAGS="-O1 -DNDEBUG" CPPFLAGS="-I/usr/include/hdf5/serial" LDFLAGS="-L/usr/lib/x86_64-linux-gnu/hdf5/serial" && make -C src -j2
COPY driver.cpp /opt/meep-driver/driver.cpp
COPY CMakeLists.txt /opt/meep-repair-cmake/CMakeLists.txt
RUN cmake -S /opt/meep-repair-cmake -B /opt/meep-repair-build && cmake --build /opt/meep-repair-build --target repair_sources --parallel 2
COPY --from=sdk /usr/local/lib/python3.14/site-packages/ /usr/local/lib/python3.14/site-packages/
COPY --from=sdk /usr/local/lib/libgmsh.so.4.15 /usr/local/lib/libgmsh.so.4.15
RUN apt-get update && apt-get install -y --no-install-recommends util-linux libglu1-mesa libgl1 libxrender1 libxcursor1 libxfixes3 libxft2 libfontconfig1 libxinerama1 && rm -rf /var/lib/apt/lists/*
COPY offline-wheels /opt/offline-wheels
ENV PIP_NO_INDEX=1 PIP_FIND_LINKS=/opt/offline-wheels
RUN useradd -m -u 1000 solver && chmod -R go-w /opt/meep-upstream /opt/meep-driver /opt/meep-repair-cmake /opt/meep-repair-build
WORKDIR /app
