# Bressner Technology s.r.o. - E-commerce Web Platform

Moderní e-commerce platforma pro průmyslovou hardware společnost Bressner Technology s.r.o. vytvořená v Next.js 14 s AI asistentem, multi-language podporou a Stripe platební integrací.

## 🚀 Hlavní Funkce

### ✅ Hotové Funkce

1. **Homepage s Elegant Design**
   - 8 produktových kategorií s video pozadím
   - Hero sekce s AOS animacemi
   - Stats sekce (30+ let zkušeností, 10,000+ instalací)
   - Solutions, About, References, Blog, CTA sekce
   - Kompletní footer s českými firemními údaji

2. **AI Chat Asistent (24/7)**
   - Claude API (Anthropic) integrace s fallback na Ollama DeepSeek V3.1 671B
   - Hlasový výstup (Apple Web Speech API s českým hlasem "Zdeněk")
   - Hlasový vstup (Web Speech Recognition)
   - Multi-language podpora (CS/DE/EN)
   - Možnost přepnout na živého operátora

3. **E-commerce Funkce**
   - Nákupní košík s localStorage persistence
   - Stripe Checkout integrace (test mode)
   - Kategorie a subkategorie produktů
   - Produktové detaily s technickými specifikacemi
   - Success/Cancel checkout stránky

4. **Multi-Language Systém**
   - Čeština (CS) - výchozí
   - Němčina (DE)
   - Angličtina (EN)
   - Language switcher v navigaci
   - Automatické překlady všech komponent

5. **Responsive Design**
   - Mobile-first přístup
   - Tailwind CSS utility-first design
   - AOS (Animate On Scroll) animace
   - Video backgrounds pro kategorie

6. **Footer s Právními Informacemi**
   - Newsletter subscription
   - Kontaktní údaje (Praha 9, Černý Most)
   - Support linky (Technical Support, Downloads, FAQ, RMA)
   - Právní sekce (Impressum, Datenschutz, Cookies, AGB, Widerruf)
   - Firmenní údaje (IČO: 27566021, DIČ: CZ27566021)
   - Jednatelka: Ing. Zuzana Pužíková

## 📁 Struktura Projektu

```
bressner-web/
├── app/
│   ├── api/
│   │   ├── chat/route.ts          # Claude/Ollama AI chat endpoint
│   │   ├── checkout/route.ts      # Stripe checkout session
│   │   └── tts/route.ts          # Piper TTS endpoint (unused)
│   ├── checkout/
│   │   ├── success/page.tsx      # Checkout success page
│   │   └── cancel/page.tsx       # Checkout cancel page
│   ├── kategorie/[id]/page.tsx   # Category detail pages
│   ├── products/[category]/[subcategory]/page.tsx
│   ├── layout.tsx
│   ├── page.tsx                  # Homepage
│   └── providers.tsx             # React Query, Auth, Language providers
├── components/
│   ├── AIChat.tsx               # AI assistant with voice I/O
│   ├── Navigation.tsx           # Top navigation with language switcher
│   ├── Hero.tsx                 # Hero section
│   ├── Stats.tsx                # Statistics section
│   ├── ProductCategories.tsx    # 8 category cards with videos
│   ├── Solutions.tsx            # Solutions showcase
│   ├── About.tsx                # About company section
│   ├── References.tsx           # Customer references
│   ├── Blog.tsx                 # Blog/news section
│   ├── CTA.tsx                  # Call-to-action section
│   ├── Newsletter.tsx           # Newsletter subscription
│   └── Footer.tsx               # Footer with legal info
├── contexts/
│   ├── LanguageContext.tsx      # Multi-language state
│   ├── CartContext.tsx          # Shopping cart state
│   └── AuthContext.tsx          # Authentication state
├── public/
│   └── videos/                  # Category videos (7 x MP4)
│       ├── medical-hardware.mp4
│       ├── industrie-pcs.mp4
│       ├── display-losungen.mp4
│       ├── hpc-losungen.mp4
│       ├── industrial-iot.mp4
│       ├── ki-losungen.mp4
│       └── rugged-computing.mp4
├── .env                         # Database, NextAuth config
├── .env.local                   # Stripe API keys, App URL
├── package.json
├── tailwind.config.ts
└── tsconfig.json
```

## 🛠️ Technologie

- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **Animations**: AOS (Animate On Scroll)
- **AI**: Claude API (Anthropic) + Ollama fallback
- **Payment**: Stripe Checkout
- **Database**: PostgreSQL (připraveno)
- **Auth**: NextAuth.js (připraveno)
- **State Management**: React Context API
- **Voice**: Web Speech API (TTS/STT)

## 📦 Instalace a Spuštění

### Prerekvizity

- Node.js 18+
- npm nebo pnpm
- PostgreSQL (pro produkci)
- Stripe účet (test mode)
- Anthropic API klíč

### Instalace

```bash
# Clone repository
git clone https://github.com/yourusername/bressner-web.git
cd bressner-web

# Install dependencies
npm install

# Copy environment variables
cp .env.example .env
cp .env.local.example .env.local

# Edit .env.local with your keys:
# - NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY
# - STRIPE_SECRET_KEY
# - ANTHROPIC_API_KEY
```

### Spuštění Development Serveru

```bash
npm run dev
```

Server běží na **http://localhost:3000** (pokud je port volný, jinak 3001, 3002...)

### Production Build

```bash
npm run build
npm start
```

## 🔑 Environment Variables

### `.env` (Database & Auth)

