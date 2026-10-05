#!/usr/bin/env bash
# Разовий перевипуск Let's Encrypt (standalone). Nginx зупиняється на ~1–2 хв.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

COMPOSE=(docker compose -f docker-compose.yml -f docker-compose.prod.yml)
DOMAIN="${DOMAIN:-tenclinic.com.ua}"

apt-get update -qq
apt-get install -y certbot

echo "==> Stop nginx (port 80 needed for standalone)"
"${COMPOSE[@]}" stop nginx

set +e
certbot certonly --standalone --agree-tos --non-interactive \
  --keep-until-expiring --expand \
  -d "$DOMAIN" -d "www.$DOMAIN"
STATUS=$?
set -e

echo "==> Start nginx"
"${COMPOSE[@]}" start nginx

if [[ "$STATUS" -ne 0 ]]; then
  echo "FATAL: certbot failed ($STATUS)"
  exit "$STATUS"
fi

echo "==> Certificate:"
openssl x509 -in "/etc/letsencrypt/live/${DOMAIN}/fullchain.pem" -noout -dates -subject
echo "==> Done"
