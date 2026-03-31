#!/bin/bash

sudo apt update
sudo apt install -y docker.io docker-compose-plugin git

sudo systemctl start docker
sudo systemctl enable docker

sudo usermod -aG docker $USER

git clone git@github.com:henriquekon/GC_aula06.git
cd GC_aula06

sudo docker compose up -d