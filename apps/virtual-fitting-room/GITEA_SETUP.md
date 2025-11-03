# 🔧 Gitea Setup - Virtual Fitting Room

## 📍 Gitea Server Information

- **URL:** http://192.168.10.35:3000
- **SSH:** ssh://git@192.168.10.35:2222
- **Owner:** maj
- **Repository:** virtual-fitting-room

---

## 🚀 Quick Setup (2 způsoby)

### Způsob 1: Manuální vytvoření (Doporučeno)

1. **Otevřít Gitea:**
   ```
   http://192.168.10.35:3000
   ```
   *(Již otevřeno v prohlížeči)*

2. **Přihlásit se:**
   - Username: `maj`
   - Password: *(vaše heslo)*

3. **Vytvořit nový repozitář:**
   - Kliknout na `+` (vpravo nahoře) → **New Repository**
   - **Owner:** maj
   - **Repository Name:** `virtual-fitting-room`
   - **Description:** `Virtual Fitting Room v1.0 - AI-Powered Virtual Try-On with CatVTON`
   - **Visibility:** Private *(nebo Public podle preference)*
   - **Initialize:** ❌ NE-zaškrtávat (máme už kód)
   - Kliknout **Create Repository**

4. **Pushnout kód:**
   ```bash
   cd ~/apps/virtual-fitting-room
   git push gitea main
   ```

5. **Ověřit:**
   - Otevřít: http://192.168.10.35:3000/maj/virtual-fitting-room
   - Měli byste vidět všechny soubory

---

### Způsob 2: Automatické vytvoření (s API tokenem)

1. **Získat API Token:**
   - Přihlásit se do Gitea
   - Nastavení → Applications → Generate New Token
   - Name: `virtual-fitting-room-setup`
   - Permissions: **repo** (create, read, write)
   - Copy token

2. **Spustit skript:**
   ```bash
   cd ~/apps/virtual-fitting-room
   export GITEA_TOKEN='your-copied-token'
   ./create-gitea-repo.sh
   ```

3. **Skript:**
   - Vytvoří repozitář automaticky
   - Pushne kód na Gitea
   - Zobrazí URL k repozitáři

---

## ✅ Co je už připraveno

- ✅ Git remote přidán:
  ```bash
  git remote -v | grep gitea
  # gitea  ssh://git@192.168.10.35:2222/maj/virtual-fitting-room.git
  ```

- ✅ Kód commitnutý:
  ```bash
  git log --oneline -2
  # acd63e4 Add backup summary documentation
  # 055a217 Add Virtual Fitting Room v1.0 - Complete Implementation
  ```

- ✅ SSH klíče nastaveny (pokud funguje push)

---

## 🔍 Troubleshooting

### Problém: "Permission denied (publickey)"

**Řešení:** Přidat SSH klíč do Gitea
```bash
# 1. Zkopírovat veřejný klíč
cat ~/.ssh/id_rsa.pub

# 2. V Gitea:
#    Settings → SSH / GPG Keys → Add Key
#    Vložit klíč a uložit

# 3. Test
ssh -T -p 2222 git@192.168.10.35
```

### Problém: "Repository not found"

**Řešení:** Repozitář ještě není vytvořený
- Postupovat podle Způsobu 1 výše

### Problém: "Authentication failed"

**Řešení:** Použít SSH místo HTTPS
```bash
git remote set-url gitea ssh://git@192.168.10.35:2222/maj/virtual-fitting-room.git
```

---

## 📦 Po úspěšném pushu

Repository bude dostupné na:
- **Web:** http://192.168.10.35:3000/maj/virtual-fitting-room
- **Clone:** `git clone ssh://git@192.168.10.35:2222/maj/virtual-fitting-room.git`

---

## 🎯 Recommended Next Steps

1. **Nastavit README jako hlavní stránku**
   - Gitea automaticky zobrazí README.md

2. **Přidat .gitea/workflows** (CI/CD)
   - Automatické testy
   - Automatické deploy

3. **Nastavit branch protection**
   - Settings → Branches → Protected Branches
   - Protect `main` branch

4. **Přidat Labels a Milestones**
   - Issues → Labels → Add labels
   - Pro tracking úkolů

---

## 🔐 Security Tips

- ✅ Použít private repository pro citlivý kód
- ✅ Pravidelně rotovat API tokeny
- ✅ Použít SSH klíče s passphrase
- ✅ Necommitovat .env soubory
- ✅ Přidat .gitignore pro citlivá data

---

## 📊 Repository Stats (po pushu)

- **Files:** 70+
- **Lines:** 10,342+
- **Commits:** 2
- **Size:** ~97 KB (bez node_modules)
- **Documentation:** 6 pages

---

Vytvořeno: November 3, 2025
Status: ✅ Ready to push
