from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import dashboard, practices, financial, patients, financial_metrics, encounters, claims, eras, search, analytics, reports

app = FastAPI(
    title="Talisman Healthcare Analytics",
    description="Healthcare revenue cycle and encounter management platform",
    version="1.0.0"
)

# CORS Configuration for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://192.168.4.45:5173"],  # Vite dev server (local & LAN)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["Dashboard"])
app.include_router(practices.router, prefix="/api/practices", tags=["Practices"])
app.include_router(financial.router, prefix="/api/financial", tags=["Financial"])
app.include_router(patients.router, prefix="/api/patients", tags=["Patients"])
app.include_router(financial_metrics.router, prefix="/api", tags=["Financial Metrics"])
app.include_router(encounters.router, prefix="/api/encounters", tags=["Encounters"])
app.include_router(claims.router, prefix="/api/claims", tags=["Claims"])
app.include_router(eras.router, prefix="/api/eras", tags=["Electronic Remittance"])
app.include_router(search.router, prefix="/api/search", tags=["Global Search"])
app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["Analytics"])
app.include_router(reports.router, prefix="/api/v1/reports", tags=["Reports"])

@app.get("/")
async def root():
    return {
        "app": "Talisman Healthcare Analytics",
        "version": "1.0.0",
        "status": "active"
    }

@app.get("/api/health")
async def health_check():
    return {"status": "healthy"}
