"""In-app notification endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import DbSession
from app.schemas.notifications import NotificationSchema
from app.notifications.service import NotificationService

router = APIRouter(prefix="/notifications", tags=["Notifications"])


def get_notification_service(db: DbSession) -> NotificationService:
    return NotificationService(db)


NotifySvc = Annotated[NotificationService, Depends(get_notification_service)]


@router.get("", response_model=list[NotificationSchema])
async def list_notifications(
    svc: NotifySvc, limit: int = 50, unread_only: bool = False
) -> list[NotificationSchema]:
    """List in-app notifications."""
    items = await svc.list_notifications(limit, unread_only)
    return [NotificationSchema(**n) for n in items]


@router.patch("/{notification_id}/read", status_code=204)
async def mark_notification_read(notification_id: int, svc: NotifySvc) -> None:
    """Mark a notification as read."""
    ok = await svc.mark_read(notification_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Notification not found")
    await svc._session.commit()


@router.post("/read-all")
async def mark_all_read(svc: NotifySvc) -> dict:
    """Mark all notifications as read."""
    count = await svc.mark_all_read()
    await svc._session.commit()
    return {"marked_read": count}
