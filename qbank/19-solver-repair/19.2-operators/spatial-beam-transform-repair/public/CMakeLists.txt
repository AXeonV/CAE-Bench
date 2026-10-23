cmake_minimum_required(VERSION 3.15)
project(BeamRepair LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 20)
set(SRC /opt/kratos-source)
set(APP ${SRC}/applications/StructuralMechanicsApplication)
add_library(beam_repair SHARED
 ${APP}/custom_elements/beam_elements/timoshenko_beam_element_3D2N.cpp
 ${APP}/custom_elements/beam_elements/timoshenko_beam_element_2D2N.cpp
 ${APP}/custom_constitutive/beam_constitutive_law.cpp
 ${APP}/custom_constitutive/timoshenko_beam_elastic_constitutive_law_3d.cpp
 ${APP}/custom_utilities/structural_mechanics_element_utilities.cpp
 ${APP}/custom_utilities/constitutive_law_utilities.cpp
 ${APP}/structural_mechanics_application_variables.cpp)
target_include_directories(beam_repair PUBLIC ${SRC}/kratos ${SRC}/external_libraries ${APP})
target_compile_definitions(beam_repair PUBLIC KRATOS_SMP_CXX11 BOOST_UBLAS_MOVE_SEMANTICS)
target_compile_options(beam_repair PRIVATE -O1 -w)
target_link_libraries(beam_repair PUBLIC /opt/kratos-build/kratos/libKratosCore.so)
add_executable(beam_driver driver.cpp)
target_link_libraries(beam_driver PRIVATE beam_repair)
set_target_properties(beam_driver PROPERTIES BUILD_RPATH "/opt/kratos-build/kratos;/opt/beam-build")

