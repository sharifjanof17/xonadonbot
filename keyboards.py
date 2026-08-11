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
        [InlineKeyboardButton(text=f"👀 Ko'rish ({entry_count})", callback_data=f"view:{category_id}")],
        [InlineKeyboardButton(text="⬅️ Toifalarga qaytish", callback_data="page:0")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def back_to_category_keyboard(category_id: int) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(text="⬅️ Orqaga", callback_data=f"cat:{category_id}")]]
    return InlineKeyboardMarkup(inline_keyboard=rows)
