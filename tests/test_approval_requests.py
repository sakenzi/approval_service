import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from main import app
from database.db import Base, async_engine
from model.models import ApprovalRequest


@pytest_asyncio.fixture
async def client():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.mark.asyncio
async def test_create_and_fetch_approval_request(client):
    response = await client.post(
        "/api/v1/workspaces/ws-1/approval-requests",
        json={
            "sourceType": "publication",
            "sourceId": "pub_123",
            "title": "Instagram reel draft",
            "description": "Needs final approval",
            "reviewerUserIds": ["usr_1", "usr_2"],
        },
        headers={"X-Workspace-Id": "ws-1", "X-User-Id": "usr_1", "X-User-Actions": "approval:create,approval:read"},
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["workspaceId"] == "ws-1"
    assert payload["status"] == "pending"
    assert payload["sourceType"] == "publication"

    list_response = await client.get(
        "/api/v1/workspaces/ws-1/approval-requests",
        headers={"X-Workspace-Id": "ws-1", "X-User-Id": "usr_1", "X-User-Actions": "approval:read"},
    )
    assert list_response.status_code == 200
    assert len(list_response.json()["items"]) == 1

    detail_response = await client.get(
        "/api/v1/workspaces/ws-1/approval-requests/" + payload["id"],
        headers={"X-Workspace-Id": "ws-1", "X-User-Id": "usr_1", "X-User-Actions": "approval:read"},
    )
    assert detail_response.status_code == 200
    assert detail_response.json()["id"] == payload["id"]


@pytest.mark.asyncio
async def test_approve_reject_and_cancel_are_idempotent_and_logged(client):
    create_response = await client.post(
        "/api/v1/workspaces/ws-1/approval-requests",
        json={
            "sourceType": "publication",
            "sourceId": "pub_123",
            "title": "Instagram reel draft",
            "description": "Needs final approval",
            "reviewerUserIds": ["usr_1", "usr_2"],
        },
        headers={"X-Workspace-Id": "ws-1", "X-User-Id": "usr_1", "X-User-Actions": "approval:create,approval:read,approval:decide"},
    )
    request_id = create_response.json()["id"]

    approve_response = await client.post(
        f"/api/v1/workspaces/ws-1/approval-requests/{request_id}/approve",
        json={"comment": "Approved"},
        headers={"X-Workspace-Id": "ws-1", "X-User-Id": "usr_1", "X-User-Actions": "approval:decide"},
    )
    assert approve_response.status_code == 200
    assert approve_response.json()["status"] == "approved"

    second_approve = await client.post(
        f"/api/v1/workspaces/ws-1/approval-requests/{request_id}/approve",
        json={"comment": "Approved again"},
        headers={"X-Workspace-Id": "ws-1", "X-User-Id": "usr_1", "X-User-Actions": "approval:decide"},
    )
    assert second_approve.status_code == 200
    assert second_approve.json()["status"] == "approved"

    async with async_engine.begin() as conn:
        count = await conn.scalar(
            ApprovalRequest.__table__.select().where(ApprovalRequest.id == request_id)
        )

    assert count is not None

    decisions = await client.get(
        f"/api/v1/workspaces/ws-1/approval-requests/{request_id}",
        headers={"X-Workspace-Id": "ws-1", "X-User-Id": "usr_1", "X-User-Actions": "approval:read"},
    )
    assert decisions.status_code == 200
    payload = decisions.json()
    assert payload["decisions"][0]["decision"] == "approved"
    assert payload["decisions"][0]["actorUserId"] == "usr_1"

    reject_response = await client.post(
        f"/api/v1/workspaces/ws-1/approval-requests/{request_id}/reject",
        json={"reason": "Brand tone is wrong"},
        headers={"X-Workspace-Id": "ws-1", "X-User-Id": "usr_1", "X-User-Actions": "approval:decide"},
    )
    assert reject_response.status_code == 200
    assert reject_response.json()["status"] == "approved"

    cancel_response = await client.post(
        f"/api/v1/workspaces/ws-1/approval-requests/{request_id}/cancel",
        json={"reason": "Draft was removed"},
        headers={"X-Workspace-Id": "ws-1", "X-User-Id": "usr_1", "X-User-Actions": "approval:cancel"},
    )
    assert cancel_response.status_code == 200
    assert cancel_response.json()["status"] == "approved"
