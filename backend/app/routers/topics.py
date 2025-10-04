from typing import List

from fastapi import APIRouter

from ..db import db
from ..models import SubTopic, Topic


router = APIRouter(prefix="/topics", tags=["topics"])


@router.get("/", response_model=List[Topic])
async def list_topics():
    rows = await db.fetch("SELECT id, name FROM topics ORDER BY name ASC")
    return [Topic(id=r["id"], name=r["name"]) for r in rows]


@router.get("/{topic_id}/sub_topics", response_model=List[SubTopic])
async def list_sub_topics(topic_id: int):
    rows = await db.fetch(
        "SELECT id, name, topic_id FROM sub_topics WHERE topic_id = $1 ORDER BY name ASC",
        topic_id,
    )
    return [SubTopic(id=r["id"], name=r["name"], topic_id=r["topic_id"]) for r in rows]


