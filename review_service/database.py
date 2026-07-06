import time
import psycopg2
from psycopg2 import OperationalError
from review_service.config import DATABASE_URL


def get_connection():
    retries = 15

    while retries > 0:
        try:
            conn = psycopg2.connect(DATABASE_URL)
            print("✅ Connected to PostgreSQL")
            return conn

        except OperationalError as e:
            retries -= 1
            print(f"⏳ Waiting for PostgreSQL... {15 - retries}/15")
            print(e)
            time.sleep(2)

    raise Exception("Could not connect to PostgreSQL.")


def init_db():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS reviews (
                    id UUID PRIMARY KEY,
                    prompt_id UUID NOT NULL,
                    prompt_snapshot TEXT NOT NULL,
                    reviewer_name VARCHAR(255) NOT NULL,
                    score INTEGER NOT NULL
                        CHECK (score >= 1 AND score <= 5),
                    feedback TEXT NOT NULL,
                    reviewed_at TIMESTAMP NOT NULL
                );
                """
            )
            cur.execute(
                """
                ALTER TABLE reviews
                ADD COLUMN IF NOT EXISTS target_type VARCHAR(10)
                    NOT NULL DEFAULT 'prompt';
                """
            )
            cur.execute(
                """
                ALTER TABLE reviews
                ADD COLUMN IF NOT EXISTS chat_id UUID;
                """
            )
            cur.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_reviews_prompt_id
                ON reviews(prompt_id);
                """
            )
            cur.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_reviews_chat_id
                ON reviews(chat_id);
                """
            )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
