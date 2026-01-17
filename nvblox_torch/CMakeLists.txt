cmake_minimum_required(VERSION 3.22.1)

# Set default build type if not provided by user
if(NOT CMAKE_BUILD_TYPE)
  set(CMAKE_BUILD_TYPE
      "RelWithDebInfo"
      CACHE
        STRING
        "Choose the type of build, options are: None Debug Release RelWithDebInfo"
        FORCE)
endif(NOT CMAKE_BUILD_TYPE)

# By default we build for the native cuda architecture. Customize by passing
# '-DCMAKE_CUDA_ARCHITECTURES=89;75;72' to cmake.
if(DEFINED CMAKE_CUDA_ARCHITECTURES)
  set(CMAKE_CUDA_ARCHITECTURES_SET_EXTERNALLY TRUE)
else()
  set(CMAKE_CUDA_ARCHITECTURES_SET_EXTERNALLY FALSE)
endif()

# Set the project name and version
project(
  nvblox_torch
  VERSION 0.0.8
  LANGUAGES CXX C CUDA)

# Options
option(BUILD_TESTING "Build tests" OFF)
option(NVBLOX_TORCH_STANDALONE "Build nvblox_torch standalone (find nvblox)" OFF)

# This option avoids any implementations using std::string in their signature in
# header files. Useful for Nvblox PyTorch wrapper, which requires the old
# Pre-CXX11 ABI on x86
if(CMAKE_SYSTEM_PROCESSOR STREQUAL "x86_64" OR CMAKE_SYSTEM_PROCESSOR STREQUAL "AMD64")
  option(PRE_CXX11_ABI_LINKABLE "Better support pre-C++11 ABI library users" ON)
  message(STATUS "Building with pre-C++11 ABI support")
else()
  option(PRE_CXX11_ABI_LINKABLE "Better support pre-C++11 ABI library users" OFF)
  message(STATUS "Building without pre-C++11 ABI support")
endif()

# Include nvblox cmake helper functions from parent directory
include(${CMAKE_CURRENT_SOURCE_DIR}/../cmake/cuda/setup_compute_capability.cmake)
include(${CMAKE_CURRENT_SOURCE_DIR}/../cmake/nvblox_targets.cmake)

# If standalone, find nvblox package. Otherwise, assume it's built alongside.
if(NVBLOX_TORCH_STANDALONE)
  find_package(nvblox REQUIRED)
else()
  # Build nvblox from parent directory
  add_subdirectory(${CMAKE_CURRENT_SOURCE_DIR}/../nvblox ${CMAKE_BINARY_DIR}/nvblox)
endif()

# Build the pytorch wrapper
add_subdirectory(cpp)

# Installation rules for scikit-build-core
# Install py_nvblox library to nvblox_torch/cpp/
install(TARGETS py_nvblox
  LIBRARY DESTINATION nvblox_torch/cpp
  RUNTIME DESTINATION nvblox_torch/cpp
)

# Install nvblox_lib to nvblox/
install(TARGETS nvblox_lib
  LIBRARY DESTINATION nvblox
  RUNTIME DESTINATION nvblox
)

# For in-place/editable builds, also copy libraries to source tree
# This is done via a post-build step in cpp/CMakeLists.txt
set(INPLACE_LIB_DIR ${CMAKE_CURRENT_SOURCE_DIR}/nvblox_torch/lib CACHE PATH "In-place library directory")
