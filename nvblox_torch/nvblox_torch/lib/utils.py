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
import importlib.util

import torch


def get_package_root() -> str:
    """Get the root path of the installed nvblox_torch package.

    This uses importlib to reliably find the package location whether
    installed via wheel, editable install, or run from source.
    """
    spec = importlib.util.find_spec('nvblox_torch')
    if spec is not None and spec.origin is not None:
        # spec.origin is the path to __init__.py
        return os.path.dirname(os.path.abspath(spec.origin))
    # Fallback: derive from this file's location (utils.py is in lib/)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_module_path() -> str:
    """Get the path to the nvblox_torch/lib module (where utils.py lives)."""
    return os.path.dirname(os.path.abspath(__file__))


def get_nvblox_py_library_path() -> str:
    """Get the path to the nvblox_torch .so library.

    This function searches for the library in multiple locations to support:
    1. Wheel-installed packages (pip install or pip install git+...)
    2. In-place/editable builds (pip install -e .)
    3. Build directory layouts

    Returns:
        Path to libpy_nvblox.so

    Raises:
        FileNotFoundError: If the library cannot be found in any location
    """
    package_root = get_package_root()

    # List of possible library locations (in order of preference)
    # package_root is the nvblox_torch package directory (site-packages/nvblox_torch/)
    possible_paths = [
        # Primary path for wheel installs: <package>/lib/cpp/
        os.path.join(package_root, 'lib', 'cpp', 'libpy_nvblox.so'),
        # Legacy path for backward compatibility: <package>/lib/nvblox_torch/cpp/
        os.path.join(package_root, 'lib', 'nvblox_torch', 'cpp', 'libpy_nvblox.so'),
        # Direct path in lib/
        os.path.join(package_root, 'lib', 'libpy_nvblox.so'),
    ]

    # Also check for libraries in build directories relative to the source
    # This handles cases where the package is run from source without install
    # For source trees, package_root is nvblox_torch/nvblox_torch/, so go up one more level
    source_root = os.path.dirname(package_root)
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
        f"Package root: {package_root}\n"
        "Please ensure the package is built. For wheel installs, run:\n"
        "  pip install .\n"
        "For installation from git:\n"
        "  pip install git+https://github.com/<org>/<repo>.git#subdirectory=nvblox_torch\n"
        "For editable/in-place builds:\n"
        "  pip install -e .\n"
        "Or build with CMake:\n"
        "  mkdir build && cd build && cmake .. && make"
    )


def get_nvblox_torch_class(class_name: str) -> Any:
    """Get one of the C++classes wrapped in the nvblox_torch library."""
    torch.classes.load_library(get_nvblox_py_library_path())
    return getattr(torch.classes.pynvblox, class_name)
