FROM caeoj-cantera1872-core:offline-sdk
COPY driver.cpp mechanism.yaml /opt/cantera1996-driver/
COPY CMakeLists.txt /opt/cantera1996-cmake/CMakeLists.txt
RUN cmake -S /opt/cantera1996-cmake -B /opt/cantera1996-build -DCMAKE_CXX_COMPILER=/usr/bin/mpicxx && cmake --build /opt/cantera1996-build --target repair_sources && chown -R root:root /opt/cantera1996-driver /opt/cantera1996-cmake /opt/cantera1996-build && chmod -R go-w /opt/cantera1996-driver /opt/cantera1996-cmake /opt/cantera1996-build
ENV LD_LIBRARY_PATH=/opt/cantera1996-build/lib
