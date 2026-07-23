#!/bin/bash
sudo docker compose -f deployment/docker/docker-compose.yml up -d --build
sudo docker compose -f deployment/docker/docker-compose.yml ps
