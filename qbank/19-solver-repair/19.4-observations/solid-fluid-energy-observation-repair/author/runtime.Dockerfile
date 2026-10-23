FROM caeoj-moose22074-prototype:pinned2022
SHELL ["/bin/bash", "-c"]
COPY --from=caeoj-moose30236-runtime:base /opt/task-python /opt/task-python
COPY --from=caeoj-moose30236-runtime:base /opt/task-wheels /opt/task-wheels
COPY rpms/ /tmp/task-rpms/
RUN dnf --disablerepo='*' install -y /tmp/task-rpms/*.rpm && rm -rf /tmp/task-rpms
ENV PATH=/opt/task-python/bin:$PATH PIP_NO_INDEX=1 PIP_FIND_LINKS=/opt/task-wheels
RUN rm -f /usr/local/bin/python && printf '#!/bin/sh\nexec /opt/task-python/bin/python "$@"\n' > /usr/local/bin/python && chmod 755 /usr/local/bin/python && mkdir -p /home/solver && chown 1000:1000 /home/solver
COPY driver/CMakeLists.txt /opt/build-control/CMakeLists.txt
RUN /usr/bin/cmake -G "Unix Makefiles" -S /opt/build-control -B /opt/moose-source-2022 && find /opt/moose-source-2022 /opt/build-control /opt/task-python /opt/task-wheels -perm /022 -exec chmod go-w {} +
WORKDIR /app
ENTRYPOINT []
CMD ["bash"]
