#!/usr/bin/env bash
set -euo pipefail

VERSION="v3.16.4"
BIN_DIR="${1:-.bin}"
RAW_OS="$(uname -s | tr '[:upper:]' '[:lower:]')"
RAW_ARCH="$(uname -m)"

case "$RAW_ARCH" in
  x86_64) ARCH="amd64" ;;
  aarch64|arm64) ARCH="arm64" ;;
  *) echo "unsupported arch: $RAW_ARCH" >&2; exit 1 ;;
esac

case "$RAW_OS" in
  linux|darwin) OS="$RAW_OS" ;;
  *) echo "unsupported os: $RAW_OS" >&2; exit 1 ;;
esac

mkdir -p "$BIN_DIR"
TARGET="$BIN_DIR/helm"
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

ARCHIVE="helm-${VERSION}-${OS}-${ARCH}.tar.gz"
URL="https://get.helm.sh/${ARCHIVE}"
SHA_URL="${URL}.sha256"

curl -fsSL "$URL" -o "$TMP_DIR/$ARCHIVE"
curl -fsSL "$SHA_URL" -o "$TMP_DIR/$ARCHIVE.sha256"
EXPECTED="$(cat "$TMP_DIR/$ARCHIVE.sha256" | tr -d '[:space:]')"
ACTUAL="$(sha256sum "$TMP_DIR/$ARCHIVE" | awk '{print $1}')"

if [[ "$EXPECTED" != "$ACTUAL" ]]; then
  echo "checksum mismatch for $ARCHIVE" >&2
  exit 1
fi

tar -xzf "$TMP_DIR/$ARCHIVE" -C "$TMP_DIR"
install -m 0755 "$TMP_DIR/$OS-$ARCH/helm" "$TARGET"

INSTALLED="$($TARGET version --short | sed 's/^v\([0-9.]*\).*/v\1/')"
if [[ "$INSTALLED" != "$VERSION" ]]; then
  echo "version verification failed: expected $VERSION got $INSTALLED" >&2
  exit 1
fi

echo "helm $VERSION installed to $TARGET"
