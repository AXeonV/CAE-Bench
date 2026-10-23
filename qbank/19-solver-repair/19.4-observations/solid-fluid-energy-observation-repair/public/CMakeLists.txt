cmake_minimum_required(VERSION 3.16)
project(SolidFluidObservationRepair NONE)
add_custom_target(energy_observation_repair
 COMMAND /bin/bash -lc "source /environment && export PETSC_DIR=/opt/petsc2022 LIBMESH_DIR=/opt/libmesh2022 LD_LIBRARY_PATH=/opt/libmesh2022/lib:/opt/petsc2022/lib:$LD_LIBRARY_PATH && unset PETSC_ARCH SLEPC_DIR && exec make -C /opt/moose-source-2022/modules/navier_stokes -j2 METHOD=opt pyconfig=/usr/bin/python3.9-config"
 USES_TERMINAL VERBATIM)
