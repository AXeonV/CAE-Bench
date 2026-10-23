FROM caeoj-moose30236-prototype:base
SHELL ["/bin/bash", "-lc"]
COPY driver/RepairDerivativeAverage.C /opt/moose-source/modules/phase_field/src/postprocessors/RepairDerivativeAverage.C
COPY driver/RepairDofMap.C /opt/moose-source/modules/phase_field/src/vectorpostprocessors/RepairDofMap.C
RUN source /environment && make -C /opt/moose-source/modules/phase_field -j2 METHOD=opt ENABLE_LIBTORCH=false
COPY rpms/ /tmp/task-rpms/
RUN dnf --disablerepo='*' install -y /tmp/task-rpms/*.rpm && rm -rf /tmp/task-rpms
COPY wheels/ /opt/task-wheels/
RUN /usr/bin/python3.11 -m venv /opt/task-python && /opt/task-python/bin/python -m pip install --no-index --find-links=/opt/task-wheels numpy==2.4.6 h5py==3.16.0 gmsh==4.15.2 jsonschema==4.26.0 setuptools==80.9.0 wheel==0.45.1
ENV PATH=/opt/task-python/bin:$PATH PIP_NO_INDEX=1 PIP_FIND_LINKS=/opt/task-wheels
RUN rm -f /usr/local/bin/python && printf '#!/bin/sh\nexec /opt/task-python/bin/python "$@"\n' > /usr/local/bin/python && chmod 755 /usr/local/bin/python && mkdir -p /home/solver && chown 1000:1000 /home/solver
COPY driver/CMakeLists.txt /opt/build-control/CMakeLists.txt
RUN /usr/bin/cmake -G "Unix Makefiles" -S /opt/build-control -B /opt/moose-source && find /opt/moose-source /opt/build-control /opt/task-python /opt/task-wheels -perm /022 -exec chmod go-w {} +
WORKDIR /app
SHELL ["/bin/bash", "-c"]
ENTRYPOINT []
CMD ["bash"]
