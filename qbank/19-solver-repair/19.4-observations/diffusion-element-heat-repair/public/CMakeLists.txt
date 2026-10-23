cmake_minimum_required(VERSION 3.20)
project(SourceSyntax NONE)
find_package(Python3 REQUIRED COMPONENTS Interpreter)
set(SOURCE_ROOT /opt/pybamm-build/source/packages/pybamm/src/pybamm/models/submodels/equivalent_circuit_elements)
foreach(name diffusion_element thermal)
  set(bytecode ${SOURCE_ROOT}/__pycache__/${name}.cpython-314.pyc)
  add_custom_command(OUTPUT ${bytecode}
    COMMAND ${Python3_EXECUTABLE} -c "import py_compile; py_compile.compile('${SOURCE_ROOT}/${name}.py', cfile='${bytecode}', doraise=True)"
    DEPENDS ${SOURCE_ROOT}/${name}.py VERBATIM)
  list(APPEND compiled ${bytecode})
endforeach()
add_custom_target(repair_sources ALL DEPENDS ${compiled})
