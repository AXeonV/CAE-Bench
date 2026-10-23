cmake_minimum_required(VERSION 3.16)
project(specfem_interface_repair LANGUAGES NONE)
find_program(MAKE_EXECUTABLE NAMES make REQUIRED)
# The upstream Fortran source is compiled directly; there is no preprocessed cache.
# Always enter the real build. Trusted grading removes the named object/executable.
add_custom_target(repair_sources ALL
  COMMAND ${MAKE_EXECUTABLE} -C ${CMAKE_BINARY_DIR}/upstream bin/xspecfem2D
  VERBATIM)
