#!/bin/bash
# Main build script for Hearth .deb package

# Get version from file (removing 'v' prefix if present)
VERSION=$(cat VERSION | tr -d 'v' | xargs)
echo "Building Hearth version ${VERSION}..."

# Ensure binary is in the correct place for nfpm
# (Note: PyInstaller built it into backend/dist/hearth)

# Run nfpm
export VERSION=${VERSION}
./nfpm pkg --target hearth_${VERSION}_amd64.deb

echo "Build complete: hearth_${VERSION}_amd64.deb"
