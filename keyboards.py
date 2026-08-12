from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

PAGE_SIZE = 8


def categories_keyboard(categories, page: int = 0) -> InlineKeyboardMarkup:
    start = page * PAGE_SIZE
    chunk = categories[start:start + PAGE_SIZE]

    rows = [
        [InlineKeyboardButton(text=f"{c['code']}. {c['name']}", callback_data=f"cat:{c['id']}")]
        for c in chunk
    ]

    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(text="⬅️ Oldingi", callback_data=f"page:{page - 1}"))
    if start + PAGE_SIZE < len(categories):
        nav.append(InlineKeyboardButton(text="Keyingi ➡️", callback_data=f"page:{page + 1}"))
    if nav:
        rows.append(nav)

    return InlineKeyboardMarkup(inline_keyboard=rows)


def category_actions_keyboard(category_id: int, entry_count: int) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text="➕ Qo'shish", callback_data=f"add:{category_id}")],
        [InlineKeyboardButton(text=f"👀 Ko'rish ({entry_count})", callback_data=f"view:{category_id}:0")],
        [InlineKeyboardButton(text="🔍 Qidirish", callback_data=f"find:{category_id}")],
        [InlineKeyboardButton(text="⬅️ Toifalarga qaytish", callback_data="page:0")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def back_to_category_keyboard(category_id: int) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(text="⬅️ Orqaga", callback_data=f"cat:{category_id}")]]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def entries_nav_keyboard(category_id: int, page: int, pages: int) -> InlineKeyboardMarkup:
    nav = []
    if page > 0:
        nav.append(
            InlineKeyboardButton(text="⬅️ Oldingi", callback_data=f"view:{category_id}:{page - 1}")
        )
    if page + 1 < pages:
        nav.append(
            InlineKeyboardButton(text="Keyingi ➡️", callback_data=f"view:{category_id}:{page + 1}")
        )

    rows = []
    if nav:
        rows.append(nav)
    rows.append([InlineKeyboardButton(text="⬅️ Toifaga qaytish", callback_data=f"cat:{category_id}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def entry_keyboard(entry_id: int) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(text="🗑 O'chirish", callback_data=f"del:{entry_id}")]]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def confirm_delete_keyboard(entry_id: int) -> InlineKeyboardMarkup:
    rows = [[
        InlineKeyboardButton(text="✅ Ha, o'chirilsin", callback_data=f"delok:{entry_id}"),
        InlineKeyboardButton(text="❌ Yo'q", callback_data=f"delno:{entry_id}"),
    ]]
    return InlineKeyboardMarkup(inline_keyboard=rows)
