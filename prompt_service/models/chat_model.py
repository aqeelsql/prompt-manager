import base64
import json
from datetime import datetime
from uuid import uuid4

from psycopg2.extras import RealDictCursor

from prompt_service.database import get_connection


ATTACHMENT_PREFIX = "[[prompt-manager-attachment:"
ATTACHMENT_SUFFIX = "]]\n"
SYSTEM_PROMPT_PREFIX = "[[prompt-manager-system-prompt]]\n"
ATTACHMENT_FIELDS = (
    "id",
    "filename",
    "file_type",
    "content_type",
    "size_bytes",
    "character_count",
)


def encode_message_content(content, attachment=None):
    """Store attachment metadata without requiring a database schema change."""
    if not attachment:
        return content

    metadata = {
        field: attachment[field]
        for field in ATTACHMENT_FIELDS
        if attachment.get(field) is not None
    }
    payload = base64.urlsafe_b64encode(
        json.dumps(metadata, separators=(",", ":"), default=str).encode("utf-8")
    ).decode("ascii")
    return f"{ATTACHMENT_PREFIX}{payload}{ATTACHMENT_SUFFIX}{content}"


def decode_message_content(content):
    if not content or not content.startswith(ATTACHMENT_PREFIX):
        return content, []

    marker_end = content.find(ATTACHMENT_SUFFIX, len(ATTACHMENT_PREFIX))
    if marker_end == -1:
        return content, []

    payload = content[len(ATTACHMENT_PREFIX):marker_end]
    try:
        padding = "=" * (-len(payload) % 4)
        metadata = json.loads(
            base64.urlsafe_b64decode(payload + padding).decode("utf-8")
        )
    except (ValueError, UnicodeDecodeError, json.JSONDecodeError):
        return content, []

    visible_content = content[marker_end + len(ATTACHMENT_SUFFIX):]
    return visible_content, [metadata] if isinstance(metadata, dict) else []


def encode_llm_role(content, llm_role=None):
    if llm_role == "system":
        return f"{SYSTEM_PROMPT_PREFIX}{content}"
    return content


def decode_llm_role(content, stored_role):
    if content and content.startswith(SYSTEM_PROMPT_PREFIX):
        return content[len(SYSTEM_PROMPT_PREFIX):], "system"
    return content, stored_role


def _fetch_chat(cur, chat_id):
    cur.execute(
        """
        SELECT id, prompt_id, title, model, total_tokens, summary,
               created_at, updated_at
        FROM chats
        WHERE id = %s;
        """,
        (str(chat_id),),
    )
    chat = cur.fetchone()
    if not chat:
        return None

    cur.execute(
        """
        SELECT id, chat_id, role, content, prompt_tokens,
               completion_tokens, total_tokens, position, created_at
        FROM messages
        WHERE chat_id = %s
        ORDER BY position ASC;
        """,
        (str(chat_id),),
    )
    messages = cur.fetchall()
    for message in messages:
        stored_content, message["llm_role"] = decode_llm_role(
            message["content"], message["role"]
        )
        message["content"], message["attachments"] = decode_message_content(
            stored_content
        )
    chat["messages"] = messages
    return chat


def create_chat(
    prompt,
    model=None,
    attachment=None,
    initial_llm_role=None,
):
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            chat_id = str(uuid4())
            now = datetime.now()
            title = prompt["name"][:255]
            selected_model = model

            cur.execute(
                """
                INSERT INTO chats
                    (id, prompt_id, title, model, total_tokens, summary,
                     created_at, updated_at)
                VALUES (%s, %s, %s, %s, 0, NULL, %s, %s);
                """,
                (
                    chat_id,
                    str(prompt["id"]),
                    title,
                    selected_model,
                    now,
                    now,
                ),
            )
            cur.execute(
                """
                INSERT INTO messages
                    (id, chat_id, role, content, prompt_tokens,
                     completion_tokens, total_tokens, position, created_at)
                VALUES (%s, %s, 'user', %s, 0, 0, 0, 1, %s);
                """,
                (
                    str(uuid4()),
                    chat_id,
                    encode_llm_role(
                        encode_message_content(prompt["content"], attachment),
                        initial_llm_role,
                    ),
                    now,
                ),
            )
        conn.commit()
        return get_chat_by_id(chat_id)
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def append_message(
    chat_id,
    role,
    content,
    prompt_tokens=0,
    completion_tokens=0,
    total_tokens=0,
    attachment=None,
):
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            now = datetime.now()
            cur.execute(
                """
                SELECT COALESCE(MAX(position), 0) + 1 AS next_position
                FROM messages
                WHERE chat_id = %s;
                """,
                (str(chat_id),),
            )
            position = cur.fetchone()["next_position"]
            cur.execute(
                """
                INSERT INTO messages
                    (id, chat_id, role, content, prompt_tokens,
                     completion_tokens, total_tokens, position, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
                """,
                (
                    str(uuid4()),
                    str(chat_id),
                    role,
                    encode_message_content(content, attachment),
                    prompt_tokens,
                    completion_tokens,
                    total_tokens,
                    position,
                    now,
                ),
            )
            cur.execute(
                """
                UPDATE chats
                SET total_tokens = total_tokens + %s,
                    updated_at = %s
                WHERE id = %s;
                """,
                (total_tokens, now, str(chat_id)),
            )
        conn.commit()
        return get_chat_by_id(chat_id)
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_all_chats(prompt_id=None):
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            query = """
                SELECT id, prompt_id, title, model, total_tokens, summary,
                       created_at, updated_at
                FROM chats
            """
            params = ()
            if prompt_id:
                query += " WHERE prompt_id = %s"
                params = (str(prompt_id),)
            query += " ORDER BY updated_at DESC;"
            cur.execute(query, params)
            return cur.fetchall()
    finally:
        conn.close()


def get_chat_by_id(chat_id):
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            return _fetch_chat(cur, chat_id)
    finally:
        conn.close()


def set_chat_summary(chat_id, summary):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE chats
                SET summary = %s, updated_at = %s
                WHERE id = %s
                RETURNING id;
                """,
                (summary, datetime.now(), str(chat_id)),
            )
            row = cur.fetchone()
        conn.commit()
        return row is not None
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def delete_chat(chat_id):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM chats WHERE id = %s RETURNING id;",
                (str(chat_id),),
            )
            row = cur.fetchone()
        conn.commit()
        return row is not None
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
