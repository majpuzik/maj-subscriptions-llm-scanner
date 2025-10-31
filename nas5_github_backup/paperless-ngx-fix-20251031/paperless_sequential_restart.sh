#!/bin/bash
#
# Paperless-NGX Sequential Restart Script
# Řeší file lock konflikty a zajišťuje zdravý start všech kontejnerů
#
# Použití: sudo bash paperless_sequential_restart.sh
#
# Autor: Claude Code (Anthropic)
# Datum: 31.10.2025
#

cd /volume1/docker/paperless-ngx

echo "╔═══════════════════════════════════════════════════════════╗"
echo "║     PAPERLESS-NGX SEQUENTIAL RESTART                      ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""

# FÁZE 1: ZASTAVENÍ A CLEANUP
echo "=== FÁZE 1: Zastavení všech kontejnerů ==="
sudo /usr/local/bin/docker stop \
  paperless-beat \
  paperless-worker \
  paperless-ngx-webserver-1 \
  paperless-ngx-broker-1 \
  paperless-ngx-db-1

# Odstranění lock souborů
sudo rm -f /volume1/docker/paperless-ngx/data/migration_lock
sudo rm -f /volume1/docker/paperless-ngx/data/celerybeat-schedule.db*

echo "✓ Kontejnery zastaveny, lock soubory odstraněny"
echo ""

# FÁZE 2: POSTUPNÉ SPOUŠTĚNÍ
echo "=== FÁZE 2: Postupné spouštění kontejnerů ==="

echo "1/5 Starting Database..."
sudo /usr/local/bin/docker start paperless-ngx-db-1
sleep 8

echo "2/5 Starting Broker (Redis)..."
sudo /usr/local/bin/docker start paperless-ngx-broker-1
sleep 8

echo "3/5 Starting Webserver (čekám 60s na migrace)..."
sudo /usr/local/bin/docker start paperless-ngx-webserver-1
sleep 60

echo "4/5 Starting Worker (čekám 20s)..."
sudo /usr/local/bin/docker start paperless-worker
sleep 20

echo "5/5 Starting Beat..."
sudo /usr/local/bin/docker start paperless-beat
sleep 15

echo ""

# FÁZE 3: KONTROLA STAVU
echo "=== FÁZE 3: Kontrola stavu ==="
sudo /usr/local/bin/docker ps -a | grep paperless

echo ""
echo "=== HEALTH CHECK (počkejte 30s na inicializaci) ==="
sleep 30

# Health check pro každý kontejner
for container in paperless-ngx-webserver-1 paperless-worker paperless-beat; do
  STATUS=$(sudo /usr/local/bin/docker inspect $container --format='{{.State.Health.Status}}' 2>/dev/null || echo "no health check")
  echo "$container: $STATUS"
done

echo ""
echo "✓ Restart dokončen!"
echo ""
echo "Pro monitoring použijte:"
echo "  sudo /usr/local/bin/docker logs --tail 50 paperless-worker"
echo "  ls -la /volume1/docker/paperless-ngx/consume/"
