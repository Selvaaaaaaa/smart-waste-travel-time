# Smart Waste Collection Simulator — Deployment & Production Guide (Phase 10)

This guide documents the procedures for deploying the Smart Waste Collection Simulator across local development, containerized Docker Compose, and production municipal environments.

---

## 1. Prerequisites

- **Python:** 3.11 or higher
- **Node.js:** 20.x or higher (`npm 10.x`)
- **Docker:** Docker Engine 24+ and Docker Compose v2+
- **Database:** PostgreSQL 15+ (Production) or SQLite 3 (Development fallback)

---

## 2. Environment Configuration

The application reads configuration from environment variables defined in `.env`:

### Root `.env` / `backend/.env`
```ini
ENVIRONMENT=production
DEBUG=False
PROJECT_NAME="Smart Waste Collection Travel-Time & Route Simulator"
API_PREFIX=/api

# CORS Allowed Origins
CORS_ORIGINS=["http://localhost:80","http://localhost:5173","http://127.0.0.1:5173"]

# PostgreSQL Database Configuration
POSTGRES_SERVER=db
POSTGRES_PORT=5432
POSTGRES_DB=smart_waste_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres_secure_password

# Authentication
SECRET_KEY=municipal_super_secret_jwt_key_phase10
ACCESS_TOKEN_EXPIRE_MINUTES=1440
```

### `frontend/.env`
```ini
VITE_API_BASE_URL=/api
```

---

## 3. Docker Compose Deployment (Recommended)

The entire integrated stack (Database, FastAPI backend, React/Nginx frontend) is containerized via `docker-compose.yml`:

```bash
# 1. Build and launch all services in detached mode
docker-compose up -d --build

# 2. Check service health status
docker-compose ps

# 3. View live combined logs
docker-compose logs -f backend frontend
```

### Exposed Endpoints in Docker
| Service | Internal Port | Host Port | Protocol | Purpose |
|---|---|---|---|---|
| `smart_waste_frontend` | 80 | **80** | HTTP / WS | Web Application & Nginx Reverse Proxy |
| `smart_waste_backend` | 8000 | **8000** | HTTP / WS | FastAPI Gateway Core |
| `smart_waste_postgres` | 5432 | **5432** | TCP | PostgreSQL Database |

---

## 4. Local Bare-Metal Development Setup

If running directly on a developer workstation:

### Backend Setup
```bash
# Navigate to backend directory
cd backend

# Create and activate virtual environment
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run database migrations and seed data
python -m app.db.seed

# Launch FastAPI development server
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### Frontend Setup
```bash
# Navigate to frontend directory
cd frontend

# Install Node modules
npm install

# Launch Vite development server
npm run dev
# Frontend runs at http://localhost:5173
```

---

## 5. Production Health Verification

Once deployed, verify all subsystems via the unified health check:
```bash
curl -s http://localhost:8000/api/v1/health | jq
```
Expected output:
```json
{
  "status": "HEALTHY",
  "service": "Smart Waste Travel Time Simulator",
  "phase": 2,
  "database": { "status": "CONNECTED", "latency_ms": 0.45 },
  "telemetry": { "status": "ACTIVE", "health_rate_pct": 100.0 },
  "websocket": { "status": "CONNECTED", "connected_clients": 1 },
  "simulation": { "status": "READY" }
}
```

---

## 6. Backup & Recovery

### Database Backup
```bash
docker exec -t smart_waste_postgres pg_dump -U postgres smart_waste_db > backup_$(date +%Y%m%d).sql
```

### Database Restore
```bash
cat backup_20260906.sql | docker exec -i smart_waste_postgres psql -U postgres -d smart_waste_db
```
