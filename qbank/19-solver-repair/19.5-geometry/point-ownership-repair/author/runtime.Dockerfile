FROM caeoj-dolfinx4450-wrapper:base
RUN apt-get update && apt-get install -y --no-install-recommends util-linux libglu1-mesa libgl1 libxrender1 libxcursor1 libxfixes3 libxft2 libfontconfig1 libxinerama1 && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir numpy==2.4.6 h5py==3.16.0 gmsh==4.15.2 jsonschema==4.26.0 typing-extensions==4.16.0
RUN pip download --dest /opt/sdk-build-wheels setuptools==80.9.0 wheel==0.48.0
RUN chown -R root:root /opt/upstream /opt/ownership-driver /opt/ownership-repair-cmake /opt/dolfinx-repair-build /opt/scotch-cmake && chmod -R go-w /opt/upstream /opt/ownership-driver /opt/ownership-repair-cmake /opt/dolfinx-repair-build /opt/scotch-cmake
ENV LD_LIBRARY_PATH=/opt/dolfinx-repair-build/lib
ENV PIP_FIND_LINKS=/opt/sdk-build-wheels PIP_NO_INDEX=1
