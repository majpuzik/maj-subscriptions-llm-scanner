#!/bin/bash
cd /volume1/docker/paperless-ngx

echo "╔═══════════════════════════════════════════════════════════╗"
echo "║     SEKVENČNÍ RESTART PAPERLESS-NGX                       ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""

echo "=== FÁZE 1: ZASTAVENÍ ==="
sudo /usr/local/bin/docker stop paperless-beat paperless-worker paperless-ngx-webserver-1 paperless-ngx-broker-1 paperless-ngx-db-1
sudo rm -f /volume1/docker/paperless-ngx/data/migration_lock
sudo rm -f /volume1/docker/paperless-ngx/data/celerybeat-schedule.db*
echo "✓ Zastaveno a vyčištěno"
echo ""

echo "=== FÁZE 2: POSTUPNÉ SPOUŠTĚNÍ ==="
echo "1/5 DB..."
sudo /usr/local/bin/docker start paperless-ngx-db-1
sleep 8

echo "2/5 Broker..."
sudo /usr/local/bin/docker start paperless-ngx-broker-1
sleep 8

echo "3/5 Webserver (čekám 60s)..."
sudo /usr/local/bin/docker start paperless-ngx-webserver-1
sleep 60

echo "4/5 Worker (čekám 20s)..."
sudo /usr/local/bin/docker start paperless-worker
sleep 20

echo "5/5 Beat..."
sudo /usr/local/bin/docker start paperless-beat
sleep 15

echo ""
echo "=== FÁZE 3: KONTROLA ==="
sudo /usr/local/bin/docker ps -a | grep paperless
