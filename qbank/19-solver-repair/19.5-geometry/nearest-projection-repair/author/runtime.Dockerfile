FROM caeoj-precice1304-prototype:base
RUN apt-get update && apt-get install -y --no-install-recommends util-linux libglu1-mesa libgl1 libxrender1 libxcursor1 libxfixes3 libxft2 libfontconfig1 libxinerama1 && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir numpy==2.4.6 h5py==3.16.0 gmsh==4.15.2 jsonschema==4.26.0 typing-extensions==4.16.0
RUN pip download --dest /opt/sdk-build-wheels setuptools==80.9.0 wheel==0.48.0
COPY driver.cpp /opt/precice-driver/driver.cpp
COPY CMakeLists.txt /opt/precice-repair-cmake/CMakeLists.txt
RUN cmake -S /opt/precice-repair-cmake -B /opt/precice-repair-build && cmake --build /opt/precice-repair-build --target repair_sources --parallel 2 && useradd -m -u 1000 solver && chown -R root:root /opt/precice-driver /opt/precice-repair-cmake /opt/precice-repair-build && chmod -R go-w /opt/precice-driver /opt/precice-repair-cmake /opt/precice-repair-build
ENV LD_LIBRARY_PATH=/opt/precice-repair-build/lib

ENV PIP_FIND_LINKS=/opt/sdk-build-wheels PIP_NO_INDEX=1
