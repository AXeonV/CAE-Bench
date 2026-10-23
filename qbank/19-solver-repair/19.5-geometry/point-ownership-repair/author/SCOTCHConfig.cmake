# Debian 7.0.7 packages contain the real libraries and headers but omit the
# upstream CMake export. This file only maps those installed dependencies.
set(SCOTCH_VERSION 7.0.7)
set(SCOTCH_INCLUDE_DIR /usr/include/scotch)
set(SCOTCH_LIBRARY_DIR /usr/lib/x86_64-linux-gnu)
foreach(component scotch scotcherr ptscotch ptscotcherr)
  find_library(SCOTCH_${component}_LIBRARY NAMES ${component} REQUIRED)
  if(NOT TARGET SCOTCH::${component})
    add_library(SCOTCH::${component} UNKNOWN IMPORTED)
    set_target_properties(SCOTCH::${component} PROPERTIES IMPORTED_LOCATION "${SCOTCH_${component}_LIBRARY}" INTERFACE_INCLUDE_DIRECTORIES "${SCOTCH_INCLUDE_DIR}")
  endif()
endforeach()
set_property(TARGET SCOTCH::ptscotch PROPERTY INTERFACE_LINK_LIBRARIES "SCOTCH::scotch;SCOTCH::ptscotcherr;SCOTCH::scotcherr;MPI::MPI_C")
set(SCOTCH_FOUND TRUE)
