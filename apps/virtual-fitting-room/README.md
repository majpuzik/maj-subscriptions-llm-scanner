# 🎨 Virtuální Zkušební Kabina

AI-powered virtuální zkušební kabina pro zkoušení oblečení a příslušenství.

## ✨ Funkce

- 📸 **Nahrání osoby** - Fotka nebo video osoby (vlevo nahoře)
- 👕 **Nahrání oblečení** - Obrázek oblečení či příslušenství (vpravo nahoře)
- 🤖 **AI Virtual Try-On** - Automatické vygenerování výsledku pomocí AI
- 🎮 **3D ovládání** - Rotace a zoom výsledného obrázku
- 💾 **Databáze** - Automatické ukládání osob, oblečení a výsledků
- 📚 **Historie** - Procházení předchozích zkoušek

## 🚀 Spuštění

```bash
cd ~/apps/virtual-fitting-room
npm run dev
```

Aplikace běží na: **http://localhost:3777**

## 🎯 Jak používat

1. **Nahrajte osobu:**
   - Zadejte jméno osoby
   - Nahrajte fotku nebo video (drag & drop nebo kliknutí)

2. **Nahrajte oblečení:**
   - Zadejte název oblečení
   - Nahrajte obrázek oblečení

3. **Vyzkoušet:**
   - Klikněte na "✨ Vyzkoušet oblečení"
   - Počkejte na zpracování
   - Výsledek se zobrazí dole s možností rotace a zoomu

4. **Historie:**
   - V levém panelu vidíte historii všech zkoušek
   - Kliknutím na položku zobrazíte výsledek

## 🤖 AI Integrace

### Aktuální stav: DEMO režim
Aplikace nyní běží v DEMO režimu - používá nahranou fotku osoby jako výsledek.

### Aktivace AI (Replicate)

Pro aktivaci skutečného AI virtual try-on:

1. **Získejte Replicate API klíč:**
   - Registrujte se na https://replicate.com
   - Získejte API token
   - Nastavte billing (cena ~$0.03 per inference)

2. **Nastavte API klíč:**
   ```bash
   # V souboru .env
   REPLICATE_API_TOKEN="váš_api_token"
   ```

3. **Restartujte server:**
   ```bash
   npm run dev
   ```

**Použité AI modely:**
- Kolors Virtual Try-On - Fotorealistické oblékání oblečení
- Podporuje: horní oblečení, spodní oblečení, celotělové

## 🔍 Lokální AI alternativy

Pro běh bez API nákladů můžeme integrovat:

### 1. IDM-VTON (lokální)
```bash
# Instalace
git clone https://github.com/yisol/IDM-VTON.git
cd IDM-VTON
pip install -r requirements.txt

# Potřebné modely se stáhnou automaticky (~10GB)
```

### 2. OOTDiffusion
```bash
git clone https://github.com/levihsu/OOTDiffusion
cd OOTDiffusion
pip install -r requirements.txt
```

**Poznámka:** Lokální varianty vyžadují:
- 16GB+ RAM
- NVIDIA GPU s 8GB+ VRAM (ideálně)
- ~15-30 sekund per inference

## 📁 Struktura projektu

```
virtual-fitting-room/
├── app/
│   ├── page.tsx              # Hlavní stránka
│   ├── layout.tsx            # Layout
│   └── api/
│       ├── try-on/route.ts   # API pro virtual try-on
│       └── history/route.ts  # API pro historii
├── components/
│   ├── UploadZone.tsx        # Komponenta pro upload
│   ├── ResultViewer.tsx      # 3D viewer s ovládáním
│   └── HistoryPanel.tsx      # Panel historie
├── lib/
│   ├── prisma.ts             # Prisma client
│   └── storage.ts            # File storage
├── prisma/
│   └── schema.prisma         # Databázové schema
└── public/
    └── uploads/              # Nahrané soubory
```

## 🗃️ Databáze

SQLite databáze s tabulkami:
- **Person** - Osoby (jméno, fotka, profil)
- **Clothing** - Oblečení (název, kategorie, obrázek)
- **TryOn** - Zkušební výsledky (osoba + oblečení + AI výsledek)

## 🎨 Customizace

### Změna kategorií oblečení
V `app/api/try-on/route.ts` upravte:
```typescript
category: 'upper_body' | 'lower_body' | 'full_body'
```

### Přidání více AI modelů
```typescript
// V route.ts přidejte switch pro různé modely
const models = {
  'kolors': 'c871bb9b...',
  'idm-vton': '...',
  // atd.
}
```

## 🛠️ Technologie

- **Framework:** Next.js 16 + React 19
- **Databáze:** Prisma + SQLite
- **AI:** Replicate API (Kolors Virtual Try-On)
- **Styling:** Tailwind CSS
- **Upload:** react-dropzone

## 📝 Další vylepšení

- [ ] Multi-angle generation (více úhlů pohledu)
- [ ] Video output (animované výsledky)
- [ ] Batch processing (více oblečení najednou)
- [ ] Outfit compositions (kombinace více kusů)
- [ ] AR preview (rozšířená realita)
- [ ] Sharing & export
- [ ] User authentication
- [ ] Cloud storage (S3/R2)

## 💡 Tipy

- **Kvalitní fotky:** Používejte fotky s dobrým osvětlením a neutrálním pozadím
- **Celé tělo:** Pro nejlepší výsledky nahrávejte celotělové fotky
- **Rozlišení:** Minimálně 512x512px, ideálně 1024x1024px
- **Formáty:** JPG, PNG (oblečení nejlépe PNG s průhledným pozadím)

## 🐛 Řešení problémů

**Server nechce nastartovat:**
```bash
rm -rf node_modules package-lock.json
npm install
npx prisma generate
npm run dev
```

**Databáze není vytvořena:**
```bash
npx prisma db push
```

**Upload nefunguje:**
```bash
mkdir -p public/uploads/{person,clothing,result}
chmod 755 public/uploads
```

## 📧 Podpora

Pro problémy nebo dotazy ohledně AI integrace zkontrolujte:
- Replicate docs: https://replicate.com/docs
- IDM-VTON: https://github.com/yisol/IDM-VTON
- OOTDiffusion: https://github.com/levihsu/OOTDiffusion
