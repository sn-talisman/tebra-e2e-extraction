# Tebra E2E Extraction & Analytics Platform

A comprehensive data platform that extracts patient, encounter, and financial data from Snowflake, transforms it into a 360-degree patient view in a local Postgres Data Warehouse, and serves it via a modern React/FastAPI web application.

## 🚀 Features

- **Data Pipeline**: Automated ETL from Snowflake to local Postgres (`tebra_dw`).
  - Claims, ERAs, Patients, Encounters, and Clinical Data.
  - Deterministic linkage between Claims and Encounters.
  - Automated backfill capabilities.
- **Backend API**: FastAPI service providing RESTful endpoints.
  - Analytics & Performance Dashboards.
  - Detailed Patient & Financial Timelines.
  - ERA Anomaly Detection.
- **Frontend**: Modern React application (Vite).
  - Interactive Dashboards (Recharts).
  - Deep-dive views for Practices, Patients, and ERAs.
  - Responsive design with dark mode support.

## 🛠 Prerequisites

- **Python 3.10+**
- **Node.js 18+** & **npm**
- **PostgreSQL 14+** (Local or Containerized)
- **Snowflake Account** (for data extraction)

## 📦 Installation & Setup

### 1. Clone the Repository
```bash
git clone https://github.com/tebra/tebra-e2e-extraction.git
cd tebra-e2e-extraction
```

### 2. Database Setup
Ensure Postgres is running and creating the target database:
```sql
CREATE DATABASE tebra_dw;
CREATE USER tebra_user WITH PASSWORD 'tebra_password';
GRANT ALL PRIVILEGES ON DATABASE tebra_dw TO tebra_user;
-- Connect to tebra_dw and create schema
\c tebra_dw
CREATE SCHEMA tebra;
```

### 3. Backend & Pipeline Setup
Create a virtual environment and install dependencies:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file in the root directory:
```ini
# Snowflake Credentials
SNOWFLAKE_ACCOUNT=your_account
SNOWFLAKE_USER=your_user
SNOWFLAKE_PASSWORD=your_password
SNOWFLAKE_WAREHOUSE=COMPUTE_WH
SNOWFLAKE_DATABASE=KAREO
SNOWFLAKE_SCHEMA=TALISMANSOLUTIONS

# Database Credentials
DB_NAME=tebra_dw
DB_USER=tebra_user
DB_PASSWORD=tebra_password
DB_HOST=localhost
DB_PORT=5432
```

### 4. Frontend Setup
Install Node dependencies:
```bash
cd apps/web
npm install
```

## 🏃‍♂️ Running the Application

### 1. Start the Data Pipeline (Optional for new setups)
If starting fresh, run the backfill script to populate your local database:
```bash
# From project root
python data-pipeline/scripts/run_backfill.py
```
*Note: This pulls data for a test practice from 2024-01-01 to present.*

### 2. Start the Backend API
```bash
# From project root
./start_dev.sh
# OR manually:
uvicorn apps.api.app.main:app --reload --port 8000
```
API Documentation will be available at: http://localhost:8000/docs

### 3. Start the Frontend
```bash
# In a new terminal, from apps/web
npm run dev
```
Access the application at: http://localhost:5173

## 🧪 Testing

We strictly maintain test coverage across all layers.

### Backend Tests (FastAPI)
Comprehensive integration tests running against the local DB:
```bash
pytest apps/api/tests/test_api_comprehensive.py
```

### Pipeline Tests (ETL Logic)
Tests validating extraction/transformation logic with mocked Snowflake/Postgres:
```bash
pytest data-pipeline/tests/test_pipeline_comprehensive.py
```

### Frontend Tests (React)
Unit and interaction tests using Vitest & React Testing Library:
```bash
cd apps/web
npm test
```

## 📂 Project Structure

```
.
├── apps
│   ├── api                 # FastAPI Backend
│   │   ├── app             # App Logic (Routes, Models)
│   │   └── tests           # API Integration Tests
│   └── web                 # React Frontend
│       ├── src             # Components, Pages, Hooks
│       └── tests           # Frontend Unit Tests
├── data-pipeline           # ETL Logic
│   ├── extraction          # Snowflake Query Scripts
│   ├── loading             # Postgres Loading Scripts
│   ├── scripts             # Orchestration Scripts
│   └── tests               # Pipeline Logic Tests
├── database                # SQL Schemas & Migrations
└── requirements.txt        # Python Dependencies
```

## 🤝 Contribution Guidelines

1.  **Tests Required**: All new features must include accompanying tests.
2.  **Linting**: Ensure code is formatted (Black/Flake8 for Python, Prettier/ESLint for JS).
3.  **PR Process**: Submit PRs with a clear description of changes and screenshot/log proof of testing.

## 📄 License

Proprietary & Confidential - Tebra
