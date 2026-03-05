from fastapi import FastAPI

app = FastAPI(title="CareOrbit", version="0.3.0")

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
