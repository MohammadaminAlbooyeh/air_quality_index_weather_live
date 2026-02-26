# frontend-react

Scaffolded Vite + React + TypeScript frontend with `react-leaflet`.

Quick start:

```bash
cd frontend-react
npm install
npm run dev
```

Open http://localhost:5173 and the app will load. It expects the backend API to be available at `/api/air-quality-coords/:lat/:lng` (relative path). If your backend runs on a different host/port during development, update the fetch URL in `src/MapView.tsx` or use a proxy in `vite.config.ts`.

Notes:
- This is a scaffold only; run `npm install` to fetch dependencies.
- If you prefer the current vanilla JS frontend, keep `frontend/` as-is; this new app lives in `frontend-react/`.