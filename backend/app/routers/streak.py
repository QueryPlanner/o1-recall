from datetime import date, timedelta

from fastapi import APIRouter

from ..config import load_settings
from ..db import db
from ..models import StreakResponse


router = APIRouter(prefix="/streak", tags=["streak"])
settings = load_settings()
DEFAULT_USER_ID = settings["DEFAULT_USER_ID"]


@router.get("/", response_model=StreakResponse)
async def get_streak():
    today = date.today()

    # Today's answer count (uses composite index on (user_id, answered_at))
    today_count = await db.fetchval(
        """
        SELECT COUNT(*)::int
        FROM user_answers
        WHERE user_id = $1
          AND answered_at >= $2::date
          AND answered_at < ($2::date + INTERVAL '1 day')
        """,
        DEFAULT_USER_ID,
        today,
    )

    # Compute consecutive days streak where each day has at least 5 answers.
    # Strategy: build daily counts, starting at today and walking backward only
    # until a day fails the threshold, but do it in SQL to avoid per-day roundtrips.
    row = await db.fetchval(
        """
        WITH daily AS (
            SELECT date_trunc('day', answered_at)::date AS day, COUNT(*)::int AS cnt
            FROM user_answers
            WHERE user_id = $1
            GROUP BY 1
        ),
        flagged AS (
            SELECT day,
                   CASE WHEN cnt >= 5 THEN 0 ELSE 1 END AS broken
            FROM daily
        ),
        gaps AS (
            SELECT day,
                   SUM(broken) OVER (ORDER BY day DESC ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS grp
            FROM flagged
            WHERE day <= $2::date
        )
        SELECT COALESCE(COUNT(*), 0)::int
        FROM gaps
        WHERE grp = 0
          AND day >= $2::date - INTERVAL '365 days'
        """,
        DEFAULT_USER_ID,
        today,
    )
    streak_days = int(row or 0)

    return StreakResponse(current_streak_days=streak_days, today_answers_count=today_count)


