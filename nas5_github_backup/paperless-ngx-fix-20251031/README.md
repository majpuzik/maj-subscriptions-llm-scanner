# Paperless-NGX Fix - FileNotFoundError a Container Health

**Datum:** 31. října 2025  
**Status:** ✅ Production-ready

## 📦 Obsah Balíčku

1. **PAPERLESS_FIX_DOCUMENTATION.md** - Kompletní dokumentace problému a řešení
2. **paperless_sequential_restart.sh** - Restart script pro správný sekvenční start
3. **README.md** - Tento soubor

## 🎯 Rychlý Přehled

### Problém:
- Dokumenty selhávaly s `FileNotFoundError` po 17+ minutách OCR
- Kontejnery unhealthy kvůli file lock konfliktům

### Řešení:
- ✅ Odstraněno file renaming z pre-consume scriptu
- ✅ Implementován sekvenční restart kontejnerů
- ✅ Všechny kontejnery nyní healthy a zpracovávají bez chyb

## 🚀 Použití

### Restart Paperless-NGX:
```bash
cd /volume1/docker/paperless-ngx
sudo bash paperless_sequential_restart.sh
```

### Kontrola stavu:
```bash
sudo /usr/local/bin/docker ps | grep paperless
sudo /usr/local/bin/docker logs --tail 50 paperless-worker
```

## 📍 Umístění Souborů

### Na Produkci (NAS4):
- Script: `/volume1/docker/paperless-ngx/scripts/pre_consume_classify.sh`
- Backup: `/volume1/docker/paperless-ngx/scripts/pre_consume_classify.sh.backup-20251031-192846`

### Backup (NAS5):
- `/volume1/docker/paperless-ngx-fix-backup-20251031/`
- `/volume1/apps/paperless-ngx-fix-backup-20251031/`
- Git: `~/nas5_github_backup/paperless-ngx-fix-20251031/`

## ✅ Verifikace

Po implementaci:
- Všechny kontejnery: **Healthy** ✓
- Worker zpracovává: **6+ docs/hod** ✓
- FileNotFoundError: **0** ✓
- Průměrný čas: **5-6 min/dokument** ✓

---

Pro detaily viz **PAPERLESS_FIX_DOCUMENTATION.md**
