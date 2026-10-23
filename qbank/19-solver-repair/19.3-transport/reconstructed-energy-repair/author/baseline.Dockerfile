FROM caeoj-cantera1872-core:offline-sdk
COPY wheels /tmp/su2-wheels
RUN python -m pip install --no-index --find-links /tmp/su2-wheels meson==1.8.3
COPY base.tar.gz mel.tar.gz /tmp/
RUN mkdir -p /opt/su2-source /opt/su2-source/externals/mel && tar -xzf /tmp/base.tar.gz -C /opt/su2-source --strip-components=1 && tar -xzf /tmp/mel.tar.gz -C /opt/su2-source/externals/mel --strip-components=1
WORKDIR /opt/su2-source
RUN python preconfigure.py --no-codi --no-medi --no-opdi --no-mpp --no-coolprop --no-mel --no-mlpcpp --no-fado && meson setup /opt/su2-build /opt/su2-source -Dcpp_args=-I/opt/su2-source/SU2_CFD/src/interfaces -Dwith-mpi=disabled -Dwith-omp=false -Denable-cgns=false -Denable-tecio=false -Denable-autodiff=false -Denable-directdiff=false && ninja -C /opt/su2-build SU2_CFD/src/SU2_CFD -j4
ENV LD_LIBRARY_PATH=/opt/su2-build
WORKDIR /app
