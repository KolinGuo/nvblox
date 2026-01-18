#[[
Copyright (c) 2023 NVIDIA CORPORATION & AFFILIATES. All rights reserved.

NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
property and proprietary rights in and to this material, related
documentation and any modifications thereto. Any use, reproduction,
disclosure or distribution of this material and related documentation
without an express license agreement from NVIDIA CORPORATION or
its affiliates is strictly prohibited.
]]

# Torch messes up the architecture flags, so have to restore them
set(CMAKE_CUDA_ARCHITECTURES_OLD ${CMAKE_CUDA_ARCHITECTURES})
find_package(Torch REQUIRED)
set(CMAKE_CUDA_ARCHITECTURES ${CMAKE_CUDA_ARCHITECTURES_OLD})

# On Jetson, we need to link explicitly against cudnn
if(CMAKE_SYSTEM_PROCESSOR STREQUAL "aarch64")
  list(APPEND TORCH_LIBRARIES cudnn)
endif()

# Nvblox-torch python wrapper
add_nvblox_shared_library(
  py_nvblox
  SOURCE_FILES
  src/py_nvblox.cu
  src/py_mapper.cu
  src/py_scene.cu
  src/convert_tensors.cpp
  src/sdf_query.cu
  src/py_layer.cpp
  src/py_mesh.cpp
  src/py_mapper_params.cpp
  src/cuda_stream.cpp
  src/py_rendering.cpp
  LINK_LIBRARIES_PUBLIC
  nvblox_lib
  ${TORCH_LIBRARIES}
  LINK_LIBRARIES_PRIVATE
  nvblox_stdgpu
  INCLUDE_DIRECTORIES_PUBLIC
  $<BUILD_INTERFACE:${CMAKE_CURRENT_LIST_DIR}/include>
  $<INSTALL_INTERFACE:include>
  ${CMAKE_CUDA_TOOLKIT_INCLUDE_DIRECTORIES})

# Use whole-archive linking for nvblox_gpu_hash to ensure all template instantiations
# (like GPULayerView<OccupancyBlock>) are included in the final shared library.
# Without this, only directly referenced symbols would be pulled from the static library,
# causing undefined symbol errors at runtime.
# Ensure nvblox_gpu_hash is built before py_nvblox
add_dependencies(py_nvblox nvblox_gpu_hash)
target_link_libraries(py_nvblox PRIVATE
  -Wl,--whole-archive
  $<TARGET_FILE:nvblox_gpu_hash>
  -Wl,--no-whole-archive
)

# Nvblox-torch python wrapper
add_nvblox_shared_library(
  py_nvblox_test
  SOURCE_FILES
  src/convert_tensors.cpp
  LINK_LIBRARIES_PUBLIC
  nvblox_lib
  ${TORCH_LIBRARIES}
  INCLUDE_DIRECTORIES_PUBLIC
  $<BUILD_INTERFACE:${CMAKE_CURRENT_LIST_DIR}/include>
  $<INSTALL_INTERFACE:include>
  ${CMAKE_CUDA_TOOLKIT_INCLUDE_DIRECTORIES})

# For in-place/editable builds, put both libraries in nvblox_torch/lib/
if(DEFINED INPLACE_LIB_DIR)
  set_target_properties(py_nvblox PROPERTIES
    LIBRARY_OUTPUT_DIRECTORY ${INPLACE_LIB_DIR}
    BUILD_RPATH "$ORIGIN"
  )

  # Copy nvblox_lib to the same directory after build
  add_custom_command(TARGET py_nvblox POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E copy
      $<TARGET_FILE:nvblox_lib>
      ${INPLACE_LIB_DIR}/
    COMMENT "Copying nvblox_lib to nvblox_torch/lib/ for in-place builds"
  )
endif()

# Tests
include(CTest)
if(BUILD_TESTING)
  enable_testing()
  add_subdirectory(tests)
endif()
