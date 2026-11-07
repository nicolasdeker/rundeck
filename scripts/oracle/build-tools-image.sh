#!/usr/bin/env bash
# build-tools-image.sh — build the prebuilt tools layer of the oracle fixture (see tools.Dockerfile).
# Usage: scripts/oracle/build-tools-image.sh [image-tag]   (default rdx-oracle-tools:6.3.0)
# Env: ORACLE_IMAGE (base, default rundeck/rundeck:6.3.0), ORACLE_EXTRA_CA (PEM file to trust inside the build;
#      the cloud environment needs /root/.ccr/ca-bundle.crt, CI needs nothing).
set -euo pipefail
tag=${1:-rdx-oracle-tools:6.3.0}
base=${ORACLE_IMAGE:-rundeck/rundeck:6.3.0}
ctx=$(mktemp -d)
trap 'rm -rf "$ctx"' EXIT
cp "$(dirname "${BASH_SOURCE[0]}")/tools.Dockerfile" "$ctx/Dockerfile"
if [ -n "${ORACLE_EXTRA_CA:-}" ] && [ -s "$ORACLE_EXTRA_CA" ]; then cp "$ORACLE_EXTRA_CA" "$ctx/extra-ca.crt"; else : > "$ctx/extra-ca.crt"; fi
docker build --build-arg "IMAGE=$base" -t "$tag" "$ctx"
echo "built $tag (base $base); use it with TEST_OSS_TOOLS_IMAGE=$tag"
