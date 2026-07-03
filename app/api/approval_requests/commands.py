import logging
from typing import Any, Dict, Optional

logger = logging.getLogger("approval_service")


def build_sanitized_event(event_name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "event": event_name,
        "workspaceId": payload.get("workspaceId"),
        "requestId": payload.get("requestId"),
        "status": payload.get("status"),
        "sourceType": payload.get("sourceType"),
        "actorUserId": payload.get("actorUserId"),
    }


def emit_event(event_name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    event = build_sanitized_event(event_name, payload)
    logger.info("Emitting event %s %s", event_name, event)
    return event


def validate_workspace_context(path_workspace_id: str, header_workspace_id: Optional[str]) -> None:
    if not header_workspace_id:
        raise ValueError("workspace_header_missing")
    if path_workspace_id != header_workspace_id:
        raise ValueError("workspace_header_mismatch")
