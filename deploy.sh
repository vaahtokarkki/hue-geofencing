#!/bin/bash
echo "$DOCKER_PASSWORD" | docker login -u "$DOCKER_USERNAME" --password-stdin
touch .env # Fix docker compose build when missing env file
docker-compose build
docker push "$DOCKER_USERNAME"/"$DOCKER_REPO"