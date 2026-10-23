FROM caeoj-cantera1872-core:offline-sdk
COPY driver.cpp mechanism.yaml /opt/cantera1655-driver/
COPY CMakeLists.txt /opt/cantera1655-cmake/CMakeLists.txt
RUN cmake -S /opt/cantera1655-cmake -B /opt/cantera1655-build -DCMAKE_CXX_COMPILER=/usr/bin/mpicxx && cmake --build /opt/cantera1655-build --target repair_sources && chown -R root:root /opt/cantera1655-driver /opt/cantera1655-cmake /opt/cantera1655-build && chmod -R go-w /opt/cantera1655-driver /opt/cantera1655-cmake /opt/cantera1655-build
ENV LD_LIBRARY_PATH=/opt/cantera1655-build/lib
