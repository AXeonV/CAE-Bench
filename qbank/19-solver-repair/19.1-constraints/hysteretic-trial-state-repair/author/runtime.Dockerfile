FROM caeoj-sdk-dependencies:7aaa57e9b8c10109 AS sdk
FROM caeoj-chrono846-core:base
COPY --from=sdk /usr/local/lib/python3.14/site-packages/ /usr/local/lib/python3.14/site-packages/
COPY --from=sdk /usr/local/lib/libgmsh.so.4.15 /usr/local/lib/libgmsh.so.4.15
COPY offline-wheels /opt/offline-wheels
ENV PIP_NO_INDEX=1 PIP_FIND_LINKS=/opt/offline-wheels
COPY source/ /opt/opensees-source/
COPY driver/ /opt/material-driver/
RUN cmake -S /opt/material-driver -B /opt/material-build -G Ninja && cmake --build /opt/material-build -j4
RUN chmod -R go-w /opt/opensees-source /opt/material-driver /opt/material-build
WORKDIR /app
