#!/bin/sh
set -eu
name=$1
arch=$2
tarball=$3
mkdir -p .cache/grype
"${DOCKER:-docker}" run --rm --entrypoint grype \
  -v "$PWD:/work" -w /work \
  -e GRYPE_DB_CACHE_DIR=/work/.cache/grype \
  "$APKO_IMAGE" "docker-archive:$tarball" \
  --output "json=cve-report-$name-$arch.json" \
  --output "sarif=grype-$name-$arch.sarif"
