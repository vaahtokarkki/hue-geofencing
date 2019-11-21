#!/bin/bash
echo "$DOCKER_PASSWORD" | docker login -u "$DOCKER_USERNAME" --password-stdin
touch .env # Fix docker compose build when missing env file
docker-compose build
docker tag "$DOCKER_REPO":amd64 "$DOCKER_REPO":latest
docker-compose push
docker push "$DOCKER_REPO":latest