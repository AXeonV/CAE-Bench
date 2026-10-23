FROM python:3.14-slim@sha256:a2b82f3c48559aa0a8446d9af49826b6e2b2016f4cd2afabfe6013ec53729170
RUN apt-get update && apt-get install -y --no-install-recommends build-essential cmake libeigen3-dev libboost-filesystem-dev libboost-log-dev libboost-program-options-dev libboost-system-dev libboost-thread-dev libboost-test-dev libxml2-dev && rm -rf /var/lib/apt/lists/*
ADD source.tar.gz /opt/precice-upstream/
RUN cmake -S /opt/precice-upstream/precice-c2a06a65631e15a6622f5ecffae194f82ba0bae3 -B /opt/precice-build -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_FLAGS_RELEASE="-O1 -DNDEBUG" -DPRECICE_MPICommunication=OFF -DPRECICE_PETScMapping=OFF -DPRECICE_PythonActions=OFF -DPRECICE_Packages=OFF -DBUILD_TESTING=OFF -DPRECICE_ENABLE_C=OFF -DPRECICE_ENABLE_FORTRAN=OFF -DPRECICE_BUILD_TOOLS=OFF
RUN cmake --build /opt/precice-build --target precice --parallel 2
