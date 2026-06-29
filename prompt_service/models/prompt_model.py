from uuid import uuid4
from datetime import datetime
from prompt_service.database import get_connection

def create_prompt(data):
    conn = get_connection()
    cur = conn.cursor()

    prompt_id = str(uuid4())
    now = datetime.now()

    cur.execute("""
        INSERT INTO prompts
        (id, name, description, content, tags, model_target, created_at, updated_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING *;
    """, (
        prompt_id,
        data.name,
        data.description,
        data.content,
        data.tags,
        data.model_target,
        now,
        now
    ))

    row = cur.fetchone()
    conn.commit()

    cur.close()
    conn.close()

    return row

def get_all_prompts(tag=None, limit=50):
    conn = get_connection()
    cur = conn.cursor()

    if tag:
        cur.execute("""
            SELECT * FROM prompts
            WHERE tags ILIKE %s
            ORDER BY created_at DESC
            LIMIT %s;
        """, (f"%{tag}%", limit))
    else:
        cur.execute("""
            SELECT * FROM prompts
            ORDER BY created_at DESC
            LIMIT %s;
        """, (limit,))

    rows = cur.fetchall()

    cur.close()
    conn.close()

    return rows

def get_prompt_by_id(prompt_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM prompts WHERE id = %s;", (str(prompt_id),))
    row = cur.fetchone()

    cur.close()
    conn.close()

    return row

def update_prompt(prompt_id, data):
    existing = get_prompt_by_id(prompt_id)

    if not existing:
        return None

    name = data.name if data.name is not None else existing[1]
    description = data.description if data.description is not None else existing[2]
    content = data.content if data.content is not None else existing[3]
    tags = data.tags if data.tags is not None else existing[4]
    model_target = data.model_target if data.model_target is not None else existing[5]
    updated_at = datetime.now()

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE prompts
        SET name=%s, description=%s, content=%s, tags=%s, model_target=%s, updated_at=%s
        WHERE id=%s
        RETURNING *;
    """, (
        name,
        description,
        content,
        tags,
        model_target,
        updated_at,
        str(prompt_id)
    ))

    row = cur.fetchone()
    conn.commit()

    cur.close()
    conn.close()

    return row

def delete_prompt(prompt_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("DELETE FROM prompts WHERE id = %s RETURNING id;", (str(prompt_id),))
    row = cur.fetchone()

    conn.commit()

    cur.close()
    conn.close()

    return row