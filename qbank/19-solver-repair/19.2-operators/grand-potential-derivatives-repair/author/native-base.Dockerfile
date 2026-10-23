FROM idaholab/moose-dev@sha256:78d1470a041e789f0ecbfba507a890e03766c8983b09176da4f9eadaf4419149
SHELL ["/bin/bash", "-lc"]
COPY baseline-source /opt/moose-source
RUN source /environment && make -C /opt/moose-source/modules/phase_field -j2 METHOD=opt ENABLE_LIBTORCH=false
ENTRYPOINT ["/bin/bash", "-lc"]
