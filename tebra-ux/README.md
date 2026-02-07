# Talisman Healthcare Analytics Platform

A modern, reusable web application scaffold for healthcare analytics built with FastAPI and React.

## 🎨 Design System

This application uses the **Talisman Solutions** design system:
- **Colors**: Dark Slate Blue primary (#0f172a) with Surgical Teal accent (#0d9488)
- **Typography**: Plus Jakarta Sans (headings) and DM Sans (body)
- **Layout**: Gmail-style collapsible sidebar navigation
- **Components**: Reusable cards, tables, stats, and buttons

## 🏗️ Architecture

### Backend (FastAPI)
- **Framework**: FastAPI with async support
- **Database**: PostgreSQL (connects to existing `tebra_dw` database)
- **API Endpoints**:
  - `/api/dashboard/metrics` - High-level KPIs
  - `/api/practices/list` - Practice locations
  - `/api/financial/summary` - Financial metrics

### Frontend (React + Vite)
- **Framework**: React 18 with React Router
- **Build Tool**: Vite for fast development
- **Styling**: Vanilla CSS with design system
- **Pages**:
  - **Dashboard**: Metrics overview
  - **Practices**: Practice locations table
  - **Financial**: Financial KPIs

## 🚀 Quick Start

### Prerequisites
- Python 3.12+
- Node.js 18+
- PostgreSQL database (running on localhost:5432)

### Backend Setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

The application will be available at:
- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## 📁 Project Structure

```
tebra-ux/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app entry point
│   │   ├── api/
│   │   │   ├── dashboard.py     # Dashboard endpoints
│   │   │   ├── practices.py     # Practices endpoints
│   │   │   └── financial.py     # Financial endpoints
│   │   └── db/
│   │       └── connection.py    # Database connection pool
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Sidebar.jsx      # Collapsible sidebar
│   │   │   └── Topbar.jsx       # Top navigation bar
│   │   ├── pages/
│   │   │   ├── Dashboard.jsx    # Dashboard page
│   │   │   ├── Practices.jsx    # Practices page
│   │   │   └── Financial.jsx    # Financial page
│   │   ├── App.jsx              # Main app with routing
│   │   ├── main.jsx             # React entry point
│   │   └── index.css            # Global styles (Talisman design system)
│   ├── public/
│   │   └── logo.jpg             # Talisman logo
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
```

## 🎯 Features

### Collapsible Sidebar
- Gmail-style collapsible navigation
- Smooth animations
- Active route highlighting
- Responsive design

### Dashboard
- Real-time metrics from database
- Encounter and claim statistics
- Financial overview
- Collection rate calculation

### Practices View
- List of all practice locations
- Encounter counts per practice
- Sortable table

### Financial Metrics
- Total billed/paid amounts
- Outstanding balance
- Collection rate
- Claim line counts

## 🔧 Configuration

### Database Connection
Edit `backend/app/db/connection.py` to configure database connection:

```python
DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "tebra_dw",
    "user": "postgres",
    "password": "postgres",
}
```

Or use environment variables:
- `DB_HOST`
- `DB_PORT`
- `DB_NAME`
- `DB_USER`
- `DB_PASSWORD`

## 🎨 Customization

### Design System
All design tokens are defined in `frontend/src/index.css`:
- Colors: CSS variables (`--slate-900`, `--accent`, etc.)
- Typography: Font families and sizes
- Spacing: Layout constants
- Components: Reusable component styles

### Adding New Pages
1. Create page component in `frontend/src/pages/YourPage.jsx`
2. Add route to `frontend/src/App.jsx`
3. Add navigation item to `frontend/src/components/Sidebar.jsx`
4. Create corresponding API endpoints in `backend/app/api/yourpage.py`

## 📦 Deployment

### Backend
```bash
pip install gunicorn
gunicorn app.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Frontend
```bash
npm run build
# Serve the dist/ folder with nginx or any static file server
```

## 🔐 Security Notes

- Add authentication middleware before production deployment
- Configure CORS origins in `backend/app/main.py`
- Use environment variables for sensitive configuration
- Enable HTTPS in production

## 📄 License

Copyright © 2025 Talisman Solutions. All rights reserved.

---

**Talisman Healthcare Analytics** - Achieve Financial Velocity
