# Marketing Email Detector & Classifier

Systém pro automatickou detekci a klasifikaci marketingových emailů s pokročilým AI skóringem a smart matching.

## 📋 Obsah

- [Přehled](#přehled)
- [Funkce](#funkce)
- [Instalace](#instalace)
- [Použití](#použití)
- [Architektura](#architektura)
- [Workflow](#workflow)
- [Troubleshooting](#troubleshooting)

---

## 🎯 Přehled

Marketing Email Detector je komplexní systém pro:
- ✅ Detekci marketingových emailů pomocí AI/pravidel
- ✅ Seskupování podobných emailů
- ✅ Interaktivní HTML UI pro manuální klasifikaci
- ✅ Smart matching podle senderu (opakované klasifikace)
- ✅ Whitelist/Blacklist integrace
- ✅ Export/Import workflow pro persistenci
- ✅ Automatická klasifikace TOP skupin

---

## 🚀 Funkce

### 1. AI Marketing Detection
**Soubor:** `marketing_email_detector.py`

**Detekční algoritmus:**
- Marketingové klíčové fráze v předmětu (25 bodů)
- Marketingové domény odesílatelů (20 bodů)
- Unsubscribe odkazy (30 bodů - silný indikátor)
- Marketingové fráze v těle (15 bodů)
- HTML analýza - odkazy a obrázky (10 bodů)
- Tracking elementy (5 bodů)

**Threshold:** 40 bodů = MARKETING

**Whitelist/Blacklist:**
- Whitelist: -20 bodů (bonus, ale POŘÁD testuje markery!)
- Blacklist: +60 bodů (silný indikátor marketingu)

### 2. Email Grouping
**Soubor:** `test_marketing_detector_grouped.py`

Seskupuje emaily podle:
- Exact sender match
- Subscription keywords (subject normalizace)

**Příklad:**
```
407× "mobile.de Suchauftrag" <noreply@dein.mobile.de>
     - 🚘 1 neues Fahrzeug für dich
     - 🚘 2 neue Fahrzeuge für dich
     - 🚘 3 neue Fahrzeuge für dich
     → 1 skupina, 407 emailů
```

### 3. Smart Sender Matching
**Funkce:** `apply_sender_classification()`

Při novém spuštění:
1. Načte klasifikace z DB (včetně senderů)
2. Porovná sendery nových skupin s DB
3. Auto-aplikuje klasifikaci, pokud sender sedí

**Matching logika:**
```python
# Exact match
"Kopp Report <noreply@kopp-report.de>" == "Kopp Report <noreply@kopp-report.de>" ✅

# Partial match (email extraction)
db_email = "noreply@kopp-report.de"
current_email = "noreply@kopp-report.de"
if db_email in current_email or current_email in db_email: ✅
```

### 4. Auto-Classification TOP Groups
**Funkce:** `auto_classify_top_groups()`

Automaticky klasifikuje:
- `mobile.de` → MARKETING
- `autoscout24` → MARKETING
- `immowelt` → MARKETING

Ale jen ty, co **ještě nejsou** v DB!

### 5. Interactive HTML UI
**Výstup:** `marketing_test_results_grouped.html`

**Funkce:**
- 🔴 MKT tlačítko → označí jako MARKETING
- 🟢 NOT tlačítko → označí jako NOT MARKETING
- ✓ Háček → již klasifikováno
- 📤 Export JSON → stáhne klasifikace s metadaty
- 📥 Export CSV → stáhne v CSV formátu

**Filtry:**
- **All** - všechny skupiny
- **Unclassified** (default) - jen neklasifikované
- **Classified** - jen klasifikované
- **Marketing** - jen marketing
- **Not Marketing** - jen ne-marketing

---

## 📦 Instalace

### Požadavky
```bash
python3 >= 3.8
sqlite3
```

### Závislosti
```bash
pip3 install email-validator
# Všechny ostatní jsou standardní knihovny
```

### Struktur adresářů
```
~/apps/maj-subscriptions-local/
├── data/
│   └── subscriptions.db          # SQLite databáze
├── marketing_email_detector.py   # Core detekční algoritmus
├── test_marketing_detector_grouped.py  # Hlavní script s UI
├── import_classifications_from_json.py # Import script
├── email_lists.py                # Whitelist/Blacklist
├── email_whitelist.json          # Whitelist data
├── email_blacklist.json          # Blacklist data
└── marketing_test_results_grouped.html  # Generované UI
```

---

## 🎮 Použití

### Základní workflow

#### 1. První spuštění
```bash
cd ~/apps/maj-subscriptions-local
python3 test_marketing_detector_grouped.py
```

**Výstup:**
```
📧 Načítám emaily...
✓ Načteno 5000 emailů

📦 Seskupuji podobné emaily...
✓ Vytvořeno 235 skupin

🔍 Smart matching podle senderu...
✓ Aplikováno 11 klasifikací z DB (podle senderu)

🤖 Auto-klasifikace TOP skupin...
✓ Automaticky klasifikováno 5 NOVÝCH skupin

📊 STATISTIKY:
  Celkem emailů: 5000
  Skupin: 235
  Marketing skupin: 176 (74.9%)
  Už klasifikovaných: 16 (6.8%)
  Zbývá klasifikovat: 219 (93.2%)

🎨 Generuji HTML rozhraní...
✅ HTML vygenerováno: marketing_test_results_grouped.html
```

#### 2. Otevři HTML a klasifikuj
```bash
open ~/apps/maj-subscriptions-local/marketing_test_results_grouped.html
```

**V prohlížeči:**
1. Projdi skupiny (default: jen Unclassified)
2. Klikni 🔴 MKT nebo 🟢 NOT
3. Skupina dostane ✓ (uloženo do localStorage)

#### 3. Export klasifikací
1. Klikni **"Export JSON"**
2. Stáhne se: `marketing_classifications_with_metadata.json`

**Formát:**
```json
{
  "139": {
    "is_marketing": true,
    "sender": "Kopp Report <noreply@kopp-report.de>",
    "subject": "Lagebericht",
    "count": 40
  }
}
```

#### 4. Import do databáze
```bash
./import_classifications_from_json.py ~/Downloads/marketing_classifications_with_metadata.json
```

**Výstup:**
```
📥 Načítám JSON soubor...
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
```

#### 5. Příští spuštění (smart matching!)
```bash
python3 test_marketing_detector_grouped.py
```

**Co se stane:**
```
🔍 Smart matching podle senderu...
✓ Aplikováno 56 klasifikací z DB (podle senderu)  ← Našel tvoje klasifikace!

📊 STATISTIKY:
  Už klasifikovaných: 61 (25.9%)  ← Více než předtím!
  Zbývá klasifikovat: 174 (74.1%)  ← Méně práce!
```

**Výsledek:** Kopp Report, Ignacio de Gregorio, CNET Mobile atd. **UŽ NEVIDÍŠ** v unclassified! ✅

---

## 🏗️ Architektura

### Databázové schéma

```sql
CREATE TABLE email_classifications (
    group_id INTEGER PRIMARY KEY,
    sender TEXT,                    -- "Kopp Report <noreply@kopp-report.de>"
    subject_pattern TEXT,           -- "Lagebericht"
    is_marketing INTEGER,           -- 1 = marketing, 0 = not marketing
    classified_at TEXT,             -- ISO timestamp
    source TEXT                     -- 'auto', 'sender_match', 'manual_import'
);
```

### Classification Sources

| Source | Popis | Příklad |
|--------|-------|---------|
| `auto` | Auto-klasifikace (mobile.de, autoscout24) | Pattern matching |
| `sender_match` | Smart matching (exact sender) | Exact string match |
| `sender_partial_match` | Smart matching (email extraction) | Email v email |
| `manual_import` | Importováno z JSON | User klasifikace |

### Data Flow

```
┌─────────────────┐
│  SQLite DB      │
│  - emails       │
│  - classif.     │
└────────┬────────┘
         │
         ↓
┌─────────────────────────────────────────┐
│ test_marketing_detector_grouped.py      │
│ 1. Load emails (5000)                   │
│ 2. Group by sender                      │
│ 3. Smart matching (DB → groups)         │
│ 4. Auto-classify TOP (mobile.de, etc)   │
│ 5. AI analyze (marketing_email_detector)│
│ 6. Generate HTML UI                     │
└────────┬────────────────────────────────┘
         │
         ↓
┌─────────────────────────────────────────┐
│ marketing_test_results_grouped.html     │
│ - localStorage (temp classifications)   │
│ - MKT/NOT buttons                       │
│ - Export JSON (with metadata!)          │
└────────┬────────────────────────────────┘
         │
         ↓
┌─────────────────────────────────────────┐
│ marketing_classifications_...json       │
│ {group_id: {sender, subject, ...}}      │
└────────┬────────────────────────────────┘
         │
         ↓
┌─────────────────────────────────────────┐
│ import_classifications_from_json.py     │
│ Parse JSON → Save to DB                 │
└────────┬────────────────────────────────┘
         │
         ↓
┌─────────────────┐
│  SQLite DB      │
│  + new classif. │
└─────────────────┘
```

---

## 🔄 Workflow Diagram

```
START
  │
  ├─→ 1. python3 test_marketing_detector_grouped.py
  │      │
  │      ├─→ Load 5000 emails from DB
  │      ├─→ Group by sender (235 groups)
  │      ├─→ Smart matching (11 klasifikací z DB)
  │      ├─→ Auto-classify TOP (5 nových)
  │      ├─→ AI analyze (marketing score)
  │      └─→ Generate HTML UI
  │
  ├─→ 2. open marketing_test_results_grouped.html
  │      │
  │      ├─→ Default filter: Unclassified (219 groups)
  │      ├─→ User klikne MKT/NOT
  │      ├─→ localStorage.setItem('group_123', true)
  │      └─→ Zobrazí ✓ (classified)
  │
  ├─→ 3. Click "Export JSON"
  │      │
  │      └─→ Download: marketing_classifications_with_metadata.json
  │
  ├─→ 4. ./import_classifications_from_json.py ~/Downloads/...json
  │      │
  │      ├─→ Parse JSON (45 záznamů)
  │      ├─→ For each: save_classification(group_id, sender, subject, is_marketing)
  │      └─→ DB: INSERT OR REPLACE INTO email_classifications
  │
  └─→ 5. python3 test_marketing_detector_grouped.py (ZNOVU)
         │
         ├─→ Smart matching (56 klasifikací z DB!)  ← NAŠEL TVOJE!
         ├─→ Auto-classify TOP (0 nových - už jsou v DB)
         └─→ Unclassified: 174 groups (místo 219!)  ← MÉNĚ PRÁCE!
```

---

## 📝 Konfigurace

### Email limit
**Soubor:** `test_marketing_detector_grouped.py:42`
```python
emails = load_emails(limit=5000)  # Změň na 10000, 20000, etc.
```

### Marketing threshold
**Soubor:** `marketing_email_detector.py:189`
```python
is_marketing = confidence >= 40  # Změň na 30 (citlivější) nebo 50 (méně citlivý)
```

### Auto-classify patterns
**Soubor:** `test_marketing_detector_grouped.py:181`
```python
def auto_classify_top_groups(groups, existing_classifications):
    patterns = [
        'mobile.de',
        'autoscout24',
        'immowelt',
        # Přidej další:
        'netflix',
        'spotify',
    ]
```

### Whitelist/Blacklist
**Soubory:** `email_whitelist.json`, `email_blacklist.json`
```json
{
  "domain": "example.com",
  "pattern": "@example.com",
  "category": "bank",
  "confidence": 100,
  "reason": "Důležitý odesilatel"
}
```

---

## 🔧 Troubleshooting

### Problém: Smart matching nenachází sendery
**Příčina:** Sender v DB se liší od senderu v nových emailech

**Řešení:**
```bash
# Zkontroluj jak vypadají sendery v DB
sqlite3 ~/apps/maj-subscriptions-local/data/subscriptions.db \
  "SELECT DISTINCT sender FROM email_classifications LIMIT 20"

# Porovnej s sendery v emailech
sqlite3 ~/apps/maj-subscriptions-local/data/subscriptions.db \
  "SELECT DISTINCT email_from FROM emails LIMIT 20"

# Pokud se liší, zkus fuzzy matching (budoucí feature)
```

### Problém: Import hlásí "chybí metadata"
**Příčina:** Starý formát JSON (jen boolean místo objektu)

**Řešení:**
```bash
# Re-exportuj z nového HTML (s groups_metadata)
open ~/apps/maj-subscriptions-local/marketing_test_results_grouped.html
# Klikni "Export JSON"
```

### Problém: Přepsání existujících klasifikací
**Příčina:** `INSERT OR REPLACE` přepíše i když už existuje

**Řešení:**
```bash
# Nejdříve zkontroluj co už je v DB
sqlite3 ~/apps/maj-subscriptions-local/data/subscriptions.db \
  "SELECT group_id, sender FROM email_classifications WHERE source='manual_import'"

# Pokud nechceš přepsat, změň v import scriptu:
# INSERT OR REPLACE → INSERT OR IGNORE
```

### Problém: Opakované dotazy i po importu
**Příčina:** Sender matching nenašel zhodu (různé formáty)

**Diagnostika:**
```bash
# Zkontroluj konkrétní sender
sqlite3 ~/apps/maj-subscriptions-local/data/subscriptions.db \
  "SELECT sender FROM email_classifications WHERE sender LIKE '%kopp%'"

# Výsledek: Kopp Report <noreply@kopp-report.de>

# Zkontroluj nové emaily
sqlite3 ~/apps/maj-subscriptions-local/data/subscriptions.db \
  "SELECT DISTINCT email_from FROM emails WHERE email_from LIKE '%kopp%' LIMIT 5"

# Pokud se liší, musíš normalizovat:
# - Odstranit display name
# - Lowercase
# - Trim whitespace
```

---

## 📊 Statistiky

### Typické výsledky (5000 emailů):

```
📊 STATISTIKY:
  Celkem emailů: 5000
  Skupin: 235

  Marketing skupin: 176 (74.9%)
  Marketing emailů: 3,745 (74.9%)

  Už klasifikovaných: 56 (23.8%)
  ├─ Auto (mobile.de, autoscout24): 11
  └─ Sender match (user import): 45

  Zbývá klasifikovat: 179 (76.2%)
  Průměrná spolehlivost: 69.7%
```

### TOP 10 nejčastějších skupin:

```
1. 407× "mobile.de Suchauftrag" <noreply@dein.mobile.de>
2. 156× "AutoScout24 Fahrzeugsuche" <savedsearches@notifications.autoscout24.com>
3.  99× "mobile.de Suchauftrag" <noreply@news.mobile.de>
4.  82× "AutoScout24 Fahrzeugsuche" <no-reply@rtm.autoscout24.com>
5.  70× "immowelt Suche" <angebot@suchen.immowelt.de>
6.  68× "OpenAI" <noreply@tm.openai.com>
7.  44× "AutoScout24 Fahrzeugsuche" <savedsearches@...>
8.  43× "TVSpielfilm.de-Newsletter" <newsletter@...>
9.  35× "Blinkist" <hello@mail.blinkist.com>
10. 34× Časopis CHIP <magazin@chip.cz>
```

---

## 🚀 Aliasy pro rychlé použití

Přidej do `~/.zshrc`:
```bash
# Marketing detector workflow
alias mkt-test="cd ~/apps/maj-subscriptions-local && python3 test_marketing_detector_grouped.py"
alias mkt-export="open ~/apps/maj-subscriptions-local/marketing_test_results_grouped.html"
alias mkt-import="~/apps/maj-subscriptions-local/import_classifications_from_json.py ~/Downloads/marketing_classifications_with_metadata.json && rm ~/Downloads/marketing_classifications_with_metadata.json"

# DB queries
alias mkt-db="sqlite3 ~/apps/maj-subscriptions-local/data/subscriptions.db"
alias mkt-stats="mkt-db 'SELECT source, COUNT(*) FROM email_classifications GROUP BY source'"
alias mkt-count="mkt-db 'SELECT COUNT(*) FROM email_classifications'"
```

**Použití:**
```bash
mkt-test       # Spusť test
mkt-export     # Otevři HTML
mkt-import     # Importuj po exportu
mkt-stats      # Statistiky klasifikací
```

---

## 📚 Další dokumentace

- **`EXPORT_IMPORT_WORKFLOW.md`** - Detailní workflow návod
- **`REPEATED_QUESTIONS_FIX.md`** - Root cause analýza opakovaných dotazů
- **`SOLUTION_SUMMARY.md`** - Přehled implementace smart matching
- **`WHITELIST_BLACKLIST_IMPROVEMENT_REPORT.md`** - Analýza WL/BL systému

---

## 🔮 Budoucí vylepšení

### 1. Real-time DB save
Přidat API endpoint pro přímé uložení z HTML (bez export/import):
```javascript
fetch('/api/classify', {
    method: 'POST',
    body: JSON.stringify({group_id, is_marketing, sender, subject})
});
```

### 2. Fuzzy sender matching
Lepší matching pro různé formáty:
```python
normalize_sender("Kopp Report <noreply@kopp-report.de>") == "kopp-report.de"
```

### 3. Machine Learning
Train model na user klasifikacích:
```python
from sklearn.ensemble import RandomForestClassifier
model = train_on_user_classifications()
```

### 4. Bulk actions
UI funkce pro hromadné akce:
- "Mark all visible as MARKETING"
- "Mark all from this sender as NOT MARKETING"

---

## 📄 License

Interní projekt - MAJ Subscriptions

## 👤 Autor

Martin Puzik (m.a.j.puzik@gmail.com)

---

## 📅 Changelog

### v1.2 (2025-01-03)
- ✅ Smart sender matching
- ✅ Export s metadaty
- ✅ Import script
- ✅ Fix opakovaných dotazů

### v1.1 (2025-01-02)
- ✅ Whitelist/Blacklist integrace
- ✅ Auto-klasifikace TOP skupin
- ✅ Default filter: Unclassified

### v1.0 (2025-01-01)
- ✅ Základní marketing detection
- ✅ Email grouping
- ✅ HTML UI s MKT/NOT buttons
- ✅ localStorage persistence
