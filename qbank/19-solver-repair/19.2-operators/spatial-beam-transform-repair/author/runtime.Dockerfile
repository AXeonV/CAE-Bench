FROM caeoj-chrono846-core:base
RUN apt-get update && apt-get install -y --no-install-recommends libboost-dev clang && rm -rf /var/lib/apt/lists/*
COPY source/ /opt/kratos-source/
RUN cmake -S /opt/kratos-source -B /opt/kratos-build -G Ninja -DCMAKE_CXX_COMPILER=clang++ -DCMAKE_C_COMPILER=clang -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_FLAGS_RELEASE='-O1 -DNDEBUG' -DKRATOS_BUILD_TESTING=OFF -DUSE_MPI=OFF -DUSE_EIGEN_MKL=OFF -DUSE_EIGEN_SUITESPARSE=OFF -DKRATOS_SHARED_MEMORY_PARALLELIZATION=C++11
RUN cmake --build /opt/kratos-build --target KratosCore -j2
COPY driver/ /opt/beam-driver/
RUN cmake -S /opt/beam-driver -B /opt/beam-build -G Ninja -DCMAKE_CXX_COMPILER=clang++ && cmake --build /opt/beam-build -j2
ENV LD_LIBRARY_PATH=/opt/kratos-build/kratos:/opt/beam-build
WORKDIR /app

