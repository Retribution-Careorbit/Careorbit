from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
import io

import api.middleware.auth as auth_mod
from api.middleware.rbac import verify_patient_access
from graph.phig_builder import phig_builder
from utils.pdf_generator import generate_health_summary_pdf
from services.azure_blob import AzureBlobService

blob_service = AzureBlobService()

router = APIRouter(prefix="/api/summary", tags=["summary"])


@router.get("/generate")
async def generate_summary(request: Request):
    current_user = await auth_mod.get_current_user(request)
    patient_id = request.query_params.get("patient_id", current_user["id"])

    await verify_patient_access(current_user["id"], patient_id)

    graph_data = await phig_builder.get_full_patient_graph(patient_id)

    total_nodes = 0
    if graph_data and "summary" in graph_data:
        total_nodes = graph_data["summary"].get("total_nodes", 0)

    if total_nodes == 0:
        return {"error": "No health data available to generate summary"}

    pdf_bytes = generate_health_summary_pdf(graph_data)

    try:
        await blob_service.upload_health_summary_pdf(pdf_bytes, f"CareOrbit_Summary_{patient_id}.pdf")
    except (NotImplementedError, Exception):
        pass

    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="CareOrbit_Summary_{patient_id}.pdf"'
        }
    )
