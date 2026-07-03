from datetime import datetime
from typing import List, Literal, Optional
from pydantic import BaseModel, Field


class ApprovalRequestCreate(BaseModel):
    sourceType: Literal["publication", "scenario", "edit", "external"] = Field(...)
    sourceId: str = Field(..., min_length=1, max_length=255)
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    reviewerUserIds: List[str] = Field(default_factory=list)


class ApprovalDecisionRequest(BaseModel):
    comment: Optional[str] = None
    reason: Optional[str] = None


class ApprovalDecisionResponse(BaseModel):
    id: str
    decision: str
    actorUserId: str
    comment: Optional[str] = None
    reason: Optional[str] = None
    createdAt: datetime


class ApprovalRequestResponse(BaseModel):
    id: str
    workspaceId: str
    sourceType: str
    sourceId: str
    title: str
    description: Optional[str] = None
    reviewerUserIds: List[str]
    status: str
    createdByUserId: str
    createdAt: datetime
    updatedAt: datetime
    decisions: List[ApprovalDecisionResponse] = Field(default_factory=list)


class ApprovalRequestListResponse(BaseModel):
    items: List[ApprovalRequestResponse]
    total: int
