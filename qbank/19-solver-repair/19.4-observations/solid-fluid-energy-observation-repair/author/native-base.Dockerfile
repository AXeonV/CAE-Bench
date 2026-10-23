FROM caeoj-moose22074-dependencies:pinned2022
SHELL ["/bin/bash", "-lc"]
COPY baseline-source /opt/moose-source-2022
RUN source /environment && export PETSC_DIR=/opt/petsc2022 LIBMESH_DIR=/opt/libmesh2022 && \
    unset PETSC_ARCH SLEPC_DIR && cd /opt/moose-source-2022/modules/navier_stokes && \
    make -j2 METHOD=opt pyconfig=/usr/bin/python3.9-config
ENTRYPOINT ["/bin/bash", "-lc"]
