# SmartGate LPR Access & Parking Prototype

A laptop-first demo of a computer-vision powered gate access stack. The project follows the PRD in `prd.yaml` and ships a FastAPI backend (mock YOLO/EasyOCR + Supabase-ready APIs) plus a Vue 3 + Vite + Tailwind frontend that covers the guard console, admin dashboards, CRUD flows, guest fees, and a lightweight user portal.

## Repo structure

```
SmartGate/
├── gitignore
├── README.md               # You are here
├── docker-compose.yml      # Dev orchestration for API + web app
├── backend/
│   ├── app/                # FastAPI application package
│   ├── requirements.txt    # Python dependencies
│   ├── Dockerfile          # Backend image (uvicorn)
│   └── .env.example        # Supabase + rate config
└── frontend/
    ├── src/                # Vue 3 + TypeScript app
    ├── package.json        # Frontend dependencies
    ├── Dockerfile          # Frontend dev image (Vite)
    └── tailwind.config.js  # Tailwind theme (brand colors)
```

## Backend (FastAPI)

### Features implemented

- `/api/infer` – wraps a mock inference pipeline (YOLO/EasyOCR interface) that can use webcam snapshots or manual plate overrides, enforces gate role thresholds, auto-opens guest sessions, and logs `access_events`.
- Real YOLOv8 + EasyOCR pipeline is wired in: drop your weights under `backend/models/` (default `yolov8n-license.pt`), set `MOCK_INFERENCE=false`, and the backend will run detection on webcam frames with CPU fallback to stay within 8 GB VRAM / 16 GB RAM limits.
- `/api/admin/*` – CRUD for users, vehicles, and passes against an in-memory seed data store (wired so Supabase/Postgres can replace the `MockDatabase`).
- `/api/access-events` – paginated event log for the guard console & dashboards.
- `/api/guest/*` - guest session lifecycle (open/close/pay + rate management) with deterministic fee math and mock payments.
- `/api/analytics/mock` - synthesizes chart-ready insights (gate frequency, guest fee trends, role/programme/vehicle distributions, unpaid ratios).
- `/api/admin/gates` - CRUD for gate definitions (dynamic slugs + minimum role thresholds) powering the guard console routing beyond the original inner/outer pair.
- `/api/face/*` - enrollment + verification endpoints powered by InsightFace (YOLO face detection + embeddings) so guards can match drivers in addition to plate reads.

### Local run

```
cd backend
python3 -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
cp .env.example .env  # update Supabase keys later
uvicorn app.main:app --host 0.0.0.0 --port 60000 --reload
```

Key environment knobs (see `.env.example`):

- `SUPABASE_URL` / `SUPABASE_KEY` – placeholders for when the Supabase client is connected.
- `USE_SUPABASE` – set to `true` (default) once your Supabase project + tables are provisioned; flip to `false` if you want the in-memory store.
- `MOCK_INFERENCE` – keep `true` for laptop demos; switch off when real YOLO/EasyOCR integration is plugged in.
- `BASE_GUEST_RATE` / `PER_MINUTE_GUEST_RATE` – defaults for guest fees, overridable via the guest API/UI.
- `REDIS_URL` / `REDIS_CACHE_TTL` – configure the Redis cache used for guard event feeds + inference throttling.
- `YOLO_WEIGHTS_PATH`, `YOLO_DEVICE`, `YOLO_CONF_THRESHOLD`, `YOLO_PLATE_CLASSES`, `OCR_LANGUAGES` – tune the YOLOv8/EasyOCR stack. By default the app loads `models/yolov8n-license.pt` on `auto` device (tries CUDA, falls back to CPU) and restricts OCR to English characters.
- `FACE_STORE_PATH` – JSON file used to persist face embeddings for the new facial-recognition prototype (default `app/data/face_store.json`).

### Notable implementation details

