#!/bin/bash

# Script de setup para VM Ubuntu zerada

echo -e "Instalando Docker"
sudo apt install -y apt-transport-https ca-certificates curl software-properties-common

curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Adicionar usuário ao grupo docker
sudo usermod -aG docker $USER

echo -e "Instalando Git"
sudo apt install -y git

echo -e "Clonando repositório"
git clone https://github.com/seu-usuario/docker-demo-aula.git
cd docker-demo-aula

echo -e "Subindo containers"
docker compose up -d

echo -e "Status:"
docker compose ps
