# AI Trading Assistant — Mobile App

React Native (Expo) + TypeScript mobile client for the trading backend.

## Stack

- **Expo** (~52) + React Native
- **TypeScript**
- **Redux Toolkit** + **RTK Query** for API state
- **React Navigation** (bottom tabs + stacks)
- Dark mode (light / dark / system)

## Screens

| Tab | Features |
|-----|----------|
| Dashboard | Balance, equity, watchlist prices, 30d stats |
| Trades | Open/closed/all trade history |
| Strategies | List, seed samples, strategy builder |
| Analytics | Win rate, equity curve, daily P/L |
| More | Notifications, settings (API URL, risk, live confirm) |

## Quick Start

1. Start the backend (port 8000):

```bash
cd ../backend && source .venv/bin/activate && uvicorn app.main:app --reload --port 8000
```

2. Install and run the app:

```bash
cd frontend
npm install
cp .env.example .env
npm start
```

3. Open in iOS Simulator, Android emulator, or Expo Go.

### API URL by device

| Device | `EXPO_PUBLIC_API_URL` |
|--------|------------------------|
| iOS Simulator | `http://localhost:8000/api/v1` |
| Android Emulator | `http://10.0.2.2:8000/api/v1` |
| Physical device | Your machine's LAN IP, e.g. `http://192.168.1.10:8000/api/v1` |

You can also change the API URL in **Settings** inside the app.

## Scripts

```bash
npm start      # Expo dev server
npm run ios    # iOS simulator
npm run android
npm run typecheck
```

## Notes

- No login screen — single-user backend (optional API key in Settings)
- **DEMO mode** by default on backend
- Live trading requires backend `POST /api/v1/risk/confirm-live` (button in Settings)
