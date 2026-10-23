FROM caeoj-su22347-core:base
COPY CMakeLists.txt /opt/repair-driver/
RUN cmake -S /opt/repair-driver -B /opt/su2-build -G "Unix Makefiles" && cmake --build /opt/su2-build --target repair_sources --parallel 4 && chown -R root:root /opt/su2-source /opt/su2-build /opt/repair-driver && chmod -R go-w /opt/su2-source /opt/su2-build /opt/repair-driver
