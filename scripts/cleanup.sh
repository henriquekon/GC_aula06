#!/bin/bash

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'

info()    { echo -e "${BLUE}[INFO]${NC}  $1"; }
success() { echo -e "${GREEN}[OK]${NC}      $1"; }
warn()    { echo -e "${YELLOW}[AVISO]${NC} $1"; }

echo -e "${YELLOW} Limpeza – VM ${NC}"

warn "Isso vai remover containers, imagens, volumes, Docker, psql e o repositório."
read -rp "Tem certeza? (s/N): " CONFIRM
[[ "$CONFIRM" != "s" && "$CONFIRM" != "S" ]] && echo "Cancelado." && exit 0
echo ""

# Containers e imagens
if command -v docker &>/dev/null; then
  info "Derrubando containers..."
  sudo docker compose \
    -f "$HOME/receitas-app/infra/prod/docker-compose.yml" \
    down --volumes 2>/dev/null || true
  sudo docker compose \
    -f "$HOME/receitas-app/infra/homolog/docker-compose.yml" \
    down --volumes 2>/dev/null || true

  info "Removendo containers restantes..."
  sudo docker ps -aq | xargs -r sudo docker rm -f 2>/dev/null || true

  info "Removendo imagens..."
  sudo docker images -q | xargs -r sudo docker rmi -f 2>/dev/null || true

  info "Removendo volumes..."
  sudo docker volume ls -q | xargs -r sudo docker volume rm 2>/dev/null || true

  info "Removendo redes criadas..."
  sudo docker network prune -f 2>/dev/null || true

  info "Desinstalando Docker..."
  sudo apt purge -y -qq docker-ce docker-ce-cli containerd.io docker-compose-plugin
  sudo rm -rf /var/lib/docker /etc/docker
  sudo rm -f /usr/share/keyrings/docker-archive-keyring.gpg
  sudo rm -f /etc/apt/sources.list.d/docker.list
  sudo apt autoremove -y -qq
  success "Docker removido."
else
  warn "Docker não estava instalado."
fi

# psql
if command -v psql &>/dev/null; then
  info "Desinstalando psql..."
  sudo apt purge -y -qq postgresql-client
  sudo apt autoremove -y -qq
  success "psql removido."
else
  warn "psql não estava instalado."
fi

# Firewall
info "Removendo regras de firewall..."
sudo ufw delete allow 8080/tcp 2>/dev/null || true
sudo ufw delete allow 8081/tcp 2>/dev/null || true
success "Regras removidas."

# Repositório
if [ -d "$HOME/receitas-app" ]; then
  info "Removendo repositório..."
  rm -rf "$HOME/receitas-app"
  success "Repositório removido."
else
  warn "Repositório não encontrado."
fi

# .env solto na home se existir
rm -f "$HOME/.env" 2>/dev/null || true

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Limpeza concluída!                    ${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
warn "Os bancos do Neon NÃO foram alterados."
warn "Para resetar o banco, acesse neon.tech e apague as tabelas manualmente."
echo ""