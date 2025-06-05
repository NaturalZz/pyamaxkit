#!/usr/bin/env python3
"""Build and upload package to PyPI.

This script packages the project and uploads the distributions to PyPI.
The target repository can be specified via the PYPI_REPOSITORY environment
variable (default: ``pypi``). Provide an API token via the ``PYPI_TOKEN``
environment variable.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path
from shutil import which
import platform


def run(cmd):
    print(f"> {cmd}")
    subprocess.check_call(cmd, shell=True)


def main():
    if which("go") is None:
        raise RuntimeError(
            "Go compiler not found. Install it and ensure 'go' is in your PATH."
        )
    if which("gcc") is None:
        raise RuntimeError(
            "C compiler not found. Install GCC or another compiler compatible with CGO."
        )

    # Align the Go target architecture with the current Python interpreter.
    arch_map = {"x86_64": "amd64", "aarch64": "arm64"}
    py_arch = platform.machine()
    go_target = arch_map.get(py_arch, py_arch)
    go_arch = subprocess.check_output(["go", "env", "GOARCH"]).decode().strip()
    if go_arch != go_target:
        print(f"Adjusting GOARCH from {go_arch} to {go_target} for wheel build")
        os.environ["GOARCH"] = go_target
        cross_cc_map = {
            "arm64": "aarch64-linux-gnu-gcc",
            "amd64": "x86_64-linux-gnu-gcc",
        }
        cross_cc = cross_cc_map.get(go_target)
        if cross_cc and which(cross_cc):
            os.environ.setdefault("CC", cross_cc)
        elif cross_cc:
            raise RuntimeError(f"Cross compiler '{cross_cc}' not found in PATH")

    # Ensure required tools are available
    # Use the current Python interpreter to ensure the ``python`` command
    # exists in environments where only ``python3`` is available.
    run(
        f"{sys.executable} -m pip install --upgrade build twine scikit-build cython"
    )

    dist_dir = Path("dist")
    if dist_dir.exists():
        shutil.rmtree(dist_dir)

    # Build sdist and wheel
    run(f"{sys.executable} -m build")

    repository = os.environ.get("PYPI_REPOSITORY", "pypi")
    token = os.environ.get("PYPI_TOKEN")

    upload_cmd = ["twine", "upload", "--repository", repository]
    if token:
        upload_cmd += ["-u", "__token__", "-p", token]
    upload_cmd.append("dist/*")

    run(" ".join(upload_cmd))


if __name__ == "__main__":
    main()
