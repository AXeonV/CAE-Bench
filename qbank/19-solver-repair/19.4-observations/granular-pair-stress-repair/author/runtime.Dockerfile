FROM caeoj-cantera1872-core:offline-sdk
COPY lammps-source.tar.gz /tmp/lammps-source.tar.gz
RUN mkdir -p /opt/lammps-source && tar -xzf /tmp/lammps-source.tar.gz -C /opt/lammps-source --strip-components=1 && cmake -S /opt/lammps-source/cmake -B /opt/lammps-build -DCMAKE_BUILD_TYPE=Release -DBUILD_MPI=OFF -DBUILD_SHARED_LIBS=ON -DPKG_GRANULAR=ON -DPKG_KOKKOS=ON -DKokkos_ENABLE_SERIAL=ON -DKokkos_ENABLE_OPENMP=OFF -DCMAKE_CXX_STANDARD=17 && cmake --build /opt/lammps-build --target lammps lmp --parallel 4 && chown -R root:root /opt/lammps-source /opt/lammps-build && chmod -R go-w /opt/lammps-source /opt/lammps-build
ENV LD_LIBRARY_PATH=/opt/lammps-build
