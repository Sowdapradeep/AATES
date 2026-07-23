#!/bin/bash
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR" || exit 1

export DOCKER_BUILDKIT=0
export COMPOSE_BAKE=0
export BUILDX_BAKE=0

if [ -f ~/.docker/config.json ]; then
    sed -i 's/"builder": "bake"/"builder": "default"/g' ~/.docker/config.json 2>/dev/null || true
fi

echo "=========================================="
echo " 🛠️  Building AATES Platform Images..."
echo "=========================================="
sudo -E DOCKER_BUILDKIT=0 COMPOSE_BAKE=0 BUILDX_BAKE=0 docker compose -f deployment/docker/docker-compose.yml build

echo ""
echo "=========================================="
echo " 🚀  Launching 5 Containers 24/7..."
echo "=========================================="
sudo -E DOCKER_BUILDKIT=0 COMPOSE_BAKE=0 BUILDX_BAKE=0 docker compose -f deployment/docker/docker-compose.yml up -d

echo ""
echo "=========================================="
echo " 🟢  Live Container Status:"
echo "=========================================="
sudo docker compose -f deployment/docker/docker-compose.yml ps
