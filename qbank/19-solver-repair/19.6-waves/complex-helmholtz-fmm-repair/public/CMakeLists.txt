cmake_minimum_required(VERSION 3.20)
project(BemppSourceRepair NONE)
set(Python3_EXECUTABLE /opt/bempp-env/bin/python)
find_package(Python3 3.11 EXACT REQUIRED COMPONENTS Interpreter)
set(SOURCE_ROOT /opt/upstream/bempp-cl-84345ee9ee314c85750f045c7ad38090f5ea5f26/bempp/api/fmm)
foreach(name exafmm fmm_assembler helpers)
  set(bytecode ${SOURCE_ROOT}/__pycache__/${name}.cpython-311.pyc)
  add_custom_command(OUTPUT ${bytecode}
    COMMAND ${Python3_EXECUTABLE} -c "import py_compile; py_compile.compile('${SOURCE_ROOT}/${name}.py', cfile='${bytecode}', doraise=True, invalidation_mode=py_compile.PycInvalidationMode.CHECKED_HASH)"
    DEPENDS ${SOURCE_ROOT}/${name}.py VERBATIM)
  list(APPEND compiled ${bytecode})
endforeach()
add_custom_target(repair_sources ALL DEPENDS ${compiled})
