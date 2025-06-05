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
from pathlib import Path


def run(cmd):
    print(f"> {cmd}")
    subprocess.check_call(cmd, shell=True)


def main():
    # Ensure required tools are available
    run("python -m pip install --upgrade build twine")

    dist_dir = Path("dist")
    if dist_dir.exists():
        shutil.rmtree(dist_dir)

    # Build sdist and wheel
    run("python -m build")

    repository = os.environ.get("PYPI_REPOSITORY", "pypi")
    token = os.environ.get("PYPI_TOKEN")

    upload_cmd = ["twine", "upload", "--repository", repository]
    if token:
        upload_cmd += ["-u", "__token__", "-p", token]
    upload_cmd.append("dist/*")

    run(" ".join(upload_cmd))


if __name__ == "__main__":
    main()
