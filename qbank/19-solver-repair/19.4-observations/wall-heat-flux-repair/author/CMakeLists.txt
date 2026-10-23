cmake_minimum_required(VERSION 3.16)
project(su2_wall_energy_repair LANGUAGES CXX)
find_program(SU2_NINJA ninja REQUIRED)
add_custom_target(repair_sources ALL
  COMMAND ${SU2_NINJA} -C /opt/su2-build SU2_CFD/src/SU2_CFD -j4
  VERBATIM)
