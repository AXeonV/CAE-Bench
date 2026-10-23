cmake_minimum_required(VERSION 3.16)
project(su2_reconstruction_repair LANGUAGES CXX)
find_program(SU2_NINJA ninja REQUIRED)
add_custom_target(repair_sources ALL
  COMMAND ${SU2_NINJA} -C /opt/su2-build SU2_CFD/src/SU2_CFD -j4
  COMMAND ${CMAKE_COMMAND} -E make_directory /opt/su2-build/bin
  COMMAND ${CMAKE_CXX_COMPILER} -std=c++17 -O3 -DNDEBUG
    -I/opt/su2-source -I/opt/su2-source/externals/mel
    -I/opt/su2-build/Common/src -I/opt/su2-source/Common/src
    /opt/repair-driver/reconstruction-driver.cpp
    -Wl,--start-group /opt/su2-build/SU2_CFD/src/libSU2core.a
    /opt/su2-build/Common/src/libSU2Common.a -Wl,--end-group
    -o /opt/su2-build/bin/reconstruction-driver
  VERBATIM)
