FROM caeoj-sdk-dependencies:7aaa57e9b8c10109 AS sdk
FROM caeoj-chrono846-core:base
ARG HTTP_PROXY
RUN apt-get update && apt-get install -y --no-install-recommends scons python3-packaging libboost-dev libfmt-dev libyaml-cpp-dev libsundials-dev libgtest-dev libgmock-dev make && rm -rf /var/lib/apt/lists/*
COPY cantera-source.tar.gz /tmp/cantera-source.tar.gz
RUN mkdir -p /opt/cantera-source && tar -xzf /tmp/cantera-source.tar.gz -C /opt/cantera-source --strip-components=1
WORKDIR /opt/cantera-source
RUN scons build -j4 env_vars=all python_package=n f90_interface=n debug=n optimize=y system_eigen=y system_fmt=y system_yamlcpp=y system_sundials=y CXX=mpicxx CC=mpicc example_data=n hdf_support=n
COPY driver.cpp plasma.yaml /opt/repair-driver/
COPY CMakeLists.txt /opt/repair-cmake/CMakeLists.txt
RUN cmake -S /opt/repair-cmake -B /opt/cantera-source/build -DCMAKE_CXX_COMPILER=/usr/bin/mpicxx && cmake --build /opt/cantera-source/build --target repair_sources
COPY --from=sdk /usr/local/lib/python3.14/site-packages/ /usr/local/lib/python3.14/site-packages/
COPY --from=sdk /usr/local/lib/libgmsh.so.4.15 /usr/local/lib/libgmsh.so.4.15
COPY wheels /opt/offline-wheels
ENV PIP_NO_INDEX=1 PIP_FIND_LINKS=/opt/offline-wheels LD_LIBRARY_PATH=/opt/cantera-source/build/lib
RUN chown -R root:root /opt/cantera-source /opt/repair-driver /opt/repair-cmake && chmod -R go-w /opt/cantera-source /opt/repair-driver /opt/repair-cmake
WORKDIR /app
