from typing import List
import time
import logging

from fastapi import APIRouter, HTTPException, Query

from ..config import load_settings
from ..db import db
from ..models import AnswerRequest, AnswerResponse, Question, Choice

logger = logging.getLogger("app.routers.questions")


router = APIRouter(prefix="", tags=["questions"])
settings = load_settings()
DEFAULT_USER_ID = settings["DEFAULT_USER_ID"]


async def _fetch_question_bundle(question_ids: List[int]) -> List[Question]:
    if not question_ids:
        return []
    rows = await db.fetch(
        "SELECT id, sub_topic_id, question_text, explanation, image_url FROM questions WHERE id = ANY($1)",
        question_ids,
    )
    choices_rows = await db.fetch(
        "SELECT id, question_id, choice_text, is_correct FROM choices WHERE question_id = ANY($1)",
        question_ids,
    )
    by_qid = {}
    for r in rows:
        by_qid[r["id"]] = {
            "q": r,
            "choices": [],
        }
    for c in choices_rows:
        by_qid[c["question_id"]]["choices"].append(c)
    result: List[Question] = []
    for qid in question_ids:
        data = by_qid.get(qid)
        if not data:
            continue
        q = data["q"]
        result.append(
            Question(
                id=q["id"],
                sub_topic_id=q["sub_topic_id"],
                question_text=q["question_text"],
                explanation=q["explanation"],
                image_url=q["image_url"],
                choices=[
                    Choice(
                        id=c["id"],
                        question_id=c["question_id"],
                        choice_text=c["choice_text"],
                        is_correct=c["is_correct"],
                    )
                    for c in data["choices"]
                ],
            )
        )
    return result


@router.get("/sub_topics/{sub_topic_id}/questions", response_model=List[Question])
async def sample_questions_for_sub_topic(sub_topic_id: int, limit: int = Query(5, ge=1, le=50)):
    # Single-query approach to eliminate multiple roundtrips to Neon cloud DB
    rows = await db.fetch(
        """
        WITH answered AS (
            SELECT question_id FROM user_answers WHERE user_id = $2
        ),
        sampled AS (
            SELECT q.id
            FROM questions q TABLESAMPLE SYSTEM (50)
            WHERE q.sub_topic_id = $1
              AND NOT EXISTS (SELECT 1 FROM answered a WHERE a.question_id = q.id)
            LIMIT $3
        ),
        fallback AS (
            SELECT q.id
            FROM questions q
            WHERE q.sub_topic_id = $1
              AND NOT EXISTS (SELECT 1 FROM answered a WHERE a.question_id = q.id)
              AND NOT EXISTS (SELECT 1 FROM sampled s WHERE s.id = q.id)
            ORDER BY q.id
            LIMIT GREATEST(0, $3 - (SELECT COUNT(*) FROM sampled))
        ),
        final_ids AS (
            SELECT id FROM sampled
            UNION ALL
            SELECT id FROM fallback
        )
        SELECT q.id, q.sub_topic_id, q.question_text, q.explanation, q.image_url,
               c.id as choice_id, c.choice_text, c.is_correct
        FROM final_ids f
        JOIN questions q ON q.id = f.id
        JOIN choices c ON c.question_id = q.id
        ORDER BY q.id, c.id
        LIMIT $3 * 10
        """,
        sub_topic_id,
        DEFAULT_USER_ID,
        limit,
    )
    
    # Group by question_id
    by_qid: dict = {}
    for r in rows:
        qid = int(r["id"])
        if qid not in by_qid:
            by_qid[qid] = {
                "q": {"id": int(r["id"]), "sub_topic_id": int(r["sub_topic_id"]), 
                      "question_text": str(r["question_text"]), "explanation": r["explanation"],
                      "image_url": r["image_url"]},
                "choices": []
            }
        choices_list: list = by_qid[qid]["choices"]
        choices_list.append({
            "id": int(r["choice_id"]), "question_id": qid,
            "choice_text": str(r["choice_text"]), "is_correct": bool(r["is_correct"])
        })
    
    result: List[Question] = []
    for qid in list(by_qid.keys())[:limit]:
        data = by_qid[qid]
        q = data["q"]
        result.append(
            Question(
                id=q["id"],
                sub_topic_id=q["sub_topic_id"],
                question_text=q["question_text"],
                explanation=q["explanation"],
                image_url=q["image_url"],
                choices=[Choice(**c) for c in data["choices"]],
            )
        )
    
    return result


