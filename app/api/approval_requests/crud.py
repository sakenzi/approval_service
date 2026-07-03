import hashlib
import json
from datetime import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from model.models import ApprovalDecision, ApprovalRequest


def _build_request_hash(workspace_id: str, payload: dict, actor_user_id: str) -> str:
    normalized = "|".join(
        [
            workspace_id,
            str(payload.get("sourceType", "")),
            str(payload.get("sourceId", "")),
            str(payload.get("title", "")),
            str(payload.get("description") or ""),
            ",".join(sorted(payload.get("reviewerUserIds", []))),
            actor_user_id,
        ]
    )
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


async def create_approval_request(
    db: AsyncSession,
    workspace_id: str,
    actor_user_id: str,
    data: dict,
) -> ApprovalRequest:
    request_hash = _build_request_hash(workspace_id, data, actor_user_id)
    existing = await db.scalar(
        select(ApprovalRequest).where(
            ApprovalRequest.workspace_id == workspace_id,
            ApprovalRequest.request_hash == request_hash,
        )
    )
    if existing is not None:
        return existing

    approval_request = ApprovalRequest(
        workspace_id=workspace_id,
        source_type=data["sourceType"],
        source_id=data["sourceId"],
        title=data["title"],
        description=data.get("description"),
        reviewer_user_ids=json.dumps(data.get("reviewerUserIds", [])),
        created_by_user_id=actor_user_id,
        request_hash=request_hash,
        status="pending",
    )
    approval_request.decisions = []
    db.add(approval_request)
    await db.commit()
    await db.refresh(approval_request)
    return approval_request


async def list_approval_requests(db: AsyncSession, workspace_id: str) -> list[ApprovalRequest]:
    result = await db.execute(
        select(ApprovalRequest)
        .where(ApprovalRequest.workspace_id == workspace_id)
        .options(selectinload(ApprovalRequest.decisions))
        .order_by(ApprovalRequest.created_at.desc())
    )
    return list(result.scalars().all())


async def get_approval_request(db: AsyncSession, workspace_id: str, request_id: str) -> Optional[ApprovalRequest]:
    result = await db.execute(
        select(ApprovalRequest)
        .where(ApprovalRequest.workspace_id == workspace_id, ApprovalRequest.id == request_id)
        .options(selectinload(ApprovalRequest.decisions))
    )
    return result.scalar_one_or_none()


async def apply_decision(
    db: AsyncSession,
    workspace_id: str,
    request_id: str,
    actor_user_id: str,
    decision: str,
    comment: Optional[str] = None,
    reason: Optional[str] = None,
) -> ApprovalRequest:
    request = await get_approval_request(db, workspace_id, request_id)
    if request is None:
        raise ValueError("approval_request_not_found")
    if request.status in {"approved", "rejected", "canceled"}:
        return request

    request.status = decision
    request.updated_at = datetime.utcnow()
    decision_record = ApprovalDecision(
        approval_request_id=request.id,
        workspace_id=workspace_id,
        decision=decision,
        actor_user_id=actor_user_id,
        comment=comment,
        reason=reason,
    )
    db.add(decision_record)
    await db.commit()
    await db.refresh(request)
    return request
