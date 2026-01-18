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
  # Try to detect torch's CUDA architectures to ensure ABI compatibility
  # This is important because torch adds -gencode flags that affect Thrust namespacing
  find_package(Python COMPONENTS Interpreter QUIET)
  if(Python_FOUND)
    execute_process(
      COMMAND ${Python_EXECUTABLE} -c "
import torch
# Get the minimum arch from torch's supported list to match its compile flags
archs = torch.cuda.get_arch_list()
# Extract numeric parts (e.g., 'sm_90' -> '90')
nums = [int(a.replace('sm_', '').replace('compute_', '')) for a in archs if a.startswith('sm_')]
if nums:
    # Use the architectures that torch was compiled with
    print(';'.join(str(n) for n in sorted(nums)))"
      OUTPUT_VARIABLE TORCH_CUDA_ARCHS_OUTPUT
      OUTPUT_STRIP_TRAILING_WHITESPACE
      ERROR_QUIET
      RESULT_VARIABLE TORCH_ARCHS_RESULT
    )
    if(TORCH_ARCHS_RESULT EQUAL 0 AND TORCH_CUDA_ARCHS_OUTPUT)
      message(STATUS "Detected torch CUDA architectures: ${TORCH_CUDA_ARCHS_OUTPUT}")
      set(CMAKE_CUDA_ARCHITECTURES ${TORCH_CUDA_ARCHS_OUTPUT} CACHE STRING "CUDA architectures from torch" FORCE)
      set(CMAKE_CUDA_ARCHITECTURES_SET_EXTERNALLY TRUE)
    endif()
  endif()
endif()

# Set the project name and version
project(
  nvblox_torch
  VERSION 0.0.8
  LANGUAGES CXX C CUDA)

# Options
option(BUILD_TESTING "Build tests" OFF)
option(NVBLOX_TORCH_STANDALONE "Build nvblox_torch standalone (find nvblox)" OFF)

# This option controls whether to use the old Pre-CXX11 ABI.
# We detect PyTorch's ABI setting using Python (to avoid CMake side effects from find_package(Torch)).
# PyTorch 2.0+ typically uses the new CXX11 ABI.
find_package(Python COMPONENTS Interpreter QUIET)
if(Python_FOUND)
  execute_process(
    COMMAND ${Python_EXECUTABLE} -c "import torch; print('1' if torch._C._GLIBCXX_USE_CXX11_ABI else '0')"
    OUTPUT_VARIABLE PYTORCH_CXX11_ABI_OUTPUT
    OUTPUT_STRIP_TRAILING_WHITESPACE
    ERROR_QUIET
    RESULT_VARIABLE PYTORCH_ABI_RESULT
  )
  if(PYTORCH_ABI_RESULT EQUAL 0)
    if(PYTORCH_CXX11_ABI_OUTPUT STREQUAL "0")
      set(PYTORCH_USES_OLD_ABI ON)
    else()
      set(PYTORCH_USES_OLD_ABI OFF)
    endif()
    option(PRE_CXX11_ABI_LINKABLE "Better support pre-C++11 ABI library users" ${PYTORCH_USES_OLD_ABI})
    message(STATUS "Detected PyTorch CXX11 ABI: ${PYTORCH_CXX11_ABI_OUTPUT}, PRE_CXX11_ABI_LINKABLE=${PRE_CXX11_ABI_LINKABLE}")
  else()
    # PyTorch not importable, default to modern ABI
    option(PRE_CXX11_ABI_LINKABLE "Better support pre-C++11 ABI library users" OFF)
    message(STATUS "Could not detect PyTorch ABI, defaulting PRE_CXX11_ABI_LINKABLE=OFF")
  endif()
else()
  # Python not found, default to modern ABI
  option(PRE_CXX11_ABI_LINKABLE "Better support pre-C++11 ABI library users" OFF)
  message(STATUS "Python not found, defaulting PRE_CXX11_ABI_LINKABLE=OFF")
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
# The wheel.install-dir in pyproject.toml is set to "nvblox_torch/lib"
# So CMake destinations are relative to that path in the final wheel.

# Set install RPATH for py_nvblox to find nvblox_lib at runtime
# The libraries are installed as:
#   nvblox_torch/lib/cpp/libpy_nvblox.so
#   nvblox_torch/lib/nvblox/libnvblox_lib.so
# So the relative path from cpp/ to nvblox/ is ../nvblox
set_target_properties(py_nvblox PROPERTIES
  INSTALL_RPATH "$ORIGIN/../nvblox"
  BUILD_WITH_INSTALL_RPATH FALSE
)

# Install py_nvblox library to cpp/ (becomes nvblox_torch/lib/cpp/ in wheel)
install(TARGETS py_nvblox
  LIBRARY DESTINATION cpp
  RUNTIME DESTINATION cpp
)

# Install nvblox_lib to nvblox/ (becomes nvblox_torch/lib/nvblox/ in wheel)
install(TARGETS nvblox_lib
  LIBRARY DESTINATION nvblox
  RUNTIME DESTINATION nvblox
)

# For in-place/editable builds, also copy libraries to source tree
# This is done via a post-build step in cpp/CMakeLists.txt
set(INPLACE_LIB_DIR ${CMAKE_CURRENT_SOURCE_DIR}/nvblox_torch/lib CACHE PATH "In-place library directory")
