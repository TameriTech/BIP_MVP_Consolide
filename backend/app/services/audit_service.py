import uuid

from sqlalchemy.orm import Session

from app.models.audit import AuditEvent


def log(
    db: Session,
    *,
    actor_user_id: uuid.UUID | None,
    actor_role: str | None,
    action: str,
    entity_type: str,
    entity_id: uuid.UUID | str | int | None = None,
    metadata: dict | None = None,
) -> AuditEvent:
    event = AuditEvent(
        actor_user_id=actor_user_id, actor_role=actor_role, action=action, entity_type=entity_type,
        entity_id=str(entity_id) if entity_id is not None else None, event_metadata=metadata,
    )
    db.add(event)
    db.flush()
    return event
