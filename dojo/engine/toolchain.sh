#!/usr/bin/env bash
# Install / check the lab toolchains (SPEC §4 Language rule). Idempotent; safe to run every job.
#   Scala 3.3 LTS from the GitHub release tarball (Maven Central is not reachable from the cloud,
#   so Scala labs use the standard library only).  Rust via the preinstalled cargo (crates.io works).
set -euo pipefail
SCALA_VERSION="${SCALA_VERSION:-3.3.4}"
PREFIX="${DOJO_TOOLS:-$HOME/.local/dojo-tools}"
SCALA_HOME="$PREFIX/scala3-$SCALA_VERSION"
mkdir -p "$PREFIX"
if [ ! -x "$SCALA_HOME/bin/scala" ]; then
  curl -sSL --retry 2 --max-time 300 -o "$PREFIX/scala3.tgz" \
    "https://github.com/scala/scala3/releases/download/$SCALA_VERSION/scala3-$SCALA_VERSION.tar.gz"
  tar -xzf "$PREFIX/scala3.tgz" -C "$PREFIX" 2>/dev/null
  rm -f "$PREFIX/scala3.tgz"
fi
echo "scala: $SCALA_HOME/bin/scala"
if command -v cargo >/dev/null 2>&1; then echo "cargo: $(command -v cargo) ($(cargo --version))"
else echo "cargo: MISSING — Rust labs cannot be verified in this run"; fi
