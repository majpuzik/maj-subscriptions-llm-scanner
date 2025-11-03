# 🚀 Virtual Fitting Room - Quick Start Guide

## Prerequisites

- Node.js 20+
- Python 3.11+ (with ComfyUI venv)
- Git

## Installation

```bash
# 1. Clone repository
cd ~/apps/virtual-fitting-room

# 2. Install Node.js dependencies
npm install

# 3. Setup database
npx prisma generate
npx prisma db push

# 4. Install Python dependencies (if needed)
pip3 install --break-system-packages flask flask-cors pillow numpy
```

## Running the Application

### Terminal 1: Start Next.js Frontend
```bash
cd ~/apps/virtual-fitting-room
npm run dev
```
→ Open http://localhost:3777

### Terminal 2: Start CatVTON AI Server
```bash
cd ~/apps/virtual-fitting-room
~/apps/ComfyUI/venv/bin/python3 catvton_server_v2.py
```
→ Server runs on http://localhost:5001

## Usage

1. **Upload or Capture Person Image**
   - Click 📤 Upload to select file
   - OR click 📷 Kamera to take photo

2. **Upload or Capture Clothing Image**
   - Same options as person image

3. **Enter Names**
   - Person name (e.g., "Jan Novák")
   - Clothing name (e.g., "Červené tričko")

4. **Click "✨ Vyzkoušet oblečení"**
   - Watch progress indicator
   - Wait ~15-35 seconds for AI processing

5. **View Result**
   - Result appears below
   - Check history in left panel

## Troubleshooting

### Port Already in Use
```bash
# Kill process on port 3777
lsof -ti:3777 | xargs kill -9

# Kill process on port 5001
lsof -ti:5001 | xargs kill -9
```

### Camera Not Working
- Refresh page (Cmd+R / F5)
- Check browser permissions
- Use Chrome/Firefox (Safari may have issues)
- Check browser console for errors

### AI Server Not Loading
```bash
# Check if PyTorch is available
~/apps/ComfyUI/venv/bin/python3 -c "import torch; print(torch.__version__)"

# Should print: PyTorch 2.9.0
```

### Database Issues
```bash
# Reset database
rm prisma/dev.db
npx prisma db push
```

## Health Checks

```bash
# Check Next.js
curl http://localhost:3777/api/history

# Check CatVTON
curl http://localhost:5001/health
# Should return: {"pipeline_loaded":true,"status":"ok"}
```

## Debugging

Enable debug logs in browser console:
- 🎥 Camera operations
- 📸 Shot capturing
- 🎨 Try-on flow
- 🚀 API requests

## Environment Variables

Create `.env` file:
```bash
DATABASE_URL="file:./dev.db"
CATVTON_SERVER_URL="http://localhost:5001"
NEXT_PUBLIC_API_URL="http://localhost:3777"
```

## Documentation

- Full docs: `IMPLEMENTATION_COMPLETE.md`
- Changes: `CHANGELOG.md`
- Issues: Create GitHub issue

## Support

Check logs:
- Browser console (F12)
- Next.js terminal
- CatVTON server terminal

Happy virtual fitting! 🎨👕
