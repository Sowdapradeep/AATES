#!/bin/bash
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR" || exit 1

# Install buildx if missing to eliminate Bake warnings
if ! docker buildx version >/dev/null 2>&1; then
    echo "Installing Docker Buildx plugin on EC2..."
    sudo apt-get update -qq && sudo apt-get install -y -qq docker-buildx-plugin >/dev/null 2>&1 || true
fi

echo "Launching AATES Platform containers on AWS EC2..."
sudo docker compose -f deployment/docker/docker-compose.yml up -d --build

echo ""
echo "=== Live Container Status ==="
sudo docker compose -f deployment/docker/docker-compose.yml ps
