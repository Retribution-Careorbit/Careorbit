import logging

from db.session import async_session


logger = logging.getLogger("careorbit.audit")


async def log_audit(user_id, patient_id, action, request=None, metadata=None):
    ip_address = "unknown"
    if request:
        if hasattr(request, "client") and request.client:
            ip_address = request.client.host
        forwarded = None
        if hasattr(request, "headers"):
            forwarded = request.headers.get("X-Forwarded-For") if hasattr(request.headers, "get") else None
        if forwarded:
            ip_address = forwarded.split(",")[0].strip()

    try:
        async with async_session() as session:
            await session.execute(
                "INSERT INTO audit_log (user_id, patient_id, action, ip_address, metadata) "
                "VALUES (:uid, :pid, :action, :ip, :metadata)",
                {
                    "uid": user_id,
                    "pid": patient_id,
                    "action": action,
                    "ip": ip_address,
                    "metadata": str(metadata) if metadata else None,
                }
            )
            await session.commit()
    except Exception as exc:
        logger.warning(f"Audit log write failed for action {action}: {exc}")
