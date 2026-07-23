#!/bin/bash
cd "$(dirname "$0")/deployment/docker" || exit 1
sudo docker compose up -d --build
echo "--- Live Container Status ---"
sudo docker compose ps
