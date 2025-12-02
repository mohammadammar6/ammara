#!/usr/bin/env bash
set -euo pipefail

# Build and push multi-arch images for the app and custom MySQL image.
# Usage: ensure you're logged into Docker Hub (`docker login`) then run:
#   ./build_and_push_multiarch.sh

IMAGE_APP=devopsusr/ammara:v3
IMAGE_MYSQL=devopsusr/ammara-mysql:v3
PLATFORMS="linux/amd64,linux/arm64"

echo "Using buildx to build multi-arch images: $PLATFORMS"

# create and use a builder if not present
docker buildx create --name multi-builder --use >/dev/null 2>&1 || true
docker buildx inspect --bootstrap

echo "Building and pushing $IMAGE_APP..."
docker buildx build --platform $PLATFORMS -t $IMAGE_APP --push -f Dockerfile .

# echo "Building and pushing $IMAGE_MYSQL..."
# docker buildx build --platform $PLATFORMS -t $IMAGE_MYSQL --push -f Dockerfile.mysql .

echo "Done. Images pushed: $IMAGE_APP" # and $IMAGE_MYSQL"
