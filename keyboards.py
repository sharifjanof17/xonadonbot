from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from i18n import LANGUAGES, localized, t

PAGE_SIZE = 8


def language_keyboard() -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text=title, callback_data=f"lang:{code}")]
        for code, title in LANGUAGES.items()
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def categories_keyboard(categories, page: int = 0, lang: str = "uz") -> InlineKeyboardMarkup:
    start = page * PAGE_SIZE
    chunk = categories[start:start + PAGE_SIZE]

    rows = [
        [InlineKeyboardButton(
            text=f"{c['code']}. {localized(c, 'name', lang)}", callback_data=f"cat:{c['id']}"
        )]
        for c in chunk
    ]

    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(text=t(lang, "btn_prev"), callback_data=f"page:{page - 1}"))
    if start + PAGE_SIZE < len(categories):
        nav.append(InlineKeyboardButton(text=t(lang, "btn_next"), callback_data=f"page:{page + 1}"))
    if nav:
        rows.append(nav)

    return InlineKeyboardMarkup(inline_keyboard=rows)


def category_actions_keyboard(category_id: int, entry_count: int, lang: str = "uz") -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text=t(lang, "btn_add"), callback_data=f"add:{category_id}")],
        [InlineKeyboardButton(
            text=t(lang, "btn_view", count=entry_count), callback_data=f"view:{category_id}:0"
        )],
        [InlineKeyboardButton(text=t(lang, "btn_search"), callback_data=f"find:{category_id}")],
        [InlineKeyboardButton(text=t(lang, "btn_back_categories"), callback_data="page:0")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def back_to_category_keyboard(category_id: int, lang: str = "uz") -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(text=t(lang, "btn_back"), callback_data=f"cat:{category_id}")]]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def entries_nav_keyboard(category_id: int, page: int, pages: int, lang: str = "uz") -> InlineKeyboardMarkup:
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(
            text=t(lang, "btn_prev"), callback_data=f"view:{category_id}:{page - 1}"
        ))
    if page + 1 < pages:
        nav.append(InlineKeyboardButton(
            text=t(lang, "btn_next"), callback_data=f"view:{category_id}:{page + 1}"
        ))

    rows = []
    if nav:
        rows.append(nav)
    rows.append([InlineKeyboardButton(
        text=t(lang, "btn_back_category"), callback_data=f"cat:{category_id}"
    )])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def entry_keyboard(entry_id: int, lang: str = "uz") -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(text=t(lang, "btn_delete"), callback_data=f"del:{entry_id}")]]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def confirm_delete_keyboard(entry_id: int, lang: str = "uz") -> InlineKeyboardMarkup:
    rows = [[
        InlineKeyboardButton(text=t(lang, "btn_delete_yes"), callback_data=f"delok:{entry_id}"),
        InlineKeyboardButton(text=t(lang, "btn_delete_no"), callback_data=f"delno:{entry_id}"),
    ]]
    return InlineKeyboardMarkup(inline_keyboard=rows)
