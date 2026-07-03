import json

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.approval_requests.commands import emit_event, validate_workspace_context
from app.api.approval_requests.crud import apply_decision, create_approval_request, get_approval_request, list_approval_requests
from app.api.approval_requests.schemas import ApprovalDecisionRequest, ApprovalDecisionResponse, ApprovalRequestCreate, ApprovalRequestListResponse, ApprovalRequestResponse
from database.db import get_db

router = APIRouter(prefix="/v1/workspaces", tags=["approval-requests"])


async def require_auth(
    workspace_id: str,
    x_workspace_id: str | None = Header(default=None, alias="X-Workspace-Id"),
    x_user_id: str | None = Header(default=None, alias="X-User-Id"),
    x_user_actions: str | None = Header(default=None, alias="X-User-Actions"),
) -> tuple[str, str, set[str]]:
    validate_workspace_context(workspace_id, x_workspace_id)
    if not x_user_id:
        raise HTTPException(status_code=401, detail="Missing user identity")
    actions = {action.strip() for action in (x_user_actions or "").split(",") if action.strip()}
    return x_user_id, workspace_id, actions


@router.post("/{workspace_id}/approval-requests", response_model=ApprovalRequestResponse, status_code=201)
async def create_approval_request_endpoint(
    request: Request,
    workspace_id: str,
    payload: ApprovalRequestCreate,
    auth_context: tuple[str, str, set[str]] = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    actor_user_id, resolved_workspace_id, actions = auth_context
    if "approval:create" not in actions:
        raise HTTPException(status_code=403, detail="Missing approval:create permission")

    approval_request = await create_approval_request(
        db,
        resolved_workspace_id,
        actor_user_id,
        payload.model_dump(),
    )
    emit_event("approval.request.created", {
        "workspaceId": resolved_workspace_id,
        "requestId": approval_request.id,
        "status": approval_request.status,
        "sourceType": approval_request.source_type,
        "actorUserId": actor_user_id,
    })
    await db.commit()
    return _serialize_request(approval_request)


@router.get("/{workspace_id}/approval-requests", response_model=ApprovalRequestListResponse)
async def list_approval_requests_endpoint(
    workspace_id: str,
    auth_context: tuple[str, str, set[str]] = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    _, resolved_workspace_id, actions = auth_context
    if "approval:read" not in actions:
        raise HTTPException(status_code=403, detail="Missing approval:read permission")

    items = await list_approval_requests(db, resolved_workspace_id)
    return ApprovalRequestListResponse(items=[_serialize_request(item) for item in items], total=len(items))


@router.get("/{workspace_id}/approval-requests/{request_id}", response_model=ApprovalRequestResponse)
async def get_approval_request_endpoint(
    workspace_id: str,
    request_id: str,
    auth_context: tuple[str, str, set[str]] = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    _, resolved_workspace_id, actions = auth_context
    if "approval:read" not in actions:
        raise HTTPException(status_code=403, detail="Missing approval:read permission")

    approval_request = await get_approval_request(db, resolved_workspace_id, request_id)
    if approval_request is None:
        raise HTTPException(status_code=404, detail="approval request not found")
    return _serialize_request(approval_request)


@router.post("/{workspace_id}/approval-requests/{request_id}/approve", response_model=ApprovalRequestResponse)
async def approve_approval_request_endpoint(
    workspace_id: str,
    request_id: str,
    payload: ApprovalDecisionRequest,
    auth_context: tuple[str, str, set[str]] = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    actor_user_id, resolved_workspace_id, actions = auth_context
    if "approval:decide" not in actions:
        raise HTTPException(status_code=403, detail="Missing approval:decide permission")

    try:
        approval_request = await apply_decision(
            db,
            resolved_workspace_id,
            request_id,
            actor_user_id,
            "approved",
            comment=payload.comment,
            reason=None,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    emit_event("approval.request.decided", {
        "workspaceId": resolved_workspace_id,
        "requestId": approval_request.id,
        "status": approval_request.status,
        "sourceType": approval_request.source_type,
        "actorUserId": actor_user_id,
    })
    return _serialize_request(approval_request)


@router.post("/{workspace_id}/approval-requests/{request_id}/reject", response_model=ApprovalRequestResponse)
async def reject_approval_request_endpoint(
    workspace_id: str,
    request_id: str,
    payload: ApprovalDecisionRequest,
    auth_context: tuple[str, str, set[str]] = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    actor_user_id, resolved_workspace_id, actions = auth_context
    if "approval:decide" not in actions:
        raise HTTPException(status_code=403, detail="Missing approval:decide permission")

    try:
        approval_request = await apply_decision(
            db,
            resolved_workspace_id,
            request_id,
            actor_user_id,
            "rejected",
            comment=None,
            reason=payload.reason,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    emit_event("approval.request.decided", {
        "workspaceId": resolved_workspace_id,
        "requestId": approval_request.id,
        "status": approval_request.status,
        "sourceType": approval_request.source_type,
        "actorUserId": actor_user_id,
    })
    return _serialize_request(approval_request)


@router.post("/{workspace_id}/approval-requests/{request_id}/cancel", response_model=ApprovalRequestResponse)
async def cancel_approval_request_endpoint(
    workspace_id: str,
    request_id: str,
    payload: ApprovalDecisionRequest,
    auth_context: tuple[str, str, set[str]] = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    actor_user_id, resolved_workspace_id, actions = auth_context
    if "approval:cancel" not in actions:
        raise HTTPException(status_code=403, detail="Missing approval:cancel permission")

    try:
        approval_request = await apply_decision(
            db,
            resolved_workspace_id,
            request_id,
            actor_user_id,
            "canceled",
            comment=None,
            reason=payload.reason,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    emit_event("approval.request.canceled", {
        "workspaceId": resolved_workspace_id,
        "requestId": approval_request.id,
        "status": approval_request.status,
        "sourceType": approval_request.source_type,
        "actorUserId": actor_user_id,
    })
    return _serialize_request(approval_request)


def _serialize_request(approval_request) -> ApprovalRequestResponse:
    reviewer_user_ids = []
    if approval_request.reviewer_user_ids:
        try:
            reviewer_user_ids = json.loads(approval_request.reviewer_user_ids)
        except (TypeError, ValueError):
            reviewer_user_ids = [approval_request.reviewer_user_ids]

    try:
        decisions = list(approval_request.decisions or [])
    except Exception:
        decisions = []

    return ApprovalRequestResponse(
        id=approval_request.id,
        workspaceId=approval_request.workspace_id,
        sourceType=approval_request.source_type,
        sourceId=approval_request.source_id,
        title=approval_request.title,
        description=approval_request.description,
        reviewerUserIds=reviewer_user_ids,
        status=approval_request.status,
        createdByUserId=approval_request.created_by_user_id,
        createdAt=approval_request.created_at,
        updatedAt=approval_request.updated_at,
        decisions=[
            ApprovalDecisionResponse(
                id=decision.id,
                decision=decision.decision,
                actorUserId=decision.actor_user_id,
                comment=decision.comment,
                reason=decision.reason,
                createdAt=decision.created_at,
            )
            for decision in decisions
        ],
    )
