#!/bin/bash
set -e

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'

info()    { echo -e "${BLUE}[INFO]${NC}  $1"; }
success() { echo -e "${GREEN}[OK]${NC}      $1"; }
warn()    { echo -e "${YELLOW}[AVISO]${NC} $1"; }
error()   { echo -e "${RED}[ERRO]${NC}   $1"; exit 1; }

REPO_URL="https://github.com/henriquekon/GC_aula06.git"
REPO_DIR="$HOME/receitas-app"
DB_PORT=5432
DB_USER=postgres
DB_NAME=postgres

echo -e "\n${BLUE}========================================${NC}"
echo -e "${BLUE}  Instalador – Sistema de Receitas      ${NC}"
echo -e "${BLUE}========================================${NC}\n"

# Bancos
info "Configuração dos bancos de dados (Supabase)"
echo ""
read -rp "Host do banco de PRODUÇÃO (db.xxx.supabase.co): " DB_HOST_PROD
read -rp "Host do banco de HOMOLOGAÇÃO (db.yyy.supabase.co): " DB_HOST_HOMOLOG
read -rsp "Senha dos bancos (mesma para ambos): " DB_PASSWORD
echo ""

[[ -z "$DB_HOST_PROD" || -z "$DB_HOST_HOMOLOG" || -z "$DB_PASSWORD" ]] && \
  error "Host de produção, host de homologação e senha são obrigatórios."
success "Configuração dos bancos salva."
echo ""

# E-mail
info "Configuração de e-mail para notificações"
echo ""
read -rp "Host SMTP (padrão: smtp.gmail.com): " MAIL_HOST
MAIL_HOST=${MAIL_HOST:-smtp.gmail.com}
read -rp "Porta SMTP (padrão: 587):" MAIL_PORT
MAIL_PORT=${MAIL_PORT:-587}
read -rp "Usuário SMTP: " MAIL_USER
read -rsp "Senha SMTP: " MAIL_PASS
echo ""
read -rp "E-mail remetente (ex: app@receitas.com): " MAIL_FROM
read -rp "E-mail destinatário (quem recebe alertas): " MAIL_TO

[[ -z "$MAIL_USER" || -z "$MAIL_PASS" || -z "$MAIL_FROM" || -z "$MAIL_TO" ]] && \
  error "Todos os campos de e-mail são obrigatórios."
success "Configuração de e-mail salva."
echo ""

# Docker
if ! command -v docker &>/dev/null; then
  info "Instalando Docker..."
  sudo apt update -qq
  sudo apt install -y -qq apt-transport-https ca-certificates curl software-properties-common git
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
    | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
  echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] \
    https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" \
    | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
  sudo apt update -qq
  sudo apt install -y -qq docker-ce docker-ce-cli containerd.io docker-compose-plugin
  sudo systemctl start docker
  sudo systemctl enable docker
  sudo usermod -aG docker "$USER"
  success "Docker instalado."
else
  success "Docker já instalado."
fi

# psql
if ! command -v psql &>/dev/null; then
  info "Instalando cliente PostgreSQL (psql)..."
  sudo apt update -qq
  sudo apt install -y -qq postgresql-client
  success "psql instalado."
else
  success "psql já instalado."
fi

# Repositório
if [ -d "$REPO_DIR/.git" ]; then
  info "Repositório já existe – atualizando..."
  git -C "$REPO_DIR" pull --ff-only
else
  info "Clonando repositório..."
  rm -rf "$REPO_DIR"
  git clone "$REPO_URL" "$REPO_DIR"
fi
success "Repositório pronto em $REPO_DIR"
echo ""

# .env
cat > "$REPO_DIR/.env" <<EOF
MAIL_HOST=${MAIL_HOST}
MAIL_PORT=${MAIL_PORT}
MAIL_USER=${MAIL_USER}
MAIL_PASS=${MAIL_PASS}
MAIL_FROM=${MAIL_FROM}
MAIL_TO=${MAIL_TO}

DB_HOST_PROD=${DB_HOST_PROD}
DB_PORT_PROD=${DB_PORT}
DB_USER_PROD=${DB_USER}
DB_PASSWORD_PROD=${DB_PASSWORD}
DB_NAME_PROD=${DB_NAME}

DB_HOST_HOMOLOG=${DB_HOST_HOMOLOG}
DB_PORT_HOMOLOG=${DB_PORT}
DB_USER_HOMOLOG=${DB_USER}
DB_PASSWORD_HOMOLOG=${DB_PASSWORD}
DB_NAME_HOMOLOG=${DB_NAME}
EOF
success ".env criado."
echo ""

# Migrations
run_migrations() {
  local label="$1"
  local host="$2"

  info "Aplicando migrations no banco de ${label}..."
  for sql_file in "$REPO_DIR"/migrations/V*.sql; do
    [ -f "$sql_file" ] || continue
    info "  → $(basename "$sql_file")"
    PGPASSWORD="$DB_PASSWORD" psql \
      -h "$host" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
      -f "$sql_file" -q
  done
  success "Migrations de ${label} aplicadas."
}

run_migrations "PRODUÇÃO" "$DB_HOST_PROD"
run_migrations "HOMOLOGAÇÃO" "$DB_HOST_HOMOLOG"
echo ""

# Containers
info "Subindo ambiente de PRODUÇÃO (porta 8080)..."
sudo docker compose \
  -f "$REPO_DIR/infra/prod/docker-compose.yml" \
  --env-file "$REPO_DIR/.env" \
  up -d --build
success "Produção no ar."

info "Subindo ambiente de HOMOLOGAÇÃO (porta 8081)..."
sudo docker compose \
  -f "$REPO_DIR/infra/homolog/docker-compose.yml" \
  --env-file "$REPO_DIR/.env" \
  up -d --build
success "Homologação no ar."
echo ""

echo -e "${GREEN}  Instalação concluída!                 ${NC}"
echo ""
echo -e "  Produção:     ${BLUE}http://localhost:8080${NC}"
echo -e "  Homologação:  ${BLUE}http://localhost:8081${NC}"
echo ""
echo -e "  Login:        admin / admin123"
echo -e "  Notificações: ${MAIL_TO}"
echo ""