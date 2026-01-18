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


def get_lib_dir() -> str:
    """Get the path to nvblox_torch/lib/ directory where .so files live."""
    return os.path.dirname(os.path.abspath(__file__))


def _find_library(name: str) -> str:
    """Find a library by name, checking lib/ directory and build/ directory.

    Args:
        name: Library filename (e.g., 'libpy_nvblox.so')

    Returns:
        Absolute path to the library

    Raises:
        FileNotFoundError: If the library cannot be found
    """
    lib_dir = get_lib_dir()

    # Primary location: nvblox_torch/lib/<name>
    primary_path = os.path.join(lib_dir, name)
    if os.path.exists(primary_path):
        return primary_path

    # Fallback: search in build directory (for development)
    # lib_dir is nvblox_torch/lib, so source root is two levels up
    source_root = os.path.dirname(os.path.dirname(lib_dir))
    build_pattern = os.path.join(source_root, 'build', '**', name)
    matches = glob.glob(build_pattern, recursive=True)
    if matches:
        return matches[0]

    raise FileNotFoundError(
        f"Could not find {name}. Searched in:\n"
        f"  - {primary_path}\n"
        f"  - {build_pattern}\n"
        "Please ensure the package is built with: uv sync"
    )


def get_nvblox_py_library_path() -> str:
    """Get the path to libpy_nvblox.so."""
    return _find_library('libpy_nvblox.so')


def get_nvblox_lib_path() -> str:
    """Get the path to libnvblox_lib.so."""
    return _find_library('libnvblox_lib.so')


def get_nvblox_torch_class(class_name: str) -> Any:
    """Get one of the C++ classes wrapped in the nvblox_torch library."""
    torch.classes.load_library(get_nvblox_py_library_path())
    return getattr(torch.classes.pynvblox, class_name)
