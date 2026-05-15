from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

#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

type = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="🚨 Жалоба", callback_data="reports"),
         InlineKeyboardButton(text="💡 Предложение", callback_data="offers")
         ],
        [
            InlineKeyboardButton(text="❓ Вопрос", callback_data="questions")
         ]
    ]
)

catolog = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="📚 Учёба", callback_data="studing_st"),
            InlineKeyboardButton(text="🧑‍🏫 Учителя", callback_data="teachers_st"),
        ],
        [
            InlineKeyboardButton(text="⚠️ Буллинг", callback_data="bulling_st"),
            InlineKeyboardButton(text="⏰ Расписание / звонки", callback_data="schedule_st")
         ],
        [
            InlineKeyboardButton(text="🏫 Условия", callback_data="conditions_st"),
            InlineKeyboardButton(text="❗Другое", callback_data="others_st")
        ],
        [
            InlineKeyboardButton(text="🔙 Назад", callback_data="back")
        ]
    ]
)
offer = InlineKeyboardMarkup(
inline_keyboard=[
        [
            InlineKeyboardButton(text="🎉 Школьные мероприятия", callback_data="events_nd"),
            InlineKeyboardButton(text="📖 Учебный процесс", callback_data="proccess_nd"),
        ],
        [
            InlineKeyboardButton(text="🌱 Идеи для школы", callback_data="ideas_nd"),
            InlineKeyboardButton(text="⏰ Расписание / звонки", callback_data="schedule_nd")
         ],
        [
            InlineKeyboardButton(text="💻 Технологии", callback_data="tech_nd"),
            InlineKeyboardButton(text="❗Другое", callback_data="others_nd")
        ],
        [
            InlineKeyboardButton(text="🔙 Назад", callback_data="back")
        ]
    ]

)

qq = InlineKeyboardMarkup(
inline_keyboard=[
        [
            InlineKeyboardButton(text="📚 Учёба / оценки", callback_data="studing_rd"),
            InlineKeyboardButton(text="🏫 Школьные правила", callback_data="rules_rd"),
        ],
        [
            InlineKeyboardButton(text="🧾 Документы / справки", callback_data="docs_rd"),
            InlineKeyboardButton(text="🤔 Общее", callback_data="general_rd")
         ],
        [
            InlineKeyboardButton(text="❗Другое", callback_data="others_rd")
        ],
        [
            InlineKeyboardButton(text="🔙 Назад", callback_data="back")
        ]
    ]
)

tch = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📥 Новые", callback_data="admin_new")],
        [InlineKeyboardButton(text="🔄 В работе", callback_data="admin_progress")],
        [InlineKeyboardButton(text="✅ Решенные", callback_data="admin_done")],
        [InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")]
    ])

bck = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="🔙 Назад", callback_data="back_fc")]
])

again = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="🔁 Подать ещё одну заявку", callback_data="again")]
])
