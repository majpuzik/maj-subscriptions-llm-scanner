# Export/Import Workflow - Persistence klasifikací

## Problém
Po klasifikaci emailů v HTML UI se klasifikace ukládají do **localStorage** prohlížeče, ale **NE do databáze**.

Při dalším spuštění `test_marketing_detector_grouped.py`:
- Vytvoří se nový HTML soubor ✅
- localStorage je prázdný ❌
- Systém se ptá na stejné skupiny znovu ❌

**Příklad:**
- Klasifikuješ "Kopp Report" jako MARKETING
- Zobrazí se ✓ (zaškrtnuto v localStorage)
- Příští den: Spustíš znovu → "Kopp Report" se objeví znovu

## Řešení: Export → Import → Smart Matching

### Krok 1: Klasifikace v HTML UI
```
1. Otevři: marketing_test_results_grouped.html
2. Projdi skupiny a klikni MKT/NOT
3. Klasifikace se ukládají do localStorage
```

### Krok 2: Export klasifikací
```
1. Klikni na tlačítko "Export JSON"
2. Stáhne se: marketing_classifications_with_metadata.json
```

**Formát JSON:**
```json
{
  "139": {
    "is_marketing": true,
    "sender": "Kopp Report <noreply@kopp-report.de>",
    "subject": "Lagebericht",
    "count": 40
  },
  "187": {
    "is_marketing": true,
    "sender": "Ignacio de Gregorio Noblejas <ignacio@thealgorithmicbridge.com>",
    "subject": "The Algorithmic Bridge",
    "count": 40
  }
}
```

### Krok 3: Import do databáze
```bash
cd ~/apps/maj-subscriptions-local
python3 import_classifications_from_json.py ~/Downloads/marketing_classifications_with_metadata.json
```

**Výstup:**
```
📥 Načítám JSON soubor: ~/Downloads/marketing_classifications_with_metadata.json
✓ Načteno 45 záznamů z JSON

  Importováno 10...
  Importováno 20...
  Importováno 30...
  Importováno 40...

============================================================
✅ Import dokončen!
  Importováno: 45
  Přeskočeno: 0
  Chyby: 0
============================================================

🔍 Pro ověření spusť:
  sqlite3 /Users/m.a.j.puzik/apps/maj-subscriptions-local/data/subscriptions.db "SELECT COUNT(*) FROM email_classifications WHERE source='manual_import'"
```

### Krok 4: Smart Matching při dalším spuštění
Při dalším spuštění `python3 test_marketing_detector_grouped.py`:

1. **Načte klasifikace z DB** → včetně sender informací
2. **Smart matching** → porovná sendery nových skupin s DB
3. **Auto-aplikuje** klasifikaci, pokud sender sedí

**Matching logika:**
```python
# Exact match
"Kopp Report <noreply@kopp-report.de>" == "Kopp Report <noreply@kopp-report.de>" ✅

# Partial match (email extraction)
"noreply@kopp-report.de" in "Kopp Report <noreply@kopp-report.de>" ✅
```

**Výsledek:**
```
🔍 Smart matching podle senderu...
✓ Aplikováno 45 klasifikací z DB (podle senderu)

🤖 Auto-klasifikace TOP skupin...
✓ Automaticky klasifikováno 5 NOVÝCH skupin

📊 STATISTIKY:
  Celkem emailů: 5000
  Skupin: 235
  Už klasifikovaných: 50 (21.3%)
  Zbývá klasifikovat: 185 (78.7%)
```

## Automatizace

### Vytvoř alias pro rychlý export
```bash
# Přidej do ~/.zshrc
alias export-mkt="open ~/apps/maj-subscriptions-local/marketing_test_results_grouped.html && echo 'Klikni Export JSON po dokončení klasifikace'"
```

