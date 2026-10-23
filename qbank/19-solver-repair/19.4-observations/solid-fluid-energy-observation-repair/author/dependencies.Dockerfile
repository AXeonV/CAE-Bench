FROM idaholab/moose-dev@sha256:78d1470a041e789f0ecbfba507a890e03766c8983b09176da4f9eadaf4419149
SHELL ["/bin/bash", "-lc"]
COPY *.tar.gz /tmp/dependency-archives/
RUN mkdir -p /opt/petsc2022-src /opt/libmesh2022-src && \
    tar -xzf /tmp/dependency-archives/petsc.tar.gz --strip-components=1 -C /opt/petsc2022-src && \
    tar -xzf /tmp/dependency-archives/libmesh.tar.gz --strip-components=1 -C /opt/libmesh2022-src && \
    tar -xzf /tmp/dependency-archives/metaphysicl.tar.gz --strip-components=1 -C /opt/libmesh2022-src/contrib/metaphysicl && \
    tar -xzf /tmp/dependency-archives/timpi.tar.gz --strip-components=1 -C /opt/libmesh2022-src/contrib/timpi && \
    tar -xzf /tmp/dependency-archives/autoconf.tar.gz --strip-components=1 -C /opt/libmesh2022-src/m4/autoconf-submodule && \
    tar -xzf /tmp/dependency-archives/autoconf_meta.tar.gz --strip-components=1 -C /opt/libmesh2022-src/contrib/metaphysicl/m4/autoconf-submodule && \
    tar -xzf /tmp/dependency-archives/autoconf_timpi.tar.gz --strip-components=1 -C /opt/libmesh2022-src/contrib/timpi/m4/autoconf-submodule && \
    tar -xzf /tmp/dependency-archives/eigen.tar.gz --strip-components=1 -C /opt/libmesh2022-src/contrib/eigen/git && \
    tar -xzf /tmp/dependency-archives/poly2tri.tar.gz --strip-components=1 -C /opt/libmesh2022-src/contrib/poly2tri/poly2tri
RUN source /environment && export PETSC_DIR=/opt/petsc2022-src PETSC_ARCH=arch-moose2022 && \
    cd /opt/petsc2022-src && /usr/bin/python3.9 ./configure --prefix=/opt/petsc2022 \
      --with-debugging=0 --with-shared-libraries=1 --with-64-bit-indices=1 \
      --with-mpi-dir=/opt/openmpi --with-blaslapack-lib='[/opt/petsc/lib/libflapack.a,/opt/petsc/lib/libfblas.a]' \
      --with-fortran-bindings=0 --with-make-np=2 --with-cxx-dialect=C++14 && \
    make -j2 all && make install
RUN source /environment && export PETSC_DIR=/opt/petsc2022 && unset PETSC_ARCH SLEPC_DIR && \
    mkdir -p /opt/libmesh2022-src/build && cd /opt/libmesh2022-src/build && \
    ../configure --prefix=/opt/libmesh2022 --with-methods=opt --enable-silent-rules \
      --enable-unique-id --with-dof-id-bytes=8 --disable-warnings --with-thread-model=openmp \
      --disable-maintainer-mode --enable-metaphysicl-required --enable-xdr-required \
      --with-cxx-std-min=2014 --without-gdb-command --with-future-timpi-dir=/opt/libmesh2022 \
      --disable-slepc --disable-vtk --disable-hdf5 && \
    make -j2 && make install
