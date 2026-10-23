cmake_minimum_required(VERSION 3.16)
project(GrandPotentialRepair NONE)
add_custom_target(phasefield_repair
  COMMAND /bin/bash -lc "source /environment && exec make -C /opt/moose-source/modules/phase_field -j2 METHOD=opt ENABLE_LIBTORCH=false"
  USES_TERMINAL
  VERBATIM)
