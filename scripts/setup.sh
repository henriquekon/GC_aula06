#!/bin/bash

sudo apt update
sudo apt install -y apt-transport-https ca-certificates curl software-properties-common git

curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

sudo systemctl start docker
sudo systemctl enable docker

sudo usermod -aG docker $USER

rm -rf GC_aula06
git clone https://github.com/henriquekon/GC_aula06.git
cd GC_aula06

sudo docker compose up -d

sleep 10 # esperar Postgres

sudo docker exec create_db pip install -r /app/requirements.txt
sudo docker exec create_db python /app/create_db.py