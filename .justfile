set minimum-version := '1.59.0'
set unstable
set default-list
set default-script
set positional-arguments
set quiet
set script-interpreter := ['bash', '-euo', 'pipefail']
set shell := ['bash', '-euo', 'pipefail', '-c']

export REGISTRY := env('REGISTRY', 'ghcr.io')
export OWNER := env('OWNER', 'eudaldgr-labs')
export TAG := env('TAG', 'test')
export SIGNING_KEY := env('SIGNING_KEY', 'melange.rsa')
export KEYRING := env('KEYRING', 'melange.rsa.pub')
export PACKAGES_DIR := env('PACKAGES_DIR', 'packages')
export OUT_DIR := env('OUT_DIR', 'out')
export DOCKER := env('DOCKER', 'docker')
export PYTHON := env('PYTHON', '.venv/bin/python')

# Install the Python helpers and local Git hooks after `mise install`.
setup:
    python -m venv --clear .venv
    .venv/bin/python -m pip install -r requirements-dev.txt
    if [[ -z "${CI:-}" ]]; then lefthook install; fi

# Check automation syntax without building images.
lint:
    just --fmt --check
    mise fmt --check
    actionlint
    zizmor --offline .github
    shellcheck scripts/*.sh
    git diff --check

# Formatting is explicit and never stages files.
fmt:
    just --fmt
    mise fmt

list:
    find . -mindepth 2 -maxdepth 2 \( -name melange.yaml -o -name apko.yaml \) -print | cut -d/ -f2 | sort -u

keygen:
    if [[ -f "$SIGNING_KEY" && -f "$KEYRING" ]]; then exit 0; fi
    if [[ -e "$SIGNING_KEY" || -e "$KEYRING" ]]; then
      echo 'Incomplete signing key pair; restore the missing key before building' >&2
      exit 1
    fi
    "$DOCKER" run --rm --user "$(id -u):$(id -g)" -v "$PWD:/work" -w /work \
      --entrypoint /usr/bin/melange "$MELANGE_IMAGE" keygen "$SIGNING_KEY"
    chmod 600 "$SIGNING_KEY"

# Build an APK only; its internal prerequisites must already exist.
melange name='all' arch=env('ARCH', 'aarch64'):
    if [[ "$1" == all ]]; then
      packages=$("$PYTHON" -m scripts.packages order all melange)
      for package in $packages; do just melange "$package" "$2"; done
      exit 0
    fi
    [[ -f "$1/melange.yaml" ]] || { echo "Unknown Melange package: $1" >&2; exit 1; }
    just keygen
    mkdir -p "$PACKAGES_DIR"
    "$PYTHON" -m scripts.packages "$1" melange "$2"
    pins=$("$PYTHON" -m scripts.packages pins "$1" melange)
    just _melange build "$1/melange.yaml" --arch "$2" $pins --source-dir "$1" \
      --signing-key "/work/$SIGNING_KEY" --repository-append "/work/$PACKAGES_DIR" \
      --keyring-append "/work/$KEYRING" --pipeline-dir /work/.pipelines --out-dir "/work/$PACKAGES_DIR"
    just index "$2"

# Propose security pins for <name> in Melange and write them into its bump step.
remediate name arch=env('ARCH', 'x86_64'):
    context=$("$PYTHON" -m scripts.remediate prepare-plan "$1" "$2")
    rm -rf "out/remediation/$1/packages"
    just _melange build "$context/plan.yaml" --arch "$2" --source-dir "$context" \
      --pipeline-dir /work/.pipelines --out-dir "/work/out/remediation/$1/packages"
    "$PYTHON" -m scripts.remediate extract "$1" "$2"
    "$PYTHON" -m scripts.remediate write "$1"

# Re-plan security pins for every opted-in recipe this branch changed.
regenerate arch=env('ARCH', 'x86_64'):
    names=$("$PYTHON" -m scripts.remediate opted --changed | "$PYTHON" -c 'import json, sys; print(" ".join(json.load(sys.stdin)))')
    for name in $names; do just remediate "$name" "$1"; done

index arch=env('ARCH', 'aarch64'):
    arch="$1"
    shopt -s nullglob
    set -- "$PACKAGES_DIR/$arch/"*.apk
    if (( $# )); then
      just _melange index --signing-key "/work/$SIGNING_KEY" \
        -o "/work/$PACKAGES_DIR/$arch/APKINDEX.tar.gz" "$@"
    fi

# Test an existing APK in Melange's isolated test environment.
melangecheck name arch=env('ARCH', 'aarch64'):
    [[ -f "$1/melange.yaml" ]] || { echo "Unknown Melange package: $1" >&2; exit 1; }
    just keygen
    pins=$("$PYTHON" -m scripts.packages pins "$1" test)
    just _melange test "$1/melange.yaml" --arch "$2" $pins \
      --repository-append "/work/$PACKAGES_DIR" --keyring-append "/work/$KEYRING" --pipeline-dirs /work/.pipelines

# Build and test APKs in dependency order.
test name='all' arch=env('ARCH', 'aarch64'):
    packages=$("$PYTHON" -m scripts.packages order "$1" melange)
    for package in $packages; do
      just melange "$package" "$2"
      just melangecheck "$package" "$2"
    done

# Build prerequisites, test APKs and assemble the image.
build name='all' arch=env('ARCH', 'aarch64'):
    packages=$("$PYTHON" -m scripts.packages order "$1" apko)
    for package in $packages; do
      just melange "$package" "$2"
      just melangecheck "$package" "$2"
    done
    if [[ "$1" == all ]]; then
      for config in */apko.yaml; do just apko "${config%/*}" "$2"; done
    else
      just apko "$1" "$2"
    fi