@router.get("/questions/random", response_model=List[Question])
async def sample_questions_random(limit: int = Query(5, ge=1, le=50)):
    t0 = time.perf_counter()
    
    # Single-query approach: fetch everything in one roundtrip using CTE
    # This eliminates multiple network roundtrips to Neon cloud DB
    rows = await db.fetch(
        """
        WITH answered AS (
            SELECT question_id FROM user_answers WHERE user_id = $1
        ),
        sampled AS (
            SELECT q.id
            FROM questions q TABLESAMPLE SYSTEM (50)
            WHERE NOT EXISTS (SELECT 1 FROM answered a WHERE a.question_id = q.id)
            LIMIT $2
        ),
        fallback AS (
            SELECT q.id
            FROM questions q
            WHERE NOT EXISTS (SELECT 1 FROM answered a WHERE a.question_id = q.id)
              AND NOT EXISTS (SELECT 1 FROM sampled s WHERE s.id = q.id)
            ORDER BY q.id
            LIMIT GREATEST(0, $2 - (SELECT COUNT(*) FROM sampled))
        ),
        final_ids AS (
            SELECT id FROM sampled
            UNION ALL
            SELECT id FROM fallback
        )
        SELECT q.id, q.sub_topic_id, q.question_text, q.explanation, q.image_url,
               c.id as choice_id, c.choice_text, c.is_correct
        FROM final_ids f
        JOIN questions q ON q.id = f.id
        JOIN choices c ON c.question_id = q.id
        ORDER BY q.id, c.id
        LIMIT $2 * 10
        """,
        DEFAULT_USER_ID,
        limit,
    )
    
    t1 = time.perf_counter()
    logger.info(f"Single-query fetch completed in {(t1-t0)*1000:.1f}ms, returned {len(rows)} rows")
    
    # Group by question_id in Python
    by_qid: dict = {}
    for r in rows:
        qid = int(r["id"])
        if qid not in by_qid:
            by_qid[qid] = {
                "q": {"id": int(r["id"]), "sub_topic_id": int(r["sub_topic_id"]), 
                      "question_text": str(r["question_text"]), "explanation": r["explanation"],
                      "image_url": r["image_url"]},
                "choices": []
            }
        choices_list: list = by_qid[qid]["choices"]
        choices_list.append({
            "id": int(r["choice_id"]), "question_id": qid,
            "choice_text": str(r["choice_text"]), "is_correct": bool(r["is_correct"])
        })
    
    result: List[Question] = []
    for qid in list(by_qid.keys())[:limit]:
        data = by_qid[qid]
        q = data["q"]
        result.append(
            Question(
                id=q["id"],
                sub_topic_id=q["sub_topic_id"],
                question_text=q["question_text"],
                explanation=q["explanation"],
                image_url=q["image_url"],
                choices=[Choice(**c) for c in data["choices"]],
            )
        )
    
    t2 = time.perf_counter()
    logger.info(f"Total time: {(t2-t0)*1000:.1f}ms for {len(result)} questions")
    
    return result


@router.post("/answers", response_model=AnswerResponse)
async def submit_answer(payload: AnswerRequest):
    choice = await db.fetchrow(
        "SELECT id, question_id, is_correct FROM choices WHERE id = $1",
        payload.choice_id,
    )
    if not choice or choice["question_id"] != payload.question_id:
        raise HTTPException(status_code=400, detail="invalid_choice")

    is_correct = bool(choice["is_correct"])
    correct_choice_id = await db.fetchval(
        "SELECT id FROM choices WHERE question_id = $1 AND is_correct = TRUE",
        payload.question_id,
    )
    await db.execute(
        """
        INSERT INTO user_answers (user_id, question_id, choice_id, is_correct)
        VALUES ($1, $2, $3, $4)
        """,
        DEFAULT_USER_ID,
        payload.question_id,
        payload.choice_id,
        is_correct,
    )
    return AnswerResponse(is_correct=is_correct, correct_choice_id=int(correct_choice_id))


