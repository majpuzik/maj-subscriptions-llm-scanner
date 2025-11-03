# Changelog

All notable changes to the Virtual Fitting Room project.

## [1.0.0] - 2025-11-03

### Added
- ✨ Complete virtual fitting room application
- 📷 Camera capture with multi-shot support
- 📤 File upload with drag & drop
- 🎨 CatVTON AI integration for realistic try-on
- 📊 Progress indicator with real-time status updates
- 💾 Database persistence with Prisma ORM
- 📜 History panel for past try-ons
- 🔄 Dual mode support (upload/camera) for both inputs
- 🐛 Comprehensive debugging logs
- 📖 Complete documentation

### Fixed
- 🔧 Video element ref issue (always in DOM now)
- 🔧 Button validation for camera mode
- 🔧 CatVTON server integration with local API
- 🔧 FormData handling in Node.js backend
- 🔧 Progress display during AI processing

### Technical Details
- Frontend: Next.js 16.0.1, React 19.2.0, TypeScript, Tailwind CSS 4
- Backend: Next.js API Routes, Prisma, SQLite
- AI Server: Python 3.11, Flask, PyTorch 2.9.0, CatVTON
- Ports: 3777 (Next.js), 5001 (CatVTON)

### Performance
- Camera capture: < 2s per shot
- Image upload: < 1s
- AI inference: 10-30s (hardware dependent)
- Total processing: ~15-35s

### Known Limitations
- Simple white mask (TODO: AutoMasker)
- First shot only for multi-shot (TODO: blending)
- Video upload not processed (TODO: frame extraction)

---

## [0.1.0] - 2025-11-03

### Initial Setup
- Project scaffolding with Next.js
- Basic UI components
- Database schema design
- CatVTON server skeleton
