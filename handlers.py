from aiogram import Router, F
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, CallbackQuery
from keyboards import type, catolog, offer, qq, tch, bck
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


import sqlite3
from groq import Groq

client = Groq(api_key="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")

class ReportState(StatesGroup):
    waiting_for_text = State()

class AdminState(StatesGroup):
    waiting_for_reply = State()

class AdminBrowseState(StatesGroup):
    browsing = State()

class BullingState(StatesGroup):
    q1 = State()  
    q2 = State()  
    q3 = State()  

router = Router()

ADMIN_IDS = [7087792004, 5086999527]


#functions
def is_admin(user_id):
    return user_id in ADMIN_IDS

def get_answer(report_id):
    conn = sqlite3.connect("reports.db")
    cursor = conn.cursor()
    cursor.execute("SELECT answer FROM reports WHERE id=?", (report_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result and result[0] else None

def add_report(user_id, type, category, text, status, answer=None):
    conn = sqlite3.connect("reports.db")
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO reports (user_id, type, category, text, status, answer)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (user_id, type, category, text, status, answer))

    report_id = cursor.lastrowid

    conn.commit()
    conn.close()

    return report_id

def get_reports():
    conn = sqlite3.connect("reports.db")
    cursor = conn.cursor()

    cursor.execute("SELECT id, user_id, type, category, text, status, answer FROM reports")
    rows = cursor.fetchall()

    conn.close()
    return rows

def get_stats():
    conn = sqlite3.connect("reports.db")
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM reports")
    total = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM reports WHERE status='done'")
    done = cursor.fetchone()[0]

    conn.close()

    return total, done

def get_reports_by_status(status):
    conn = sqlite3.connect("reports.db")
    cursor = conn.cursor()

    cursor.execute("SELECT id, type, category, text FROM reports WHERE status=?", (status,))
    rows = cursor.fetchall()

    conn.close()
    return rows


async def show_report_page(message, reports, index, edit=False):
    r = reports[index]
    total = len(reports)

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="◀️", callback_data="page_prev"),
            InlineKeyboardButton(text=f"{index+1}/{total}", callback_data="page_noop"),
            InlineKeyboardButton(text="▶️", callback_data="page_next"),
        ],
        [InlineKeyboardButton(text="✏️ Ответить", callback_data=f"reply_{r[0]}")],
        [InlineKeyboardButton(text="🔄 В работу", callback_data=f"take_{r[0]}")],
        [InlineKeyboardButton(text="✅ Решено", callback_data=f"done_{r[0]}")]
    ])

    text = (
        f"📋 Заявка #{r[0]}\n"
        f"📌Тип:  {r[1]}\n"
        f"📌Категория:  {r[2]}\n\n"
        f"📝 {r[3]}"
    )

    if edit:
        await message.edit_text(text, reply_markup=kb)
    else:
        await message.answer(text, reply_markup=kb)


def get_user_id(report_id):
    import sqlite3

    conn = sqlite3.connect("reports.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT user_id FROM reports WHERE id=?",
        (report_id,)
    )

    result = cursor.fetchone()
    conn.close()

    if result:
        return result[0]
    return None

def update_status(report_id, new_status):
    import sqlite3

    conn = sqlite3.connect("reports.db")
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE reports SET status=? WHERE id=?",
        (new_status, report_id)
    )

    conn.commit()
    conn.close()

def check_text_with_ai(text: str) -> bool:
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {
                "role": "system",
                "content": (
                    "Ты — модератор сообщений в школьной системе обратной связи. "
                    "Твоя задача — проверить текст и определить, нарушает ли он правила."
                    """
                    Правила:
                        - Запрещены оскорбления, мат, угрозы
                        - Запрещён спам и бессмысленный текст
                        - Запрещён токсичный или агрессивный тон
                        - Разрешены жалобы, даже если они негативные, но без оскорблений

                        ВАЖНО:
                        - Не блокируй нормальные жалобы
                        - Учитывай, что ученик может писать эмоционально, и может писать о помощи или о буллинге но это допустимо
                    """
                    "Ответь ТОЛЬКО одним словом: OK или BLOCK. "
                    "BLOCK если есть: нарушение, все в заглавных буквах(capslock). "
                    "OK если всё нормально."
                )
            },
            {"role": "user", "content": text}
        ]
    )

    result = response.choices[0].message.content.strip()
    return result == "OK"
 
def add_answer(report_id, answer):
    import sqlite3

    conn = sqlite3.connect("reports.db")
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE reports SET answer=? WHERE id=?",
        (answer, report_id)
    )

    conn.commit()
    conn.close()


