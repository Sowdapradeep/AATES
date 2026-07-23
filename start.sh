#!/bin/bash
cd deployment/docker
sudo docker compose up -d --build || sudo docker-compose up -d --build
sudo docker compose ps || sudo docker-compose ps
