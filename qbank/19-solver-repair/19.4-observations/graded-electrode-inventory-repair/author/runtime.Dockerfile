FROM caeoj-pybamm5859-core:offline-sdk
USER root
COPY build-wheels /opt/pybamm-build-wheels
RUN pip install --no-index --find-links=/opt/pybamm-build-wheels hatchling hatch-vcs editables
RUN rm -rf /opt/pybamm-build/source /opt/pybamm-build/CMakeCache.txt /opt/pybamm-build/CMakeFiles
COPY source /opt/pybamm-build/source
RUN SETUPTOOLS_SCM_PRETEND_VERSION=0.0.0 pip install --no-build-isolation --no-deps -e /opt/pybamm-build/source/packages/pybamm
COPY CMakeLists.txt /opt/repair-cmake/CMakeLists.txt
COPY driver.py /opt/repair-driver/driver.py
RUN cmake -S /opt/repair-cmake -B /opt/pybamm-build -G Ninja && cmake --build /opt/pybamm-build --target repair_sources && chown -R 1000:1000 /opt/pybamm-build
RUN python -c "import pybamm; assert pybamm.__file__.startswith('/opt/pybamm-build/source/')"
