#
# Copyright (c) 2023 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
#
# NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
# property and proprietary rights in and to this material, related
# documentation and any modifications thereto. Any use, reproduction,
# disclosure or distribution of this material and related documentation
# without an express license agreement from NVIDIA CORPORATION or
# its affiliates is strictly prohibited.
#
from typing import Any
import os
import glob

import torch


# get paths
def get_module_path() -> str:
    """Get the path to the nvblox_torch module."""
    path = os.path.dirname(__file__)
    return path


def get_nvblox_py_library_path() -> str:
    """Get the path to the nvblox_torch .so library.

    This function searches for the library in multiple locations to support:
    1. Installed packages (library in lib/nvblox_torch/cpp/)
    2. In-place/editable builds (library in lib/nvblox_torch/cpp/)
    3. Build directory layouts

    Returns:
        Path to libpy_nvblox.so

    Raises:
        FileNotFoundError: If the library cannot be found in any location
    """
    module_path = get_module_path()

    # List of possible library locations (in order of preference)
    possible_paths = [
        # Standard installed/in-place location
        os.path.join(module_path, 'nvblox_torch/cpp/libpy_nvblox.so'),
        # Alternative paths for different build configurations
        os.path.join(module_path, 'nvblox_torch', 'cpp', 'libpy_nvblox.so'),
        # Direct path (for cases where lib/ is the library directory)
        os.path.join(module_path, 'libpy_nvblox.so'),
    ]

    # Also check for libraries in build directories relative to the source
    source_root = os.path.dirname(os.path.dirname(module_path))
    build_patterns = [
        os.path.join(source_root, 'build', '**', 'libpy_nvblox.so'),
        os.path.join(source_root, 'build', '**', 'cpp', 'libpy_nvblox.so'),
    ]

    # First, check explicit paths
    for path in possible_paths:
        if os.path.exists(path):
            return path

    # Then, search build directories using glob
    for pattern in build_patterns:
        matches = glob.glob(pattern, recursive=True)
        if matches:
            # Return the first match
            return matches[0]

    # If we get here, we couldn't find the library
    search_locations = '\n  - '.join(possible_paths + build_patterns)
    raise FileNotFoundError(
        f"Could not find libpy_nvblox.so. Searched in:\n  - {search_locations}\n"
        "Please ensure the package is built. For in-place builds, run:\n"
        "  pip install -e .\n"
        "Or build with CMake:\n"
        "  mkdir build && cd build && cmake .. && make"
    )


def get_nvblox_torch_class(class_name: str) -> Any:
    """Get one of the C++classes wrapped in the nvblox_torch library."""
    torch.classes.load_library(get_nvblox_py_library_path())
    return getattr(torch.classes.pynvblox, class_name)
