#!/bin/bash
set -e

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'

info()    { echo -e "${BLUE}[INFO]${NC}  $1"; }
success() { echo -e "${GREEN}[OK]${NC}      $1"; }
warn()    { echo -e "${YELLOW}[AVISO]${NC} $1"; }
error()   { echo -e "${RED}[ERRO]${NC}   $1"; exit 1; }

echo -e "\n${BLUE}========================================${NC}"
echo -e "${BLUE}  Instalador – Sistema de Receitas      ${NC}"
echo -e "${BLUE}========================================${NC}\n"

info "Configuração de e-mail para notificações"
echo ""

read -rp "  E-mail REMETENTE (ex: app@mailtrap.io):   " MAIL_FROM
read -rp "  E-mail DESTINATÁRIO (quem recebe alerts): " MAIL_TO
read -rp "  Host SMTP (padrão: sandbox.smtp.mailtrap.io): " MAIL_HOST
MAIL_HOST=${MAIL_HOST:-sandbox.smtp.mailtrap.io}
read -rp "  Porta SMTP (padrão: 2525): " MAIL_PORT
MAIL_PORT=${MAIL_PORT:-2525}
read -rp "  Usuário SMTP: " MAIL_USER
read -rsp "  Senha SMTP:   " MAIL_PASS
echo ""

[[ -z "$MAIL_FROM" || -z "$MAIL_TO" || -z "$MAIL_USER" || -z "$MAIL_PASS" ]] && \
  error "Todos os campos de e-mail são obrigatórios."

success "Configuração de e-mail salva."
echo ""

if ! command -v docker &>/dev/null; then
  info "Instalando Docker..."
  sudo apt update -qq
  sudo apt install -y -qq apt-transport-https ca-certificates curl software-properties-common git
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
  echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
  sudo apt update -qq
  sudo apt install -y -qq docker-ce docker-ce-cli containerd.io docker-compose-plugin
  sudo systemctl start docker
  sudo systemctl enable docker
  sudo usermod -aG docker "$USER"
  success "Docker instalado."
else
  success "Docker já instalado."
fi

cat > .env <<EOF
MAIL_HOST=${MAIL_HOST}
MAIL_PORT=${MAIL_PORT}
MAIL_USER=${MAIL_USER}
MAIL_PASS=${MAIL_PASS}
MAIL_FROM=${MAIL_FROM}
MAIL_TO=${MAIL_TO}
EOF
success ".env criado com credenciais de e-mail."

info "Iniciando containers (docker compose up)..."
sudo docker compose --env-file .env up -d --build
success "Containers no ar."

info "Aguardando Postgres inicializar..."
for i in $(seq 1 30); do
  if sudo docker exec my-postgres pg_isready -U postgres -q 2>/dev/null; then
    success "Postgres pronto (${i}s)."
    break
  fi
  sleep 1
done

info "Criando tabelas e populando banco..."
sudo docker exec -w /app create_db pip install -r requirements.txt -q
sudo docker exec -w /app create_db python create_db.py
success "Banco de dados configurado."

echo ""
info "Executando testes unitários..."
echo "──────────────────────────────────────────"

if sudo docker exec -w /app minha-api python -m pytest tests.py -v --tb=short; then
  echo "──────────────────────────────────────────"
  success "Todos os testes passaram! ✓"
else
  echo "──────────────────────────────────────────"
  warn "Alguns testes falharam. Verifique os logs acima."
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Instalação concluída!                 ${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "  Aplicação: ${BLUE}http://localhost${NC}"
echo -e "  API:       ${BLUE}http://localhost/api/receitas${NC}"
echo -e "  Login:     admin / admin123"
echo ""