#!/usr/bin/env bash
set -euo pipefail

VERSION="0.57.0"
BIN_DIR="${1:-.bin}"
RAW_OS="$(uname -s)"
RAW_ARCH="$(uname -m)"

case "$RAW_OS" in
  Linux) OS="Linux" ;;
  Darwin) OS="Darwin" ;;
  *) echo "unsupported os: $RAW_OS" >&2; exit 1 ;;
esac

case "$RAW_ARCH" in
  x86_64) ARCH="x86_64" ;;
  aarch64|arm64) ARCH="arm64" ;;
  *) echo "unsupported arch: $RAW_ARCH" >&2; exit 1 ;;
esac

mkdir -p "$BIN_DIR"
TARGET="$BIN_DIR/conftest"
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

ARCHIVE="conftest_${VERSION}_${OS}_${ARCH}.tar.gz"
BASE_URL="https://github.com/open-policy-agent/conftest/releases/download/v${VERSION}"

curl -fsSL "$BASE_URL/$ARCHIVE" -o "$TMP_DIR/$ARCHIVE"
curl -fsSL "$BASE_URL/checksums.txt" -o "$TMP_DIR/checksums.txt"

EXPECTED="$(grep "$ARCHIVE$" "$TMP_DIR/checksums.txt" | awk '{print $1}')"
ACTUAL="$(sha256sum "$TMP_DIR/$ARCHIVE" | awk '{print $1}')"

if [[ -z "$EXPECTED" ]]; then
  echo "failed to resolve checksum for $ARCHIVE" >&2
  exit 1
fi

if [[ "$EXPECTED" != "$ACTUAL" ]]; then
  echo "checksum mismatch for $ARCHIVE" >&2
  echo "expected: $EXPECTED" >&2
  echo "actual:   $ACTUAL" >&2
  exit 1
fi

tar -xzf "$TMP_DIR/$ARCHIVE" -C "$TMP_DIR"
install -m 0755 "$TMP_DIR/conftest" "$TARGET"

INSTALLED="$($TARGET --version | awk 'NR==1 {print $2}')"
if [[ "$INSTALLED" != "$VERSION" ]]; then
  echo "version verification failed: expected $VERSION got $INSTALLED" >&2
  exit 1
fi

echo "conftest v$VERSION installed to $TARGET"
