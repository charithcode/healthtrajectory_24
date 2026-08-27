from datetime import datetime, timezone

@router.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "health-trajectory-api",
        "version": "1.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