```env
DATABASE_URL="postgresql://postgres:postgres@localhost:5432/bressner"
NEXTAUTH_SECRET="bressner-secret-key-2025-change-in-production"
NEXTAUTH_URL="http://localhost:3000"
DEFAULT_VAT_RATE="21"
DEFAULT_LOCALE="cs"
SUPPORTED_LOCALES="cs,de,en"
```

### `.env.local` (API Keys & Secrets)

```env
# Stripe (Test Mode)
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_SECRET_KEY=sk_test_...

# App URL (for Stripe redirects)
NEXT_PUBLIC_APP_URL=http://localhost:3002

# Anthropic Claude AI
ANTHROPIC_API_KEY=sk-ant-...

# Ollama Remote (Optional fallback)
OLLAMA_API_URL=http://your-ollama-server:11434
```

## 🎨 Design System

### Barvy (Bressner Brand)

- **Primary**: `#00AEEF` (Bressner Blue)
- **Secondary**: `#0099d6` (Darker Blue)
- **Text**: `#1a1a1a` (Dark Gray)
- **Background**: `#ffffff` (White)

### Typografie

- **Headings**: Helvetica Bold
- **Body**: Helvetica Roman
- **Sizes**: 14px-48px responsive scale

## 🌍 Multi-Language Podpora

Všechny texty jsou v 3 jazycích:

```typescript
// Příklad
{language === 'de'
  ? 'Text německy'
  : language === 'en'
  ? 'Text anglicky'
  : 'Text česky'
}
```

## 💳 Stripe Integrace

### Test Karty

```
Card Number: 4242 4242 4242 4242
Expiry: 12/34
CVC: 123
ZIP: 12345
```

### Checkout Flow

1. User přidá produkty do košíku
2. Klikne "Checkout"
3. Stripe Checkout Session se vytvoří
4. Redirect na Stripe hosted checkout
5. Po úspěšné platbě → `/checkout/success`
6. Po zrušení → `/checkout/cancel`

## 🤖 AI Chat Features

### Podporované Funkce

- ✅ Produkt doporučení
- ✅ Technické dotazy
- ✅ Kompatibilita komponentů
- ✅ Předběžná objednávka
- ✅ Multi-language responses
- ✅ Hlasový výstup (Czech)
- ✅ Hlasový vstup (Czech)

### API Provider Priority

1. **Claude Sonnet 4** (Anthropic API)
2. **DeepSeek V3.1 671B** (Remote Ollama fallback)
3. Error handling with user-friendly messages

## 📊 Produktové Kategorie

1. **Medical Hardware** - EN 60601 certifikované PC pro zdravotnictví
2. **Industrie-PCs** - Robustní počítače pro výrobu
3. **Display Solutions** - Průmyslové displeje a touch panely
4. **HPC Solutions** - High-performance computing pro AI
5. **Industrial IoT** - IoT gateway a edge computing
6. **AI Solutions** - Hardware pro machine learning
7. **Rugged Computing** - Odolné počítače pro extrémní podmínky
8. **Embedded Systems** - COM-Express a SBC pro OEM

## 🔐 Právní Informace

### Firemní Údaje

- **Název**: Bressner Technology s.r.o.
- **IČO**: 27566021
- **DIČ**: CZ27566021
- **Sídlo**: Ocelkova 643/20, 198 00 Praha 9, Černý Most
- **Jednatelka**: Ing. Zuzana Pužíková
- **Spisová značka**: C 113048 vedená u Městského soudu v Praze
- **Telefon**: +420 251 109 954
- **Email**: kunst@bressner.cz
- **Web**: www.bressner.cz

### Potřebné Právní Stránky (TODO)

- [ ] `/impressum` - Impressum s firemními údaji
- [ ] `/datenschutz` - GDPR privacy policy
- [ ] `/cookies` - EU cookie directive
- [ ] `/agb` - Terms and conditions
- [ ] `/widerruf` - Right of withdrawal

## 🚧 TODO - Další Vývoj

### High Priority

- [ ] Vytvoření právních stránek (Impressum, Datenschutz, Cookies, AGB)
- [ ] Detail stránky kategorií (`/kategorie/[id]`)
- [ ] Support/Downloads portály
- [ ] Newsletter funkčnost (backend)
- [ ] Produktový katalog (import z databáze)

### Medium Priority

- [ ] PostgreSQL database setup
- [ ] NextAuth authentication
- [ ] User dashboard
- [ ] Order history
- [ ] Admin panel
- [ ] Product management CMS

### Low Priority

- [ ] Blog systém
- [ ] Customer reviews
- [ ] Wishlist funkce
- [ ] Compare products
- [ ] Advanced search/filters

## 📝 Git Commit History

```bash
# View commits
git log --oneline --graph

# Recent changes
- Footer updated with Czech company info (IČO, DIČ, Ing. Zuzana Pužíková)
- Homepage redesigned (removed products with prices, added category cards)
- AI Chat with voice output (Web Speech API)
- Stripe checkout integration
- Multi-language system (CS/DE/EN)
```

## 🔗 Důležité Odkazy

- **Development**: http://localhost:3002
- **Tailscale Funnel**: Dostupné přes Tailscale VPN
- **Stripe Dashboard**: https://dashboard.stripe.com/test/payments
- **Obchodní rejstřík**: https://rejstrik-firem.kurzy.cz/27566021/

## 👥 Kontakt

- **Email**: kunst@bressner.cz
- **Telefon**: +420 251 109 954, +420 602 650 950
- **LinkedIn**: https://www.linkedin.com/company/bressner-technology
- **Twitter**: https://twitter.com/bressner_tech

## 📄 License

Proprietární software - Bressner Technology s.r.o. © 2025

---

**Vytvořeno s Claude Code AI Assistant**
Poslední update: 31. října 2025
