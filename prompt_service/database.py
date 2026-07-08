import time
import psycopg2
from psycopg2 import OperationalError

from prompt_service.config import DATABASE_URL


def get_connection():
    retries = 15

    while retries > 0:
        try:
            conn = psycopg2.connect(DATABASE_URL)
            print("Connected to PostgreSQL")
            return conn

        except OperationalError as e:
            retries -= 1
            print(f"Waiting for PostgreSQL... {15 - retries}/15")
            print(e)
            time.sleep(2)

    raise Exception("Could not connect to PostgreSQL.")


def init_db():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS prompts (
                    id UUID PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    description TEXT,
                    content TEXT NOT NULL,
                    tags TEXT,
                    model_target VARCHAR(255),
                    created_at TIMESTAMP NOT NULL,
                    updated_at TIMESTAMP NOT NULL
                );
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS chats (
                    id UUID PRIMARY KEY,
                    prompt_id UUID NOT NULL
                        REFERENCES prompts(id) ON DELETE CASCADE,
                    title VARCHAR(255) NOT NULL,
                    model VARCHAR(255),
                    total_tokens INTEGER NOT NULL DEFAULT 0
                        CHECK (total_tokens >= 0),
                    summary TEXT,
                    created_at TIMESTAMP NOT NULL,
                    updated_at TIMESTAMP NOT NULL
                );
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS messages (
                    id UUID PRIMARY KEY,
                    chat_id UUID NOT NULL
                        REFERENCES chats(id) ON DELETE CASCADE,
                    role VARCHAR(20) NOT NULL
                        CHECK (role IN ('user', 'assistant')),
                    content TEXT NOT NULL,
                    prompt_tokens INTEGER NOT NULL DEFAULT 0
                        CHECK (prompt_tokens >= 0),
                    completion_tokens INTEGER NOT NULL DEFAULT 0
                        CHECK (completion_tokens >= 0),
                    total_tokens INTEGER NOT NULL DEFAULT 0
                        CHECK (total_tokens >= 0),
                    position INTEGER NOT NULL,
                    created_at TIMESTAMP NOT NULL,
                    UNIQUE (chat_id, position)
                );
                """
            )
            cur.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_chats_prompt_id
                ON chats(prompt_id);
                """
            )
            cur.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_messages_chat_position
                ON messages(chat_id, position);
                """
            )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
