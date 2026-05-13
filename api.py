from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import APIKeyHeader
from pydantic import BaseModel
from typing import Optional
import sqlite3

app = FastAPI(title="School Reports API")

# Простая защита через API ключ
API_KEY = "kelechek_tech"  # поменяй на свой
api_key_header = APIKeyHeader(name="X-API-Key")

import httpx

BOT_TOKEN = "8706542269:AAFxivgewbI17tlO7boF5h2-6jVgf4RhSSw"  # вставь токен от @BotFather

async def notify_user(user_id: int, text: str):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    async with httpx.AsyncClient() as client:
        try:
            await client.post(url, json={"chat_id": user_id, "text": text})
        except Exception as e:
            print(f"Уведомление не отправлено: {e}")

def get_user_id_by_report(report_id: int):
    conn = get_db()
    row = conn.execute("SELECT user_id FROM reports WHERE id=?", (report_id,)).fetchone()
    conn.close()
    return row["user_id"] if row else None

def verify_key(key: str = Depends(api_key_header)):
    if key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API Key")
    return key

def get_db():
    conn = sqlite3.connect("reports.db")
    conn.row_factory = sqlite3.Row  # чтобы возвращало словари
    return conn


# --- Модели ответов ---
class Report(BaseModel):
    id: int
    user_id: int
    type: str
    category: str
    text: str
    status: str
    answer: Optional[str] = None


# --- Эндпоинты ---

@app.get("/reports", response_model=list[Report])
def get_all_reports(key: str = Depends(verify_key)):
    """Все заявки"""
    conn = get_db()
    rows = conn.execute(
        "SELECT id, user_id, type, category, text, status, answer FROM reports"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@app.get("/reports/{report_id}", response_model=Report)
def get_report(report_id: int, key: str = Depends(verify_key)):
    """Одна заявка по ID"""
    conn = get_db()
    row = conn.execute(
        "SELECT id, user_id, type, category, text, status, answer FROM reports WHERE id=?",
        (report_id,)
    ).fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Report not found")
    return dict(row)


@app.get("/reports/status/{status}", response_model=list[Report])
def get_by_status(status: str, key: str = Depends(verify_key)):
    """Заявки по статусу: new / in_progress / done"""
    conn = get_db()
    rows = conn.execute(
        "SELECT id, user_id, type, category, text, status, answer FROM reports WHERE status=?",
        (status,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@app.get("/stats")
def get_stats(key: str = Depends(verify_key)):
    """Статистика"""
    conn = get_db()
    total = conn.execute("SELECT COUNT(*) FROM reports").fetchone()[0]
    new = conn.execute("SELECT COUNT(*) FROM reports WHERE status='new'").fetchone()[0]
    in_progress = conn.execute("SELECT COUNT(*) FROM reports WHERE status='in_progress'").fetchone()[0]
    done = conn.execute("SELECT COUNT(*) FROM reports WHERE status='done'").fetchone()[0]
    conn.close()
    return {"total": total, "new": new, "in_progress": in_progress, "done": done}

from pydantic import BaseModel

class StatusUpdate(BaseModel):
    status: str

class AnswerUpdate(BaseModel):
    answer: str

from fastapi import FastAPI, HTTPException, Depends
from fastapi.concurrency import run_in_threadpool

@app.patch("/reports/{report_id}/status")
async def update_report_status(report_id: int, body: StatusUpdate, key: str = Depends(verify_key)):
    user_id = get_user_id_by_report(report_id)
    
    conn = get_db()
    conn.execute("UPDATE reports SET status=? WHERE id=?", (body.status, report_id))
    conn.commit()
    conn.close()

    if user_id:
        if body.status == "in_progress":
            await notify_user(user_id,
                f"🔄 Ваша заявка #{report_id} взята в работу!\n"
                f"Ожидайте ответа от администрации."
            )
        elif body.status == "done":
            conn = get_db()
            row = conn.execute("SELECT answer FROM reports WHERE id=?", (report_id,)).fetchone()
            conn.close()
            answer = row["answer"] if row and row["answer"] else None
            if answer:
                await notify_user(user_id,
                    f"✅ Ваша заявка #{report_id} решена!\n\n"
                    f"✉️ Ответ:\n{answer}\n\n"
                    f"Если остались вопросы — создайте новую заявку."
                )
            else:
                await notify_user(user_id,
                    f"✅ Ваша заявка #{report_id} решена!\n"
                    f"Если остались вопросы — создайте новую заявку."
                )

    return {"ok": True}


@app.patch("/reports/{report_id}/answer")
async def update_report_answer(report_id: int, body: AnswerUpdate, key: str = Depends(verify_key)):
    user_id = get_user_id_by_report(report_id)

    conn = get_db()
    conn.execute("UPDATE reports SET answer=?, status='done' WHERE id=?", (body.answer, report_id))
    conn.commit()
    conn.close()

    if user_id:
        await notify_user(user_id,
            f"✉️ Ответ на вашу заявку #{report_id}:\n\n"
            f"{body.answer}\n\n"
            f"✅ Заявка закрыта. Если остались вопросы — создайте новую заявку."
        )

    return {"ok": True}