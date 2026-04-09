#!/bin/bash
set -e

IMAGE="racoolstudio/grafana-synthetic-data"

echo "================================================"
echo "  Pushing to Docker Hub: $IMAGE"
echo "================================================"

echo ""
echo "Tagging as latest and v1.0..."
/usr/local/bin/docker tag $IMAGE:latest $IMAGE:v1.0

echo ""
echo "Pushing latest..."
/usr/local/bin/docker push $IMAGE:latest

echo ""
echo "Pushing v1.0..."
/usr/local/bin/docker push $IMAGE:v1.0

echo ""
echo "================================================"
echo "  Done!"
echo "  https://hub.docker.com/r/$IMAGE"
echo ""
echo "  Anyone can now run:"
echo "  docker compose -f docker-compose.hub.yml up -d"
echo "================================================"
