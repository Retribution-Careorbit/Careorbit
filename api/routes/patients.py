from fastapi import APIRouter, Request

import api.middleware.auth as auth_mod
import api.middleware.rbac as rbac_mod
from graph.phig_builder import phig_builder

router = APIRouter(prefix="/api/patients", tags=["patients"])


@router.get("/overview")
async def get_overview(request: Request):
    current_user = await auth_mod.get_current_user(request)
    patient_id = request.query_params.get("patient_id", current_user["id"])
    await rbac_mod.verify_patient_access(current_user["id"], patient_id)
    graph = await phig_builder.get_full_patient_graph(patient_id)
    return graph


@router.get("/medications")
async def get_medications(request: Request):
    current_user = await auth_mod.get_current_user(request)
    patient_id = request.query_params.get("patient_id", current_user["id"])
    await rbac_mod.verify_patient_access(current_user["id"], patient_id)
    meds = await phig_builder.get_medication_subgraph(patient_id)
    return meds
