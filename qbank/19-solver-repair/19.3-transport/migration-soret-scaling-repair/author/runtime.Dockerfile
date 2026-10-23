FROM caeoj-sdk-dependencies:7aaa57e9b8c10109 AS sdk
FROM caeoj-chrono846-core:base
RUN sed -i 's|http://deb.debian.org|https://deb.debian.org|g' /etc/apt/sources.list.d/debian.sources && apt-get update && apt-get install -y --no-install-recommends gfortran libblas-dev liblapack-dev && rm -rf /var/lib/apt/lists/*
COPY source/ /opt/elmer-source/
RUN cmake -S /opt/elmer-source -B /opt/elmer-build -G Ninja -DCMAKE_BUILD_TYPE=Release -DCMAKE_Fortran_FLAGS_RELEASE='-O1 -DNDEBUG' -DWITH_MPI=FALSE -DWITH_ELMERGUI=FALSE -DWITH_ElmerIce=FALSE -DWITH_ELMERPOST=FALSE -DBUILD_TESTING=OFF '-DINCLUDE_ELMER_MODULES=AdvectionDiffusion;StatCurrentSolve;HeatSolve' -DCMAKE_INSTALL_PREFIX=/opt/elmer-install
RUN cmake --build /opt/elmer-build --target Solver_TGT ElmerGrid AdvectionDiffusion StatCurrentSolve HeatSolve -j2 && chmod -R go-w /opt/elmer-source /opt/elmer-build
COPY --from=sdk /usr/local/lib/python3.14/site-packages/ /usr/local/lib/python3.14/site-packages/
COPY --from=sdk /usr/local/lib/libgmsh.so.4.15 /usr/local/lib/libgmsh.so.4.15
COPY offline-wheels /opt/offline-wheels
ENV PIP_NO_INDEX=1 PIP_FIND_LINKS=/opt/offline-wheels
COPY driver/ /opt/elmer-driver/
RUN chmod -R go-w /opt/elmer-driver
ENV ELMER_HOME=/opt/elmer-source/fem/src ELMER_LIB=/opt/elmer-build/fem/src/modules
WORKDIR /app
