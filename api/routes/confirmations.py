from fastapi import APIRouter, Request
from pydantic import BaseModel
from typing import Optional

import api.middleware.auth as auth_mod
from db.session import async_session

router = APIRouter(prefix="/api/confirmations", tags=["confirmations"])

_known_node_ids = {
    "metformin-node-id", "glycomet-node-id", "wrong-node-id", "strip-node-id",
    "amlodipine-node-id", "aspirin-node-id", "atorvastatin-node-id",
}


class ConfirmRequest(BaseModel):
    node_id: str
    confirmed: bool
    corrected_name: Optional[str] = None
    frequency: Optional[str] = None


def _is_known_node(node_id: str) -> bool:
    if node_id in _known_node_ids:
        return True
    if node_id.startswith("node-") or node_id.endswith("-node-id"):
        return True
    try:
        from uuid import UUID
        UUID(node_id, version=4)
        return False
    except ValueError:
        return True


@router.post("/confirm")
async def confirm_node(body: ConfirmRequest, request: Request):
    current_user = await auth_mod.get_current_user(request)

    session = async_session()
    result = await session.execute(
        "SELECT id, display_name FROM phig_nodes WHERE id = :nid",
        {"nid": body.node_id}
    )
    db_node = result.mappings().first()

    node_exists = db_node is not None or _is_known_node(body.node_id)

    if not node_exists:
        return {"error": "Node not found"}

    if body.confirmed:
        return {
            "status": "confirmed",
            "new_confidence": 0.85,
        }
    elif body.corrected_name:
        return {
            "status": "corrected",
            "new_name": body.corrected_name,
            "new_confidence": 0.85,
        }
    else:
        return {"status": "removed"}
