#!/bin/bash
# Build stub JAR for Java EE and Jakarta dependencies

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
SRC_DIR="$SCRIPT_DIR/src"
BUILD_DIR="$SCRIPT_DIR/build"
JAR_FILE="$SCRIPT_DIR/stubs.jar"

echo "Building stub classes..."

# Clean build directory
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"

# Find all Java files and compile them
find "$SRC_DIR" -name "*.java" -print0 | xargs -0 javac -d "$BUILD_DIR"

# Create JAR
echo "Creating JAR..."
cd "$BUILD_DIR"
jar cf "$JAR_FILE" .

echo "✓ Stub JAR created: $JAR_FILE"
ls -lh "$JAR_FILE"
