cmake_minimum_required(VERSION 3.16)
project(material_driver CXX)
set(CMAKE_CXX_STANDARD 17)
set(ROOT /opt/opensees-source)
add_executable(material_driver driver.cpp
${ROOT}/SRC/material/Material.cpp
${ROOT}/SRC/tagged/TaggedObject.cpp
${ROOT}/SRC/actor/actor/MovableObject.cpp
${ROOT}/SRC/matrix/ID.cpp
${ROOT}/SRC/matrix/Vector.cpp
${ROOT}/SRC/matrix/Matrix.cpp
${ROOT}/SRC/handler/OPS_Stream.cpp
${ROOT}/SRC/handler/StandardStream.cpp
${ROOT}/SRC/element/Information.cpp
${ROOT}/SRC/recorder/response/Response.cpp
${ROOT}/SRC/recorder/response/MaterialResponse.cpp
${ROOT}/SRC/material/uniaxial/UniaxialMaterial.cpp
${ROOT}/SRC/tagged/storage/MapOfTaggedObjects.cpp
${ROOT}/SRC/tagged/storage/MapOfTaggedObjectsIter.cpp
${ROOT}/SRC/domain/component/Parameter.cpp
${ROOT}/SRC/actor/channel/Channel.cpp
${ROOT}/SRC/actor/address/ChannelAddress.cpp
${ROOT}/SRC/material/uniaxial/HystereticMaterial.cpp
${ROOT}/SRC/material/uniaxial/HystereticSMMaterial.cpp
)
target_include_directories(material_driver PRIVATE
${ROOT}/SRC
${ROOT}/SRC/actor/actor
${ROOT}/SRC/actor/address
${ROOT}/SRC/actor/channel
${ROOT}/SRC/actor/message
${ROOT}/SRC/actor/objectBroker
${ROOT}/SRC/api
${ROOT}/SRC/domain/component
${ROOT}/SRC/element
${ROOT}/SRC/handler
${ROOT}/SRC/material
${ROOT}/SRC/material/uniaxial
${ROOT}/SRC/matrix
${ROOT}/SRC/recorder/response
${ROOT}/SRC/tagged
${ROOT}/SRC/tagged/storage
)
target_compile_options(material_driver PRIVATE -O1 -ffunction-sections -fdata-sections)
target_link_options(material_driver PRIVATE -Wl,--gc-sections)
