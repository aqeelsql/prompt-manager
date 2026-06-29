import psycopg2
from review_service.config import DATABASE_URL

def get_connection():
    return psycopg2.connect(DATABASE_URL)

def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS reviews (
            id UUID PRIMARY KEY,
            prompt_id UUID NOT NULL,
            prompt_snapshot TEXT NOT NULL,
            reviewer_name VARCHAR(255) NOT NULL,
            score INTEGER NOT NULL CHECK (score >= 1 AND score <= 5),
            feedback TEXT NOT NULL,
            reviewed_at TIMESTAMP NOT NULL
        );
    """)

    conn.commit()
    cur.close()
    conn.close()