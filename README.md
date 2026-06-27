# AI Logistics Control Tower

[![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Redis](https://img.shields.io/badge/Redis-DC382D?logo=redis&logoColor=white)](https://redis.io/)
[![React](https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=black)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.6-3178C6?logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![Vite](https://img.shields.io/badge/Vite-646CFF?logo=vite&logoColor=white)](https://vite.dev/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind-38BDF8?logo=tailwindcss&logoColor=white)](https://tailwindcss.com/)
[![Docker](https://img.shields.io/badge/Docker-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)

A production-shaped monorepo for an AI Logistics Control Tower. The backend exposes logistics APIs for route optimization, ETA prediction, and delay analytics, while the frontend provides a dispatcher-focused dashboard and a route-planning experience built around map interaction and optimization feedback.

## Architecture

```mermaid
flowchart LR
  subgraph Browser[Dispatcher Browser]
    UI[React + TypeScript Control Tower]
    RoutePage[Plan Route Page]
    Dashboard[Operational Dashboard]
  end

  subgraph App[Application Layer]
    API[FastAPI API]
    Auth[JWT Auth]
    ETA[ETA Prediction Service]
    VRP[Route Optimization Service]
    Analytics[Delay Analytics Service]
  end

  subgraph Data[Data Layer]
    PG[(PostgreSQL)]
    Redis[(Redis Cache)]
    Model[(ETA Joblib Model)]
  end

  subgraph Ops[Offline Jobs]
    Synth[Synthetic Data Generator]
    Loader[Bulk Loader]
    Train[ETA Model Training]
  end

  UI --> API
  RoutePage --> API
  Dashboard --> API
  API --> Auth
  API --> ETA
  API --> VRP
  API --> Analytics
  Auth --> PG
  ETA --> Model
  VRP --> PG
  Analytics --> PG
  Analytics --> Redis
  Synth --> Loader
  Loader --> PG
  Train --> Model
```

## Repository Layout

- `backend/` FastAPI service, SQLAlchemy models, Pydantic schemas, Alembic migrations, and utility scripts
- `frontend/` React 18 + TypeScript app with Tailwind CSS, React Query, and Leaflet-based routing UX
- `docker-compose.yml` Local orchestration for PostgreSQL, Redis, backend, and frontend
- `README.md` Project overview and setup guide

## Key Results

The project exposes the core metrics in code and API responses, but this repository does not currently persist a benchmark artifact or CI report snapshot. The values below should be filled from the latest benchmark or test run.

- Route optimization savings: `TBD` percentage versus the naive sequential route
- ETA prediction accuracy: `TBD` based on the latest model evaluation output from `backend/scripts/train_eta_model.py`
- Delay detection precision: `TBD` from the delay analytics validation run

If you have the benchmark outputs, place them here in a fixed format such as:

- Route optimization savings: `42.8%`
- ETA prediction accuracy: `MAE 8.6 min` or `R² 0.91`
- Delay detection precision: `0.87`

## Screenshots

Add screenshots of the major user flows here once they are captured.

### Dashboard

<img width="1695" height="902" alt="image" src="https://github.com/user-attachments/assets/d560f7b6-d9bd-4bd6-8af2-c036ffe83256" />

### Plan Route

<img width="1546" height="868" alt="image" src="https://github.com/user-attachments/assets/7b13bf71-e54b-4961-8abc-0dc353d938bf" />


### Route Optimization Result

<img width="1012" height="486" alt="image" src="https://github.com/user-attachments/assets/5cfb1203-e4f3-4847-bbf1-aad9642038bd" />


## Setup

### Prerequisites

- Python 3.11
- Node.js 18 or newer
- Docker Desktop or Docker Engine + Compose

### 1. Start the full stack with Docker

```bash
docker compose up --build
```

This starts:

- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API health: http://localhost:8000/api/health

### 2. Run the backend locally

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Run the frontend locally

```bash
cd frontend
npm install
npm run dev
```

## Environment Variables

Backend configuration is centralized in `backend/app/core/config.py`.

- `DATABASE_URL` SQLAlchemy async connection string for PostgreSQL
- `REDIS_URL` Redis connection string for analytics caching
- `BACKEND_CORS_ORIGINS` Comma-separated list of allowed frontend origins
- `ETA_MODEL_PATH` Path to the persisted ETA model artifact
- `ANALYTICS_CACHE_TTL_SECONDS` Redis cache TTL for delay analytics responses
- `VITE_API_BASE_URL` Frontend API base URL used at build time

## Backend Workflows

### Generate synthetic logistics data

```bash
cd backend
python scripts/generate_synthetic_logistics_data.py
```

### Load synthetic data into PostgreSQL

```bash
cd backend
python scripts/load_synthetic_logistics_data.py --truncate
```

### Train the ETA prediction model

```bash
cd backend
python scripts/train_eta_model.py
```

### API endpoints

- `POST /api/auth/register`
- `POST /api/auth/login`
- `POST /api/auth/refresh`
- `GET /api/auth/me`
- `POST /api/predict-eta`
- `POST /api/optimize-route`
- `POST /api/analytics/delays`
- `GET /api/health`

## Frontend Highlights

- Dispatcher-focused route planning with map clicks and address search
- Live route comparison with naive versus optimized metrics
- Map rendering with Leaflet and OpenStreetMap tiles
- Dashboard panels for fleet state, shipment data, and analytics
- Skeleton loaders for asynchronous views

## Notes

- The route optimization service uses OR-Tools when available and falls back to a nearest-neighbor heuristic if solving times out or the solver is unavailable.
- The analytics endpoint caches repeated requests in Redis to keep the dashboard responsive.
- The ETA training script writes both a `joblib` model artifact and a companion metrics JSON file next to it.
- This repository is structured to support local development first, but the layout is suitable for containerized deployment and future CI integration.
