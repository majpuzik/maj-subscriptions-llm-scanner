# Unified MCP v5 - Progress Report

**Datum:** 2025-01-03 19:55
**Session:** Initial Implementation
**Status:** 🚧 IN PROGRESS (Step 2/8 completed)

---

## ✅ Dokončené úkoly (2/8)

### 1. ✅ Upload Python modules to NAS5

**Soubory nahrané na `/volume1/docker/unified-mcp-server/`:**

```
-rwxrwxrwx+ marketing_email_detector.py  (11K)  ✓
-rwxrwxrwx+ subscription_detector.py     (8.1K) ✓
-rwxrwxrwx+ email_lists.py               (7.5K) ✓
-rwxrwxrwx+ email_whitelist.json         (4.2K) ✓
-rwxrwxrwx+ email_blacklist.json         (12K)  ✓
```

**Metoda:** SSH cat redirect (SCP/rsync selhávaly kvůli permissions)

---

### 2. ✅ Create subscription_detector.py

**Features implementované:**
- Hybrid approach (keyword pre-filter + LLM)
- quick_keyword_filter() - fast pre-screening
- analyze_with_llm() - Kimi-k2:1t-cloud integration
- detect_subscription() - main entry point
- Paperless-compatible output format
- NULL filtering for clean data
- Debug logging

**Ollama config:**
- Model: kimi-k2:1t-cloud (1T parameters)
- Endpoint: http://192.168.10.83:11434/api/generate
- Timeout: 120s

---

## ⏳ Pending úkoly (6/8)

### 3. ⏳ Add MCP tools to server.js

**Co přidat:**
```javascript
{
  name: "classify_marketing_email",
  description: "Classify email as marketing/newsletter/subscription renewal",
  inputSchema: {
    type: "object",
    properties: {
      subject: { type: "string" },
      from: { type: "string" },
      body: { type: "string" }
    },
    required: ["subject", "from", "body"]
  }
},
{
  name: "detect_subscription",
  description: "Detect and extract subscription information from email",
  inputSchema: {
    type: "object",
    properties: {
      subject: { type: "string" },
      from: { type: "string" },
      body: { type: "string" }
    },
    required: ["subject", "from", "body"]
  }
}
```

**File:** `/volume1/docker/unified-mcp-server/server.js`

---

### 4. ⏳ Add HTTP endpoints to http-server.js

**Endpointy k přidání:**

#### Marketing Classification
```javascript
app.post('/api/v5/classify/marketing', async (req, res) => { ... })
```

#### Subscription Detection
```javascript
app.post('/api/v5/classify/subscription', async (req, res) => { ... })
```

#### Unified Classifier
```javascript
app.post('/api/v5/classify', async (req, res) => { ... })
```

**File:** `/volume1/docker/unified-mcp-server/http-server.js`

---

### 5. ⏳ Test marketing classifier

**Test příkaz:**
```bash
curl -X POST http://192.168.10.35:8080/api/v5/classify/marketing \
  -H "Content-Type: application/json" \
  -d '{
    "subject": "Newsletter: Heute meistgelesen",
    "from": "noreply@nzz.ch",
    "body": "Top stories... Unsubscribe here"
  }'
```

**Expected output:**
```json
{
  "is_marketing": true,
  "confidence": 70,
  "category": "newsletter"
}
```

---

### 6. ⏳ Test subscription detector

**Test příkaz:**
```bash
curl -X POST http://192.168.10.35:8080/api/v5/classify/subscription \
  -H "Content-Type: application/json" \
  -d '{
    "subject": "Your OpenAI subscription renewal",
    "from": "noreply@openai.com",
    "body": "Your $20/month ChatGPT Plus subscription..."
  }'
```

**Expected output:**
```json
{
  "is_subscription": true,
  "confidence": 85,
  "service_name": "OpenAI",
  "amount": 20.0,
  "currency": "USD"
}
```

---

### 7. ⏳ Restart unified-mcp-server

**Příkaz:**
```bash
ssh admin@192.168.10.35 -p 4438
cd /volume1/docker/unified-mcp-server
sudo docker-compose restart
```

---

### 8. ⏳ Commit and push to GitHub

---

## 📊 Aktuální stav

