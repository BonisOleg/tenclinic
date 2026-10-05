#!/usr/bin/env bash
# Одноразовий bootstrap для Droplet 104.248.31.202 / tenclinic.com.ua
# Запуск на сервері: bash deploy/docker/bootstrap-droplet.sh
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

if [[ ! -f .env ]]; then
  cp .env.docker.example .env
  echo ""
  echo "Створено .env — ОБОВ'ЯЗКОВО відредагуй перед продовженням:"
  echo "  SECRET_KEY, DB_PASSWORD, DJANGO_SUPERUSER_PASSWORD"
  echo ""
  echo "  nano .env"
  exit 1
fi

bash deploy/docker/install-docker.sh
bash deploy/docker/deploy.sh

echo ""
echo "==> Перевірка"
curl -sf "http://127.0.0.1/healthz/" && echo " healthz OK"
curl -sI "http://127.0.0.1/static/images/hero-bg.jpg" | head -1
echo ""
echo "Сайт: http://104.248.31.202/"
echo "Адмінка: http://104.248.31.202/admin/"
echo ""
echo "Після DNS propagation — SSL:"
echo "  bash deploy/ssl/renew-now.sh"
echo "  # .env: USE_HTTPS=true"
echo "  USE_HTTPS=true bash deploy/docker/deploy.sh"
echo "  bash deploy/ssl/setup-renewal.sh"