#Commands
@router.message(CommandStart())
async def start(message: Message):
    try:
        conn = sqlite3.connect("reports.db")
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reports(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER, 
                type TEXT,
                category TEXT,
                text TEXT,
                status TEXT,
                priority TEXT,
                answer TEXT
            )
            """)

    except Exception as e:
        await message.answer(f"Error while creating data base: {e}")

    await message.answer("Привет выбери что ты хочешь написать", reply_markup=type)

from aiogram.filters import Command

@router.message(Command("reports"))
async def show_reports(message: Message):
    reports = get_reports()

    if not reports:
        await message.answer("📭 Жалоб нет")
        return

    text = "📋 Список жалоб:\n\n"

    for r in reports:
        text += (
            f"🆔 ID: {r[0]}\n"
            f"👤 User: {r[1]}\n"
            f"📌 Type: {r[2]}\n"
            f"📂 Category: {r[3]}\n"
            f"📝 Text: {r[4]}\n"
            f"📊 Status: {r[5]}\n"
            f"💬 Answer: {r[6]}\n"
            f"-----------------\n"
            f"\n"
            f"\n"
        )

    await message.answer(text)

@router.message(Command("admin"))
async def admin_panel(message: Message):
    if not is_admin(message.from_user.id):
        return await message.answer("❌ Нет доступа")

    await message.answer("👨‍🏫 Админ панель", reply_markup=tch)




#Callbacks
@router.callback_query(F.data=="reports")
async def report(callback:CallbackQuery):
    await callback.answer()
    await callback.message.edit_text("Выбери категорию жалобы", reply_markup=catolog)

@router.callback_query(F.data=="offers")
async def offers(callback:CallbackQuery):
    await callback.answer()
    await callback.message.edit_text("Выбери категорию предложения", reply_markup=offer)

@router.callback_query(F.data=="questions")
async def questions(callback:CallbackQuery):
    await callback.answer()
    await callback.message.edit_text("Выбери категорию вопроса", reply_markup=qq)

@router.callback_query(F.data=="back_fc")
async def back_fc(callback:CallbackQuery, state:FSMContext):
    await callback.answer()
    await callback.message.edit_text("Выбери что ты хочешь написать", reply_markup=type)
    await state.clear()

@router.callback_query(F.data=="back")
async def back(callback:CallbackQuery):
    await callback.answer()
    await callback.message.edit_text("Выбери что ты хочешь написать", reply_markup=type)




@router.callback_query(F.data == "admin_new")
async def show_new(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    reports = get_reports_by_status("new")

    if not reports:
        return await callback.message.edit_text("📭 Нет новых заявок", reply_markup=tch)

    await state.update_data(reports=reports, index=0)
    await state.set_state(AdminBrowseState.browsing)
    await show_report_page(callback.message, reports, 0)


@router.callback_query(F.data == "admin_progress")
async def show_progress(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    reports = get_reports_by_status("in_progress")

    if not reports:
        return await callback.message.edit_text("📭 Нет заявок в работе", reply_markup=tch)

    await state.update_data(reports=reports, index=0)
    await state.set_state(AdminBrowseState.browsing)
    await show_report_page(callback.message, reports, 0)


@router.callback_query(F.data == "admin_done")
async def show_done(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    reports = get_reports_by_status("done")

    if not reports:
        return await callback.message.edit_text("📭 Нет решённых заявок", reply_markup=tch)

    await state.update_data(reports=reports, index=0)
    await state.set_state(AdminBrowseState.browsing)
    await show_report_page(callback.message, reports, 0)

@router.callback_query(F.data == "admin_stats")
async def show_stats(callback: CallbackQuery):
    await callback.answer()
    total, done = get_stats()
    in_progress = len(get_reports_by_status("in_progress"))
    new = len(get_reports_by_status("new"))

    try:
        await callback.message.edit_text(
            f"📊 Статистика:\n\n"
            f"📋 Всего заявок: {total}\n"
            f"🆕 Новых: {new}\n"
            f"🔄 В работе: {in_progress}\n"
            f"✅ Решено: {done}",
            reply_markup=tch
        )
    except Exception:
        pass  

@router.callback_query(AdminBrowseState.browsing, F.data == "page_next")
async def page_next(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    data = await state.get_data()
    reports = data["reports"]
    index = data["index"]

    index = (index + 1) % len(reports)
    await state.update_data(index=index)
    await show_report_page(callback.message, reports, index, edit=True)


@router.callback_query(AdminBrowseState.browsing, F.data == "page_prev")
async def page_prev(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    data = await state.get_data()
    reports = data["reports"]
    index = data["index"]

    index = (index - 1) % len(reports) 
    await state.update_data(index=index)
    await show_report_page(callback.message, reports, index, edit=True)


@router.callback_query(F.data == "page_noop")
async def page_noop(callback: CallbackQuery):
    await callback.answer()  


@router.callback_query(F.data.startswith("take_"))
async def take_report(callback: CallbackQuery, state: FSMContext):
    report_id = int(callback.data.split("_")[1])
    update_status(report_id, "in_progress")

    user_id = get_user_id(report_id)

    
    try:
        await callback.bot.send_message(
            user_id,
            f"🔄 Ваша заявка #{report_id} взята в работу!\n"
            f"Ожидайте ответа от администрации."
        )
    except Exception:
        pass 

    await callback.answer(f"🔄 Заявка #{report_id} в работе", show_alert=True)

    
    data = await state.get_data()
    await callback.message.edit_reply_markup(reply_markup=None)


@router.callback_query(F.data.startswith("done_"))
async def done_report(callback: CallbackQuery):
    report_id = int(callback.data.split("_")[1])
    update_status(report_id, "done")

    user_id = get_user_id(report_id)
    answer = get_answer(report_id)

    try:
        if answer:
            await callback.bot.send_message(
                user_id,
                f"✅ Ваша заявка #{report_id} решена!\n\n"
                f"✉️ Ответ администрации:\n{answer}"
                f"Если остались вопросы — создайте новую заявку."
            )
        else:
            await callback.bot.send_message(
                user_id,
                f"✅ Ваша заявка #{report_id} решена!\n"
                f"Если остались вопросы — создайте новую заявку."
            )
    except Exception:
        pass

    await callback.answer("✅ Отмечено как решено", show_alert=True)
    await callback.message.edit_reply_markup(reply_markup=None)


@router.callback_query(F.data.startswith("reply_"))
async def reply_start(callback: CallbackQuery, state: FSMContext):
    callback.answer()
    report_id = int(callback.data.split("_")[1])

    await state.update_data(report_id=report_id)

    await callback.message.answer("Введите ответ:")
    await state.set_state(AdminState.waiting_for_reply)

@router.message(AdminState.waiting_for_reply)
async def send_reply(message: Message, state: FSMContext):
    data = await state.get_data()
    report_id = data["report_id"]

    add_answer(report_id, message.text)
    update_status(report_id, "done")

    user_id = get_user_id(report_id)

    try:
        await message.bot.send_message(
            user_id,
            f"✉️ Ответ на вашу заявку #{report_id}:\n\n"
            f"{message.text}\n\n"
            f"✅ Заявка закрыта."
        )
        await message.answer("✅ Ответ отправлен пользователю")
    except Exception:
        await message.answer("⚠️ Не удалось отправить — пользователь заблокировал бота")

    await state.clear()






#Reports
@router.callback_query(F.data == "studing_st")
async def studing_st(callback: CallbackQuery, state: FSMContext):
    await callback.answer()

    await state.update_data(
        type="🚨 Жалоба",
        category="📚 Учёба"
    )

    await callback.message.edit_text("Напиши текст жалобы 👇", reply_markup=bck)

    await state.set_state(ReportState.waiting_for_text)


@router.callback_query(F.data == "teachers_st")
async def teachers_st(callback: CallbackQuery, state:FSMContext):
    await callback.answer()
    await state.update_data(
        type="🚨 Жалоба",
        category="🧑‍🏫 Учителя"
    )

    await callback.message.edit_text("Напиши текст жалобы 👇", reply_markup=bck)

    await state.set_state(ReportState.waiting_for_text)


@router.callback_query(F.data == "bulling_st")
async def bulling_st(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.update_data(
        type="🚨 Жалоба",
        category="⚠️ Буллинг"
    )
    await callback.message.edit_text(
        "⚠️ Это серьёзно, и ты правильно делаешь что сообщаешь.\n\n"
        "Я задам несколько вопросов чтобы лучше разобраться в ситуации.\n\n"
        "❓ Вопрос 1 из 3:\n"
        "<b>Кто тебя обижает? (можно описать — одноклассник, группа, старшеклассник и т.д.)</b>",
        parse_mode="HTML"
    )
    await state.set_state(BullingState.q1)


@router.message(BullingState.q1)
async def bulling_q1(message: Message, state: FSMContext):
    if not check_text_with_ai(message.text):
        await message.answer("⛔ Текст заблокирован (нарушение правил)")
        await state.clear()
        return

    await state.update_data(bulling_q1=message.text)
    await message.answer(
        "❓ Вопрос 2 из 3:\n"
        "<b>Где это происходит? (в классе, в коридоре, на улице, в интернете и т.д.)</b>",
        parse_mode="HTML"
    )
    await state.set_state(BullingState.q2)


@router.message(BullingState.q2)
async def bulling_q2(message: Message, state: FSMContext):
    if not check_text_with_ai(message.text):
        await message.answer("⛔ Текст заблокирован (нарушение правил)")
        await state.clear()
        return

    await state.update_data(bulling_q2=message.text)
    await message.answer(
        "❓ Вопрос 3 из 3:\n"
        "<b>Как давно это происходит и как часто?</b>",
        parse_mode="HTML"
    )
    await state.set_state(BullingState.q3)



@router.message(BullingState.q3)
async def bulling_q3(message: Message, state: FSMContext):
    if not check_text_with_ai(message.text):
        await message.answer("⛔ Текст заблокирован (нарушение правил)")
        await state.clear()
        return

    await state.update_data(bulling_q3=message.text)
    data = await state.get_data()

    await message.answer("⏳ Обрабатываю информацию, подожди немного...")

    # ИИ составляет итоговый текст заявки
    enriched_text = await enrich_bulling_report(
        q1=data["bulling_q1"],
        q2=data["bulling_q2"],
        q3=data["bulling_q3"]
    )

    report_id = add_report(
        user_id=message.from_user.id,
        type=data["type"],
        category=data["category"],
        text=enriched_text,
        status="new"
    )

    await message.answer(
        f"✅ Жалоба отправлена! ID: <b>{report_id}</b>\n\n"
        f"Администрация рассмотрит её в ближайшее время. Ты не один.",
        parse_mode="HTML"
    )
    await state.clear()

async def enrich_bulling_report(q1: str, q2: str, q3: str) -> str:
    import asyncio

    prompt = f"""
