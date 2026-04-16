# TDMS And Dashboard Setup

Use this page to run TDMS and the Test Case Execution Dashboard together in local development.

The integrated setup includes six services:

- TDMS backend
- TDMS frontend
- Dashboard backend
- Dashboard frontend
- Auth service
- Interface manager

## Prerequisites

- Python `3.10+`
- Node.js `20.19+` or `22.12+`
- npm
- Chrome browser (for interface manager web automation use cases)

## One-Time Configuration

Update repository root [`config.json`](../../config.json) for database and ports.

SQLite example:

```json
{
  "db": {
    "engine": "sqlite",
    "engine_type": "sqlite",
    "file": "AIEvaluationData.db"
  },
  "port": {
    "back-end": "7000",
    "interface-manager": "8000"
  }
}
```

MariaDB example:

```json
{
  "db": {
    "engine": "mariadb",
    "engine_type": "mariadb",
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

Notes:

- TDMS backend reads `db.engine`.
- Dashboard backend reads `db.engine_type`.
- Keeping both keys aligned avoids configuration drift.

## Install Dependencies

Install Python dependencies:

```bash
pip install -r requirements.txt
pip install -r src/app/TDMS/back-end/requirements.txt
pip install -r src/app/auth_service/requirements.txt
```

Install frontend dependencies:

```bash
cd src/app/TDMS/front-end && npm install
cd ../../TestCaseExecutorDashboard/front-end && npm install
```

## Start Services

Start each service in a separate terminal.

1. Auth service (`http://localhost:7500`):

```bash
cd src/app/auth_service
python main.py
```

2. TDMS backend (`http://localhost:7250`):

```bash
cd src/app/TDMS/back-end
python main.py
```

3. Dashboard backend (`http://localhost:7000` by default from `config.json`):

```bash
cd src/app/TestCaseExecutorDashboard/back-end
python main.py
```

4. Interface manager (`http://localhost:8000`):

```bash
cd src/app/interface_manager
python main.py
```

5. TDMS frontend (typically `http://localhost:8080`):

```bash
cd src/app/TDMS/front-end
npm run dev
```

6. Dashboard frontend (typically `http://localhost:3000`):

```bash
cd src/app/TestCaseExecutorDashboard/front-end
REACT_APP_API_BASE_URL=http://localhost:7000 npm start
```

## Access URLs

- Auth login: `http://localhost:7500/web/login`
- TDMS: `http://localhost:8080`
- Dashboard: `http://localhost:3000`
- TDMS backend health: `http://localhost:7250/`

## Setup Validation Checklist

- Login page opens from the auth service.
- TDMS dashboard cards show counts.
- Dashboard test runs page loads without auth errors.
- New run form loads targets, plans, and filters.
- Interface manager is reachable when run execution starts.