### ✅ Co funguje:

1. **Paperless improvements (v1.5)** - implementováno a commitnuto
   - Better debug output
   - NULL filtering

2. **Python moduly** - nahrány na NAS5
   - marketing_email_detector.py
   - subscription_detector.py
   - email_lists.py + JSON files

3. **Migration guide** - vytvořen a zdokumentován
   - UNIFIED_MCP_V5_MIGRATION_GUIDE.md

---

### 🚧 Co zbývá:

1. **MCP tools** - přidat do server.js
2. **HTTP endpointy** - přidat do http-server.js
3. **Server restart** - aplikovat změny
4. **Testing** - verifikovat funkčnost
5. **Git commit** - commitnout vše

---

## 🎯 Next Steps (pro pokračování)

### Krok 1: Backup server.js a http-server.js

```bash
ssh admin@192.168.10.35 -p 4438 "
  cd /volume1/docker/unified-mcp-server
  cp server.js server.js.backup-v5-migration
  cp http-server.js http-server.js.backup-v5-migration
"
```

### Krok 2: Přidat MCP tools

Editovat `/volume1/docker/unified-mcp-server/server.js`:
- Najít sekci `tools` array
- Přidat 2 nové tool definitions (marketing + subscription)

### Krok 3: Přidat HTTP endpointy

Editovat `/volume1/docker/unified-mcp-server/http-server.js`:
- Najít sekci s existujícími endpointy
- Přidat 3 nové endpointy (/api/v5/classify/*)

### Krok 4: Test & Restart

```bash
# Test Python modules standalone
ssh admin@192.168.10.35 -p 4438 "
  cd /volume1/docker/unified-mcp-server
  python3 marketing_email_detector.py
  python3 subscription_detector.py 'Test subject' 'test@test.com' 'Test body'
"

# Restart server
ssh admin@192.168.10.35 -p 4438 "
  cd /volume1/docker/unified-mcp-server
  sudo docker-compose restart
"

# Watch logs
ssh admin@192.168.10.35 -p 4438 "
  sudo docker logs -f unified-mcp-server
"
```

---

## 📁 Soubory v repozitáři

### ✅ Commitnuté:

1. `apps/maj-subscriptions-local/production_llm_scanner.py` - enhanced debug output
2. `apps/maj-subscriptions-local/document_classifier_api.py` - NULL filtering
3. `apps/maj-subscriptions-local/PAPERLESS_IMPROVEMENTS_ADOPTION.md`
4. `apps/maj-subscriptions-local/UNIFIED_MCP_V5_MIGRATION_GUIDE.md`

### ⏳ Pending (na NAS5, ne v Gitu):

1. `/volume1/docker/unified-mcp-server/marketing_email_detector.py`
2. `/volume1/docker/unified-mcp-server/subscription_detector.py`
3. `/volume1/docker/unified-mcp-server/email_lists.py`
4. `/volume1/docker/unified-mcp-server/email_*.json`

---

## 🔧 Problémově řešené

### SSH Transfer Issue ✅ SOLVED

**Problém:** SCP a rsync selhávaly s "Permission denied"

**Řešení:** Použití SSH cat redirect:
```bash
ssh admin@192.168.10.35 "cat > /path/to/file" < local_file
```

**Proč to fungovalo:** SSH login fungoval, ale subsystémy SCP/SFTP měly permission issues.

---

## 📈 Celkový progress

**Dokončeno:** 25% (2/8 kroků)

**Čas strávený:** ~45 minut

**Odhadovaný zbývající čas:** ~90 minut

**ETA dokončení:** 2025-01-03 21:30

---

## 💡 Poznámky pro pokračování

1. **Backup vždy před editací** - server.js a http-server.js jsou kritické
2. **Test Python modules standalone** před integrací do MCP serveru
3. **Watch logs po restartu** - sledovat errory v real-time
4. **Test každý endpoint zvlášť** - nemusí všechno fungovat najednou
5. **Commit často** - po každém funkčním kroku

---

**Verze:** Unified MCP v5.0 (in progress)
**Implementoval:** Claude Code
**Session:** 2025-01-03 19:00-19:55
**Next session:** Dokončit MCP tools + HTTP endpointy + testing
