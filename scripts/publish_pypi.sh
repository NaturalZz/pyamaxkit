#!/usr/bin/env bash
set -euo pipefail

repo=${PYPI_REPOSITORY:-pypi}
token=${PYPI_TOKEN:-}

command -v go >/dev/null || { echo "Go compiler not found" >&2; exit 1; }
command -v gcc >/dev/null || { echo "C compiler not found" >&2; exit 1; }

py_arch=$(uname -m)
case "$py_arch" in
  x86_64) go_target=amd64 ;;
  aarch64) go_target=arm64 ;;
  *) go_target="$py_arch" ;;
esac
current=$(go env GOARCH)
if [ "$current" != "$go_target" ]; then
  echo "Adjusting GOARCH from $current to $go_target for wheel build"
  export GOARCH=$go_target
  case "$go_target" in
    arm64) cross_cc=aarch64-linux-gnu-gcc ;;
    amd64) cross_cc=x86_64-linux-gnu-gcc ;;
    *) cross_cc="" ;;
  esac
  if [ -n "$cross_cc" ] && command -v "$cross_cc" >/dev/null; then
    export CC="$cross_cc"
  elif [ -n "$cross_cc" ]; then
    echo "Cross compiler '$cross_cc' not found" >&2
    exit 1
  fi
fi

python_cmd=$(command -v python3 || command -v python)
"$python_cmd" -m pip install --upgrade build twine scikit-build cython auditwheel

rm -rf dist
"$python_cmd" -m build

# Convert the wheel to a manylinux2014 compatible wheel
whl_file=$("$python_cmd" scripts/get_whl_file.py dist)
(
  cd dist
  "$python_cmd" -m auditwheel repair "${whl_file}" --plat manylinux2014_x86_64
  mv wheelhouse/*.whl .
  rm -r wheelhouse
  rm "${whl_file}"
)

upload=(twine upload --repository "$repo")
if [ -n "$token" ]; then
  upload+=( -u __token__ -p "$token" )
fi
upload+=( dist/* )
"${upload[@]}"

