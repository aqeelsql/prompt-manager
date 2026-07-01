import json
from datetime import datetime
from uuid import uuid4

from review_service.database import get_connection

REVIEW_COLUMNS = """
    id, target_type, prompt_id, chat_id, prompt_snapshot,
    reviewer_name, score, feedback, reviewed_at
"""


def create_review(data, prompt_id, snapshot):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            review_id = str(uuid4())
            now = datetime.now()
            stored_snapshot = (
                json.dumps(snapshot, default=str)
                if data.target_type == "chat"
                else str(snapshot)
            )
            cur.execute(
                f"""
                INSERT INTO reviews
                    (id, target_type, prompt_id, chat_id, prompt_snapshot,
                     reviewer_name, score, feedback, reviewed_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING {REVIEW_COLUMNS};
                """,
                (
                    review_id,
                    data.target_type,
                    str(prompt_id),
                    str(data.chat_id) if data.chat_id else None,
                    stored_snapshot,
                    data.reviewer_name,
                    data.score,
                    data.feedback,
                    now,
                ),
            )
            row = cur.fetchone()
        conn.commit()
        return row
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_all_reviews(prompt_id=None, chat_id=None, target_type=None):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            conditions = []
            params = []
            if prompt_id:
                conditions.append("prompt_id = %s")
                params.append(str(prompt_id))
            if chat_id:
                conditions.append("chat_id = %s")
                params.append(str(chat_id))
            if target_type:
                conditions.append("target_type = %s")
                params.append(target_type)

            query = f"SELECT {REVIEW_COLUMNS} FROM reviews"
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            query += " ORDER BY reviewed_at DESC;"
            cur.execute(query, tuple(params))
            return cur.fetchall()
    finally:
        conn.close()


def get_review_by_id(review_id):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT {REVIEW_COLUMNS}
                FROM reviews
                WHERE id = %s;
                """,
                (str(review_id),),
            )
            return cur.fetchone()
    finally:
        conn.close()


def delete_review(review_id):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM reviews WHERE id = %s RETURNING id;",
                (str(review_id),),
            )
            row = cur.fetchone()
        conn.commit()
        return row is not None
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