# Assemble from existing APKs, retaining the exact archive and SBOM.
apko name='all' arch=env('ARCH', 'aarch64'):
    if [[ "$1" == all ]]; then
      for config in */apko.yaml; do just apko "${config%/*}" "$2"; done
      exit 0
    fi
    [[ -f "$1/apko.yaml" ]] || { echo "Unknown Apko package: $1" >&2; exit 1; }
    case "$2" in aarch64) docker_arch=arm64 ;; x86_64) docker_arch=amd64 ;; *) echo "Unsupported architecture: $2" >&2; exit 1 ;; esac
    "$PYTHON" -m scripts.packages "$1" apko "$2"
    just keygen
    tarball="$OUT_DIR/$1-$2.tar"
    sbom="$OUT_DIR/$1-$2.sbom"
    image="$REGISTRY/$OWNER/$1:$TAG"
    rm -f "$tarball"
    mkdir -p "$sbom"
    pins=$("$PYTHON" -m scripts.packages pins "$1" apko)
    "$DOCKER" run --rm -v "$PWD:/work" -w /work --entrypoint /usr/bin/apko "$APKO_IMAGE" \
      build "$1/apko.yaml" "$image" "$tarball" $pins --arch "$2" \
      --repository-append "/work/$PACKAGES_DIR" --keyring-append "/work/$KEYRING" --sbom-path "/work/$sbom"
    mv "$sbom/sbom-$2.spdx.json" "$OUT_DIR/$1-$2.spdx.json"
    "$DOCKER" load --input "$tarball"
    "$DOCKER" tag "$image-$docker_arch" "$image"

# Scan the same archive that was tested, with both scanners; CVEs are advisory.
scan name='all' arch=env('ARCH', 'aarch64'):
    if [[ "$1" == all ]]; then
      for config in */apko.yaml; do just scan "${config%/*}" "$2"; done
      exit 0
    fi
    bash scripts/scan.sh "$1" "$2" "$OUT_DIR/$1-$2.tar"
    trivy image --input "$OUT_DIR/$1-$2.tar" --format sarif --output "trivy-$1-$2.sarif" --exit-code 0

# Explicitly push a previously assembled local image.
push name:
    if [[ "$1" == all ]]; then
      for config in */apko.yaml; do just push "${config%/*}"; done
      exit 0
    fi
    "$DOCKER" push "$REGISTRY/$OWNER/$1:$TAG"

report:
    "$PYTHON" .report/report.py

clean:
    rm -rf "$PACKAGES_DIR" "$OUT_DIR" .artifacts
    rm -f sbom-*.spdx.json

clean-images arch=env('ARCH', 'aarch64'):
    case "$1" in aarch64) docker_arch=arm64 ;; x86_64) docker_arch=amd64 ;; *) exit 1 ;; esac
    for config in */apko.yaml; do
      image="$REGISTRY/$OWNER/${config%/*}:$TAG"
      "$DOCKER" rmi "$image" "$image-$docker_arch" || true
    done

[private]
_melange *args:
    "$DOCKER" run --rm --privileged -v "$PWD:/work" -w /work --entrypoint /usr/bin/melange "$MELANGE_IMAGE" "$@"