Ученик сообщил о буллинге. Вот его ответы на три вопроса:

1. Кто обидчик: {q1}
2. Где происходит: {q2}  
3. Как давно и как часто: {q3}

Составь структурированный текст заявки для администрации школы.
Пиши от третьего лица, кратко и по делу.
Выдели ключевые факты: кто, где, как давно.
Добавь краткую оценку серьёзности ситуации.
Не придумывай детали которых нет в ответах.
Объём — 3-5 предложений.
"""

    def _call():
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {
                    "role": "system",
                    "content": "Ты помощник школьного психолога. Составляешь заявки о буллинге на основе ответов ученика."
                },
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content.strip()

    
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, _call)

    
    raw = (
        f"\n\n---\n"
        f"📝 Ответы ученика:\n"
        f"• Обидчик: {q1}\n"
        f"• Место: {q2}\n"
        f"• Давность: {q3}"
    )

    return result + raw

@router.callback_query(F.data == "schedule_st")
async def schedule_st(callback: CallbackQuery, state:FSMContext):
    await callback.answer()
    await state.update_data(
        type="🚨 Жалоба",
        category="⏰ Расписание / звонки"
    )

    await callback.message.edit_text("Напиши текст жалобы 👇", reply_markup=bck)

    await state.set_state(ReportState.waiting_for_text)



@router.callback_query(F.data == "conditions_st")
async def conditions_st(callback: CallbackQuery, state:FSMContext):
    await callback.answer()
    await state.update_data(
        type="🚨 Жалоба",
        category="🏫 Условия"
    )

    await callback.message.edit_text("Напиши текст жалобы 👇", reply_markup=bck)

    await state.set_state(ReportState.waiting_for_text)

@router.callback_query(F.data == "others_st")
async def others_st(callback: CallbackQuery, state:FSMContext):
    await callback.answer()
    await state.update_data(
        type="🚨 Жалоба",
        category="❗Другое"
    )

    await callback.message.edit_text("Напиши текст жалобы 👇", reply_markup=bck)

    await state.set_state(ReportState.waiting_for_text)



#Offers
@router.callback_query(F.data == "events_nd")
async def events_nd(callback: CallbackQuery, state:FSMContext):
    await callback.answer()
    await state.update_data(
        type="💡 Предложение",
        category="🎉 Школьные мероприятия"
    )

    await callback.message.edit_text("Напиши текст предолжения 👇", reply_markup=bck)

    await state.set_state(ReportState.waiting_for_text)


@router.callback_query(F.data == "proccess_nd")
async def proccess_nd(callback: CallbackQuery, state:FSMContext):
    await callback.answer()
    await state.update_data(
        type="💡 Предложение",
        category="📖 Учебный процесс"
    )

    await callback.message.edit_text("Напиши текст предолжения 👇", reply_markup=bck)

    await state.set_state(ReportState.waiting_for_text)

@router.callback_query(F.data == "ideas_nd")
async def ideas_nd(callback: CallbackQuery, state:FSMContext):
    await callback.answer()
    await state.update_data(
        type="💡 Предложение",
        category="🌱 Идеи для школы"
    )

    await callback.message.edit_text("Напиши текст предолжения 👇", reply_markup=bck)

    await state.set_state(ReportState.waiting_for_text)

@router.callback_query(F.data == "schedule_nd")
async def schedule_nd(callback: CallbackQuery, state:FSMContext):
    await callback.answer()
    await state.update_data(
        type="💡 Предложение",
        category="⏰ Расписание / звонки"
    )

    await callback.message.edit_text("Напиши текст предолжения 👇", reply_markup=bck)

    await state.set_state(ReportState.waiting_for_text)

@router.callback_query(F.data == "tech_nd")
async def tech_nd(callback: CallbackQuery, state:FSMContext):
    await callback.answer()
    await state.update_data(
        type="💡 Предложение",
        category="💻 Технологии"
    )

    await callback.message.edit_text("Напиши текст предолжения 👇", reply_markup=bck)

    await state.set_state(ReportState.waiting_for_text)

@router.callback_query(F.data == "others_nd")
async def others_nd(callback: CallbackQuery, state:FSMContext):
    await callback.answer()
    await state.update_data(
        type="💡 Предложение",
        category="❗Другое"
    )

    await callback.message.edit_text("Напиши текст предолжения 👇", reply_markup=bck)

    await state.set_state(ReportState.waiting_for_text)


#Questions
@router.callback_query(F.data == "studing_rd")
async def studing_rd(callback: CallbackQuery, state:FSMContext):
    await callback.answer()
    await state.update_data(
        type="❓ Вопрос",
        category="📚 Учёба / оценки"
    )

    await callback.message.edit_text("Напиши текст вопроса 👇", reply_markup=bck)

    await state.set_state(ReportState.waiting_for_text)

@router.callback_query(F.data == "rules_rd")
async def rules_rd(callback: CallbackQuery, state:FSMContext):
    await callback.answer()
    await state.update_data(
        type="❓ Вопрос",
        category="🏫 Школьные правила"
    )

    await callback.message.edit_text("Напиши текст вопроса 👇", reply_markup=bck)

    await state.set_state(ReportState.waiting_for_text)

@router.callback_query(F.data == "docs_rd")
async def docs_rd(callback: CallbackQuery, state:FSMContext):
    await callback.answer()
    await state.update_data(
        type="❓ Вопрос",
        category="🧾 Документы / справки"
    )

    await callback.message.edit_text("Напиши текст вопроса 👇", reply_markup=bck)

    await state.set_state(ReportState.waiting_for_text)

@router.callback_query(F.data == "general_rd")
async def general_rd(callback: CallbackQuery, state:FSMContext):
    await callback.answer()
    await state.update_data(
        type="❓ Вопрос",
        category="🤔 Общее"
    )

    await callback.message.edit_text("Напиши текст вопроса 👇", reply_markup=bck)

    await state.set_state(ReportState.waiting_for_text)

@router.callback_query(F.data == "others_rd")
async def others_rd(callback: CallbackQuery, state:FSMContext):
    await callback.answer()
    await state.update_data(
        type="❓ Вопрос",
        category="❗Другое"
    )

    await callback.message.edit_text("Напиши текст вопроса 👇", reply_markup=bck)

    await state.set_state(ReportState.waiting_for_text)

#Text
@router.message(ReportState.waiting_for_text)
async def get_text(message: Message, state: FSMContext):
    data = await state.get_data()

    text = message.text

    if not check_text_with_ai(text):
        await message.answer("⛔ Текст заблокирован ИИ (нарушение правил)")
        await state.clear()
        return

    report_id = add_report(
        user_id=message.from_user.id,
        type=data["type"],
        category=data["category"],
        text=message.text,
        status="new"
    )

    await message.answer(f"✅ Ваша заявка отправлена! ID: {report_id}")

    await state.clear()
