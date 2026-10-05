#!/usr/bin/env bash
# Перемикає Let's Encrypt на webroot і вмикає автопродовження без даунтайму.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

DOMAIN="${DOMAIN:-tenclinic.com.ua}"
WEBROOT="/var/www/certbot"
RENEW_CONF="/etc/letsencrypt/renewal/${DOMAIN}.conf"
HOOK_DIR="/etc/letsencrypt/renewal-hooks/deploy"
HOOK="${HOOK_DIR}/reload-nginx.sh"
COMPOSE=(docker compose -f docker-compose.yml -f docker-compose.prod.yml)

apt-get update -qq
apt-get install -y certbot
mkdir -p "${WEBROOT}/.well-known/acme-challenge"
mkdir -p "$HOOK_DIR"

cat > "$HOOK" << EOF
#!/usr/bin/env bash
set -euo pipefail
cd "$ROOT_DIR"
docker compose -f docker-compose.yml -f docker-compose.prod.yml exec -T nginx nginx -s reload
EOF
chmod +x "$HOOK"

python3 << PY
from pathlib import Path

path = Path("$RENEW_CONF")
if not path.exists():
    raise SystemExit(f"Немає {path} — спочатку випустіть сертифікат (deploy/ssl/renew-now.sh)")

text = path.read_text()
text = text.replace("authenticator = standalone", "authenticator = webroot")
if "authenticator = webroot" not in text:
    if "[renewalparams]" in text:
        text = text.replace("[renewalparams]", "[renewalparams]\nauthenticator = webroot", 1)
    else:
        text += "\n[renewalparams]\nauthenticator = webroot\n"
if "webroot_path" not in text:
    text = text.replace(
        "[renewalparams]",
        "[renewalparams]\nwebroot_path = $WEBROOT",
        1,
    )
if "[[webroot_map]]" not in text:
    text += "\n[[webroot_map]]\n$DOMAIN = $WEBROOT\nwww.$DOMAIN = $WEBROOT\n"
path.write_text(text)
print(f"==> Оновлено {path}")
PY

systemctl enable --now certbot.timer 2>/dev/null || true

echo "==> Recreate nginx with ACME webroot"
"${COMPOSE[@]}" up -d nginx

echo "==> Dry-run renewal"
certbot renew --dry-run

echo "==> Timers:"
systemctl list-timers --all 2>/dev/null | grep -i certbot || true
echo "==> Auto-renewal ready"
