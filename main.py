import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="CareOrbit", version="0.3.0")

_default_origins = [
    "http://localhost:5000",
    "http://127.0.0.1:5000",
    "http://localhost:3000",
]
_replit_domain = os.environ.get("REPLIT_DEV_DOMAIN", "")
if _replit_domain:
    _default_origins.append(f"https://{_replit_domain}")
_extra = os.environ.get("CORS_ORIGINS", "")
if _extra:
    _default_origins.extend([o.strip() for o in _extra.split(",") if o.strip()])

app.add_middleware(
    CORSMiddleware,
    allow_origins=_default_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from api.routes.auth import router as auth_router
from api.routes.health import router as health_router
from api.routes.documents import router as documents_router
from api.routes.patients import router as patients_router
from api.routes.confirmations import router as confirmations_router
from api.routes.caregivers import router as caregivers_router
from api.routes.summary import router as summary_router
from api.routes.reminders import router as reminders_router
from api.routes.subscriptions import router as subscriptions_router
from api.routes.chat import router as chat_router
from api.routes.tests import router as tests_router
from api.routes.orbit import router as orbit_router

app.include_router(auth_router)
app.include_router(health_router)
app.include_router(documents_router)
app.include_router(patients_router)
app.include_router(confirmations_router)
app.include_router(caregivers_router)
app.include_router(summary_router)
app.include_router(reminders_router)
app.include_router(subscriptions_router)
app.include_router(chat_router)
app.include_router(tests_router)
app.include_router(orbit_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
