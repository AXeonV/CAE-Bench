FROM caeoj-dolfinx4450-prototype:base
COPY driver.cpp /opt/ownership-driver/driver.cpp
COPY CMakeLists.txt /opt/ownership-repair-cmake/CMakeLists.txt
RUN cmake -S /opt/ownership-repair-cmake -B /opt/dolfinx-repair-build -G Ninja -DCMAKE_BUILD_TYPE=Release && cmake --build /opt/dolfinx-repair-build --target repair_sources --parallel 2