- The inference service returns deterministic mock detections so UI flows remain testable without heavy ML downloads. Swap `InferenceService._real_inference` with YOLO/EasyOCR code when ready.
- `MockDatabase` holds state in memory with seed data from `backend/app/data/seed.py`. Replace this layer with Supabase/Postgres adapters for persistence.
- When `USE_SUPABASE=true`, the app talks directly to Supabase tables (`users`, `vehicles`, `passes`, `access_events`, `guest_sessions`, `payments`, `guest_rates`) via the official Python client. Keep them synced with the schema defined in `app/schemas`.
- Redis backs a small cache for access events, guest session lookups, and adds rate-limiting to `/api/infer` so laptop demos stay responsive.
- Analytics are derived from the mock store so the dashboard renders without needing Supabase Realtime yet.
- YOLOv8 integration respects your hardware budget: the service lazily loads `yolov8n` (or your custom weights), fuses layers, and automatically downgrades to CPU if the 8 GB GPU isn’t available. EasyOCR shares the same device flag, so you can keep RAM/VRAM in check.

### Running real CV inference

1. Place your trained weights at `backend/models/yolov8n-license.pt` (or point `YOLO_WEIGHTS_PATH` to a different path). The lightweight `yolov8n` variant is recommended for an 8 GB GPU; heavier weights may exceed VRAM.
2. Optionally list allowed plate class IDs via `YOLO_PLATE_CLASSES=[0]` if your model outputs multiple classes.
3. Set `MOCK_INFERENCE=false` in `backend/.env`.
4. Restart the backend. Webcam captures (or uploads) now run YOLOv8 → EasyOCR, and the Guard Console displays the decoded plate instead of the mock `VISITX`.

## Frontend (Vue 3 + Vite)

### Views delivered

- **Guard Console** – webcam preview, capture button, manual plate override, live decision card, gate event table.
- **Admin Dashboard** – KPI tiles and Chart.js visualizations for gate traffic, role/vehicle mix, and guest fee trends.
- **Users / Vehicles / Passes** – CRUD tables + forms backed by the admin APIs.
- **Guest Management** – live session table, rate controls, open/close/pay actions (wired to guest APIs).
- **My Pass Portal** – shows role, expiry, linked vehicles, mock upgrade request form, and parking availability meters.

### Local run

```
cd frontend
npm install
npm run dev  # http://localhost:5173 (expects API on :60000)
```

Vite exposes `VITE_API_BASE`; defaults to `http://localhost:60000/api` when unset. Adjust via `.env` or docker-compose.

### Build/test status

- `npm run build` ✅ (bundles Tailwind/Pinia/Chart.js app; output under `frontend/dist`).
- `python3 -m compileall backend/app` ✅ (sanity check for FastAPI modules).

## Docker Compose

Bring up both stacks with hot reload:

```
docker-compose up --build
```

- Frontend served at `http://localhost:5173` (Vite dev server) with `VITE_API_BASE` prepointed at the backend service.
- Backend served at `http://localhost:60000` running `uvicorn app.main:app --reload`.
- Redis (port `6379`) is included for caching/rate-limiting; the backend auto-connects using the compose service URL.

## Next steps / gaps

1. **Real CV pipeline** – wire `InferenceService._real_inference` to actual YOLOv8 + EasyOCR weights and ensure OpenCV frame capture is available to FastAPI.
2. **Persistence** – swap `MockDatabase` with Supabase/Postgres plus storage for plate snapshots; add SQL schema + migrations.
3. **Auth** – integrate Supabase Auth or another JWT provider; guard admin routes & show real user profiles in the portal.
4. **Realtime updates** – forward access events to Supabase Realtime/WS to auto-refresh dashboards without manual polling.
5. **Automated tests** – add FastAPI route tests + Cypress component smoke tests around Guard Console & admin forms.
6. **Face liveness / anti-spoofing** – extend the InsightFace pipeline with liveness detection before trusting facial verification in production.

With the current code you can already simulate the entire demo loop on a laptop: open the backend, run the Vue client, use the webcam feed with printed plates or manual overrides, and walk through guest billing as described in the PRD.
