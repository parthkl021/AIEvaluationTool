# Setup (With Or Without NGINX)

Use this guide to run TDMS and the Test Case Execution Tool (Dashboard) locally without Docker.

You can choose either:

- direct frontend dev servers (`without NGINX`)
- frontend build artifacts hosted by NGINX (`with NGINX`)

## UI And Service Matrix

### Frontend UIs

- `TDMS UI` (Vite build output: `dist/`)
- `Test Case Execution Dashboard UI` (CRA build output: `build/`)

### Other User-Facing Web Interface

- `Central Login UI` is served by the auth backend at `/web/login` (no separate frontend build needed)

### Backend Services

- `auth-service` (`localhost:7500`)
- `tdms-backend` (`localhost:7250`)
- `dashboard-backend` (`localhost:7000` from `config.json`)
- `interface-manager` (`localhost:8000`)

## Prerequisites

- Python `3.10+`
- Node.js `20.19+` or `22.12+`
- npm
- NGINX (required only for NGINX mode)
- Chrome browser (needed for interface-manager web automation scenarios)

## Step 1: Create Required `.env` Files

Create and populate all required `.env` files before starting services.

### 1.1 Root `.env` (repository root)

This is used by shared runtime components (for example `interface_manager` and API key based providers).

```bash
cp .env.example .env
```

Example values in root `.env`:

```env
OLLAMA_URL=http://localhost:12434
GPU_URL=http://localhost:16000
LLM_AS_JUDGE_MODEL=
PERSPECTIVE_API_KEY=
SARVAM_API_KEY=
GEMINI_API_KEY=
OPENAI_API_KEY=
```

### 1.2 TDMS frontend `.env`

Create `src/app/TDMS/front-end/.env`:

```env
VITE_API_BASE_URL=http://localhost:7250
VITE_AUTH_SERVICE_URL=http://localhost:7500
```

### 1.3 Dashboard frontend `.env`

Create `src/app/TestCaseExecutorDashboard/front-end/.env`:

```env
REACT_APP_API_BASE_URL=http://localhost:7000
REACT_APP_AUTH_SERVICE_URL=http://localhost:7500
```

### 1.4 Auth service `.env`

Create `src/app/auth_service/.env`:

```env
AUTH_SECRET_KEY=@cerai
AUTH_REFRESH_SECRET_KEY=@cerai_refresh
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=
DB_NAME=aievaluation
TCE_APP_URL=http://localhost:3000
TDMS_APP_URL=http://localhost:8080/dashboard
CORS_ALLOW_ORIGINS=http://localhost:3000,http://localhost:8080,http://localhost:7250
COOKIE_SECURE=false
COOKIE_SAMESITE=lax
```

### 1.5 Strategy `.env`

For strategy defaults used by `src/lib/strategy/utils_new.py`, keep `src/lib/strategy/.env` present.

```bash
cp src/lib/strategy/.env.example src/lib/strategy/.env
```

Expected values:

```env
DATA_PATH=data/
DEFAULT_VALUES_PATH=data/defaults.json
EXAMPLES_DIR=data/examples/
IMAGES_DIR=data/images/
```

Important:

- Keep all runtime configuration in these `.env` files.
- Do not pass `VITE_*` or `REACT_APP_*` variables inline in run commands.

## Step 2: Configure Root `config.json`

Update repository root [`config.json`](../../config.json).

For local SQLite:

```json
{
  "db": {
    "engine": "sqlite",
    "file": "AIEvaluationData.db"
  },
  "port": {
    "back-end": "7000",
    "interface-manager": "8000"
  }
}
```

For local MariaDB:

```json
{
  "db": {
    "engine": "mariadb",
    "host": "localhost",
    "port": 3306,
    "user": "your_username",
    "password": "your_password",
    "database": "aievaluationtool"
  },
  "port": {
    "back-end": "7000",
    "interface-manager": "8000"
  }
}
```

Important:

- TDMS backend and Dashboard backend reads `db.engine`.
- Keep both keys aligned.

## Step 3: Install Dependencies

From repository root:

```bash
pip install -r requirements.txt
```

Install UI dependencies:

```bash
cd src/app/TDMS/front-end && npm install
cd ../../TestCaseExecutorDashboard/front-end && npm install
```

## Step 4: Run Backend Services Locally

Start each service in a separate terminal.

1. Auth service:

```bash
cd src/app/auth_service
python main.py
```

2. TDMS backend:

```bash
cd src/app/TDMS/back-end
python main.py
```

3. Dashboard backend (test case execution backend):

```bash
cd src/app/TestCaseExecutorDashboard/back-end
python main.py
```

4. Interface manager:

```bash
cd src/app/interface_manager
python main.py
```

## Step 5: Choose Frontend Run Mode

### Option A: Run Without NGINX (Direct Dev Servers)

This is best for development and frequent UI changes.

1. Run TDMS frontend:

```bash
cd src/app/TDMS/front-end
npm run dev
```

2. Run Dashboard frontend:

```bash
cd src/app/TestCaseExecutorDashboard/front-end
npm start
```

Access URLs in this mode:

- TDMS UI: `http://localhost:8080`
- Dashboard UI: `http://localhost:3000`
- Central login UI: `http://localhost:7500/web/login`

### Option B: Run With NGINX (Build And Serve)

Use this when you want static UI hosting and production-like frontend serving.

#### Step 5.1: Build Both UIs For NGINX

Use the `.env` files created in Step 1.

### TDMS UI build

Build:

```bash
cd src/app/TDMS/front-end
npm run build
```

### Dashboard UI build

Build:

```bash
cd src/app/TestCaseExecutorDashboard/front-end
npm run build
```

#### Step 5.2: Place Build Artifacts For NGINX

Example deployment directories:

- `/var/www/aievaluation/tdms-ui`
- `/var/www/aievaluation/dashboard-ui`

Copy files:

```bash
sudo mkdir -p /var/www/aievaluation/tdms-ui /var/www/aievaluation/dashboard-ui
sudo rsync -a --delete src/app/TDMS/front-end/dist/ /var/www/aievaluation/tdms-ui/
sudo rsync -a --delete src/app/TestCaseExecutorDashboard/front-end/build/ /var/www/aievaluation/dashboard-ui/
```

#### Step 5.3: Configure NGINX For Both UIs

Create `/etc/nginx/conf.d/aievaluation-ui.conf`:

```nginx
server {
    listen 8080;
    server_name _;

    root /var/www/aievaluation/tdms-ui;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location = /healthz {
        access_log off;
        add_header Content-Type text/plain;
        return 200 'ok';
    }
}

server {
    listen 3000;
    server_name _;

    root /var/www/aievaluation/dashboard-ui;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location = /healthz {
        access_log off;
        add_header Content-Type text/plain;
        return 200 'ok';
    }
}
```

Reload NGINX:

```bash
sudo nginx -t
sudo systemctl reload nginx
```

Access URLs in this mode:

- TDMS UI via NGINX: `http://localhost:8080`
- Dashboard UI via NGINX: `http://localhost:3000`
- Central login UI: `http://localhost:7500/web/login`

## Validation Checklist

- Backend services are reachable on `7500`, `7250`, `7000`, and `8000`.
- TDMS login redirects to auth and returns correctly.
- Dashboard login redirects to auth and returns correctly.
- TDMS `Home` link opens dashboard.
- Dashboard `Test Data` link opens TDMS.
- New run and continue run flows can load filters and start execution.
- If using NGINX mode, `http://localhost:8080/healthz` and `http://localhost:3000/healthz` return `ok`.
