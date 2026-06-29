from uuid import uuid4
from datetime import datetime
from review_service.database import get_connection

def create_review(data, prompt_snapshot):
    conn = get_connection()
    cur = conn.cursor()

    review_id = str(uuid4())
    now = datetime.now()

    cur.execute("""
        INSERT INTO reviews
        (id, prompt_id, prompt_snapshot, reviewer_name, score, feedback, reviewed_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        RETURNING *;
    """, (
        review_id,
        str(data.prompt_id),
        prompt_snapshot,
        data.reviewer_name,
        data.score,
        data.feedback,
        now
    ))

    row = cur.fetchone()
    conn.commit()

    cur.close()
    conn.close()

    return row

def get_all_reviews(prompt_id=None):
    conn = get_connection()
    cur = conn.cursor()

    if prompt_id:
        cur.execute("""
            SELECT * FROM reviews
            WHERE prompt_id = %s
            ORDER BY reviewed_at DESC;
        """, (str(prompt_id),))
    else:
        cur.execute("""
            SELECT * FROM reviews
            ORDER BY reviewed_at DESC;
        """)

    rows = cur.fetchall()

    cur.close()
    conn.close()

    return rows

def get_review_by_id(review_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM reviews WHERE id = %s;", (str(review_id),))
    row = cur.fetchone()

    cur.close()
    conn.close()

    return row