### Vytvoř alias pro import
```bash
# Přidej do ~/.zshrc
alias import-mkt="python3 ~/apps/maj-subscriptions-local/import_classifications_from_json.py ~/Downloads/marketing_classifications_with_metadata.json && rm ~/Downloads/marketing_classifications_with_metadata.json"
```

### Workflow s aliasy
```bash
# 1. Klasifikuj
export-mkt

# 2. Po exportu importuj
import-mkt

# 3. Spusť znovu (už bez opakování)
cd ~/apps/maj-subscriptions-local
python3 test_marketing_detector_grouped.py
```

## Ověření fungování

### Zkontroluj DB před importem
```bash
sqlite3 ~/apps/maj-subscriptions-local/data/subscriptions.db \
  "SELECT COUNT(*) FROM email_classifications WHERE sender LIKE '%kopp%'"
# Výsledek: 0 (ještě není v DB)
```

### Proveď import
```bash
python3 import_classifications_from_json.py ~/Downloads/marketing_classifications_with_metadata.json
```

### Zkontroluj DB po importu
```bash
sqlite3 ~/apps/maj-subscriptions-local/data/subscriptions.db \
  "SELECT sender, is_marketing, source FROM email_classifications WHERE sender LIKE '%kopp%'"
# Výsledek:
# Kopp Report <noreply@kopp-report.de>|1|manual_import
```

### Spusť znovu a zkontroluj matching
```bash
python3 test_marketing_detector_grouped.py | grep -i kopp
# Očekávaný výsledek:
# ✓ Smart matching nalezl "Kopp Report" jako MARKETING
# (skupina se už nezobrazí mezi unclassified)
```

## Výhody tohoto řešení

1. ✅ **Persistence** - Klasifikace se ukládají do DB
2. ✅ **Smart matching** - Automaticky rozpozná stejné sendery
3. ✅ **Flexibilita** - Můžeš klasifikaci změnit (re-import přepíše)
4. ✅ **Historie** - Vidíš kdy a jak byla klasifikace uložena (source: manual_import)
5. ✅ **Škálovatelnost** - Funguje i pro tisíce klasifikací

## Možné budoucí vylepšení

### 1. Automatický DB save při kliku na MKT/NOT
Místo export/import workflow přidat API endpoint:
```javascript
function classify(groupId, isMarketing) {
    // Uložit do localStorage
    classifications[groupId] = isMarketing;

    // Uložit do DB přes API
    fetch('/api/classify', {
        method: 'POST',
        body: JSON.stringify({
            group_id: groupId,
            is_marketing: isMarketing,
            sender: groupsMetadata[groupId].sender,
            subject: groupsMetadata[groupId].subject
        })
    });
}
```

### 2. Real-time synchronizace
WebSocket pro live update mezi UI a DB.

### 3. Multi-user podpora
Sdílená DB mezi více uživateli/zařízeními.

## Troubleshooting

### Problém: Import hlásí "chybí metadata"
**Příčina:** Starý formát JSON (jen boolean místo objektu)

**Řešení:** Re-exportuj z nového HTML (s groups_metadata)

### Problém: Smart matching nenachází sendery
**Příčina:** Sender v DB se liší od senderu v nových emailech

**Řešení:**
```bash
# Zkontroluj jak vypadají sendery v DB
sqlite3 ~/apps/maj-subscriptions-local/data/subscriptions.db \
  "SELECT DISTINCT sender FROM email_classifications LIMIT 10"

# Porovnej s sendery v emailech
sqlite3 ~/apps/maj-subscriptions-local/data/subscriptions.db \
  "SELECT DISTINCT email_from FROM emails LIMIT 10"
```

### Problém: Přepsání existujících klasifikací
**Příčina:** `INSERT OR REPLACE` přepíše i když už existuje

**Řešení:** Nejdříve zkontroluj co už je v DB:
```bash
sqlite3 ~/apps/maj-subscriptions-local/data/subscriptions.db \
  "SELECT COUNT(*) FROM email_classifications"
```
