import html
import logging

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

import db
from db import ENTRIES_PAGE_SIZE
from i18n import LANGUAGES, PAGE_LABEL_PREFIXES, localized, normalize, t
from keyboards import (
    back_to_category_keyboard,
    categories_keyboard,
    category_actions_keyboard,
    confirm_delete_keyboard,
    entries_nav_keyboard,
    entry_keyboard,
    language_keyboard,
)

router = Router()
logger = logging.getLogger(__name__)

MAX_TEXT = 3500      # Telegram matn chegarasi 4096
MAX_CAPTION = 900    # Telegram media izohi chegarasi 1024
SEARCH_LIMIT = 20


class AddEntry(StatesGroup):
    waiting_content = State()


class SearchEntry(StatesGroup):
    waiting_query = State()


# ---------------------------------------------------------------- yordamchilar


async def _ensure_user(tg_user):
    """Message va CallbackQuery uchun ham ishlaydi: foydalanuvchi bazada bo'lishini kafolatlaydi."""
    return await db.get_or_create_user(tg_user.id, tg_user.full_name)


def _lang(user) -> str:
    return normalize(user["language"] if user is not None else None)


def _esc(value) -> str:
    return html.escape(str(value)) if value is not None else ""


def _trim(text: str, limit: int) -> str:
    text = text or ""
    return text if len(text) <= limit else text[:limit] + " …"


def _can_delete(user, entry) -> bool:
    """Oila boshlig'i ('asosiy') hammasini, qolganlar faqat o'zi qo'shganini o'chira oladi."""
    return user["role"] == "asosiy" or entry["user_id"] == user["id"]


def _entry_header(entry, lang: str, with_category: bool = False) -> str:
    who = _esc(entry["full_name"] or t(lang, "unknown_person"))
    when = entry["created_at"].strftime("%d.%m.%Y %H:%M")
    header = f"👤 {who} | 🕒 {when}"
    if with_category and entry.get("category_name"):
        category = entry["category_name_ru"] if lang == "ru" and entry.get("category_name_ru") else entry["category_name"]
        header = f"📂 <b>{_esc(category)}</b>\n{header}"
    return header


async def _send_entry(message: Message, entry, user, with_category: bool = False) -> None:
    """Bitta yozuvni turiga qarab yuboradi (izohi va o'chirish tugmasi bilan)."""
    lang = _lang(user)
    keyboard = entry_keyboard(entry["id"], lang) if _can_delete(user, entry) else None
    header = _entry_header(entry, lang, with_category)

    if entry["content_type"] == "text":
        body = _esc(_trim(entry["text_content"], MAX_TEXT))
        await message.answer(f"{header}\n\n{body}", reply_markup=keyboard)
        return

    caption = header
    if entry["caption"]:
        caption += f"\n\n{_esc(_trim(entry['caption'], MAX_CAPTION))}"

    senders = {
        "photo": message.answer_photo,
        "video": message.answer_video,
        "document": message.answer_document,
        "voice": message.answer_voice,
        "audio": message.answer_audio,
        "video_note": message.answer_video_note,
    }
    sender = senders.get(entry["content_type"])
    if sender is None:
        await message.answer(f"{header}\n\n{t(lang, 'unknown_entry_type')}", reply_markup=keyboard)
        return

    if entry["content_type"] == "video_note":
        await message.answer(header, reply_markup=keyboard)
        await sender(entry["file_id"])
    else:
        await sender(entry["file_id"], caption=caption, reply_markup=keyboard)


async def _show_results(message: Message, entries, user, query: str, category_id: int | None) -> None:
    lang = _lang(user)
    if not entries:
        await message.answer(
            t(lang, "search_empty", query=_esc(query)),
            reply_markup=back_to_category_keyboard(category_id, lang) if category_id else None,
        )
        return

    await message.answer(t(lang, "search_results", query=_esc(query), count=len(entries)))
    for entry in entries:
        await _send_entry(message, entry, user, with_category=category_id is None)
    if category_id:
        await message.answer(
            t(lang, "more_actions"), reply_markup=back_to_category_keyboard(category_id, lang)
        )


async def _edit_or_send(message: Message, text: str, reply_markup=None) -> None:
    """Xabarni tahrirlaydi; media xabar bo'lgani uchun bo'lmasa — yangisini yuboradi."""
    try:
        await message.edit_text(text, reply_markup=reply_markup)
    except TelegramBadRequest:
        await message.answer(text, reply_markup=reply_markup)


# ---------------------------------------------------------------- til


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await _ensure_user(message.from_user)
    await message.answer(
        "Tilni tanlang / Выберите язык:", reply_markup=language_keyboard()
    )


@router.message(Command("til", "language", "yazyk"))
async def cmd_language(message: Message, state: FSMContext):
    await state.clear()
    user = await _ensure_user(message.from_user)
    await message.answer(t(_lang(user), "choose_language"), reply_markup=language_keyboard())


@router.callback_query(F.data.startswith("lang:"))
async def cb_language(callback: CallbackQuery, state: FSMContext):
    lang = callback.data.split(":")[1]
    if lang not in LANGUAGES:
        await callback.answer()
        return

    await _ensure_user(callback.from_user)
    await db.set_language(callback.from_user.id, lang)
    user = await db.get_user(callback.from_user.id)
    invite_code = await db.get_family_invite_code(user["family_id"])

    await _edit_or_send(callback.message, t(lang, "language_saved"))
    await callback.message.answer(t(lang, "start", code=_esc(invite_code)))
    await callback.answer()


# ---------------------------------------------------------------- buyruqlar


@router.message(Command("help"))
async def cmd_help(message: Message):
    user = await _ensure_user(message.from_user)
    await message.answer(t(_lang(user), "help"))


@router.message(Command("join"))
async def cmd_join(message: Message, command: CommandObject, state: FSMContext):
    user = await _ensure_user(message.from_user)
    lang = _lang(user)
    if not command.args:
        await message.answer(t(lang, "join_usage"))
        return
    await state.clear()
    family = await db.join_family(message.from_user.id, message.from_user.full_name, command.args)
    if family is None:
        await message.answer(t(lang, "join_not_found"))
        return
    await message.answer(t(lang, "join_ok"))


@router.message(Command("family"))
async def cmd_family(message: Message):
    user = await _ensure_user(message.from_user)
    lang = _lang(user)
    invite_code = await db.get_family_invite_code(user["family_id"])
    members = await db.list_family_members(user["family_id"])

    lines = [t(lang, "family_header", code=_esc(invite_code), count=len(members))]
    for member in members:
        is_head = member["role"] == "asosiy"
        role = t(lang, "role_head" if is_head else "role_member")
        name = _esc(member["full_name"] or t(lang, "unknown_person"))
        lines.append(f"• {name} — {role}{' ⭐️' if is_head else ''}")

    await message.answer("\n".join(lines))


@router.message(Command("categories"))
async def cmd_categories(message: Message, state: FSMContext):
    await state.clear()
    user = await _ensure_user(message.from_user)
    lang = _lang(user)
    categories = await db.list_categories()
    await message.answer(
        t(lang, "categories_title"),
        reply_markup=categories_keyboard(categories, page=0, lang=lang),
    )


@router.message(Command("search"))
async def cmd_search(message: Message, command: CommandObject, state: FSMContext):
    user = await _ensure_user(message.from_user)
    lang = _lang(user)
    if not command.args or len(command.args.strip()) < 2:
        await message.answer(t(lang, "search_usage"))
        return
    await state.clear()
    query = command.args.strip()
    entries = await db.search_entries(user["family_id"], query, limit=SEARCH_LIMIT)
    await _show_results(message, entries, user, query, category_id=None)


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext):
    await state.clear()
    user = await _ensure_user(message.from_user)
    await message.answer(t(_lang(user), "cancelled"))


# ---------------------------------------------------------------- toifalar


@router.callback_query(F.data.startswith("page:"))
async def cb_page(callback: CallbackQuery):
    page = int(callback.data.split(":")[1])
    user = await _ensure_user(callback.from_user)
    lang = _lang(user)
    categories = await db.list_categories()
    await _edit_or_send(
        callback.message,
        t(lang, "categories_title"),
        reply_markup=categories_keyboard(categories, page=page, lang=lang),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("cat:"))
async def cb_category(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    category_id = int(callback.data.split(":")[1])
    user = await _ensure_user(callback.from_user)
    lang = _lang(user)

    category = await db.get_category(category_id)
    if category is None:
        await callback.answer(t(lang, "category_not_found"), show_alert=True)
        return

    count = await db.count_entries(user["family_id"], category_id)
    await _edit_or_send(
        callback.message,
        t(
            lang, "category_card",
            name=_esc(localized(category, "name", lang)),
            description=_esc(localized(category, "description", lang)),
            count=count,
        ),
        reply_markup=category_actions_keyboard(category_id, count, lang),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("add:"))
async def cb_add(callback: CallbackQuery, state: FSMContext):
    category_id = int(callback.data.split(":")[1])
    user = await _ensure_user(callback.from_user)
    lang = _lang(user)

    category = await db.get_category(category_id)
    if category is None:
        await callback.answer(t(lang, "category_not_found"), show_alert=True)
        return

    await state.set_state(AddEntry.waiting_content)
    await state.update_data(category_id=category_id)

    # Har bir toifa o'ziga mos ma'lumotni so'raydi
    prompt = localized(category, "prompt", lang) or t(lang, "add_prompt_default")
    await _edit_or_send(
        callback.message,
        t(lang, "add_intro", name=_esc(localized(category, "name", lang)), prompt=prompt),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("find:"))
async def cb_find(callback: CallbackQuery, state: FSMContext):
    category_id = int(callback.data.split(":")[1])
    user = await _ensure_user(callback.from_user)
    lang = _lang(user)

    category = await db.get_category(category_id)
    if category is None:
        await callback.answer(t(lang, "category_not_found"), show_alert=True)
        return

    await state.set_state(SearchEntry.waiting_query)
    await state.update_data(category_id=category_id)
    await callback.message.answer(
        t(lang, "search_prompt", name=_esc(localized(category, "name", lang)))
    )
    await callback.answer()


@router.callback_query(F.data.startswith("view:"))
async def cb_view(callback: CallbackQuery):
    parts = callback.data.split(":")
    category_id = int(parts[1])
    page = int(parts[2]) if len(parts) > 2 else 0

    user = await _ensure_user(callback.from_user)
    lang = _lang(user)
    category = await db.get_category(category_id)
    if category is None:
        await callback.answer(t(lang, "category_not_found"), show_alert=True)
        return

    name = _esc(localized(category, "name", lang))
    total = await db.count_entries(user["family_id"], category_id)
    await callback.answer()

    if total == 0:
        await _edit_or_send(
            callback.message,
            t(lang, "entries_empty", name=name),
            reply_markup=back_to_category_keyboard(category_id, lang),
        )
        return

    pages = (total + ENTRIES_PAGE_SIZE - 1) // ENTRIES_PAGE_SIZE
    page = max(0, min(page, pages - 1))

    # Sahifa almashtirilayotgan bo'lsa, eski navigatsiya xabarini olib tashlaymiz
    if callback.message.text and callback.message.text.startswith(PAGE_LABEL_PREFIXES):
        try:
            await callback.message.delete()
        except TelegramBadRequest:
            pass

    entries = await db.list_entries(
        user["family_id"], category_id, limit=ENTRIES_PAGE_SIZE, offset=page * ENTRIES_PAGE_SIZE
    )
    await callback.message.answer(
        t(lang, "entries_header", name=name, total=total, page=page + 1, pages=pages)
    )
    for entry in entries:
        await _send_entry(callback.message, entry, user)

    await callback.message.answer(
        t(lang, "page_label", page=page + 1, pages=pages),
        reply_markup=entries_nav_keyboard(category_id, page, pages, lang),
    )


# ---------------------------------------------------------------- o'chirish


@router.callback_query(F.data.startswith("del:"))
async def cb_delete_ask(callback: CallbackQuery):
    entry_id = int(callback.data.split(":")[1])
    user = await _ensure_user(callback.from_user)
    lang = _lang(user)
    entry = await db.get_entry(entry_id, user["family_id"])

    if entry is None:
        await callback.answer(t(lang, "entry_not_found"), show_alert=True)
        try:
            await callback.message.edit_reply_markup(reply_markup=None)
        except TelegramBadRequest:
            pass
        return

    if not _can_delete(user, entry):
        await callback.answer(t(lang, "no_delete_right"), show_alert=True)
        return

    await callback.message.edit_reply_markup(reply_markup=confirm_delete_keyboard(entry_id, lang))
    await callback.answer(t(lang, "delete_ask"))


@router.callback_query(F.data.startswith("delno:"))
async def cb_delete_cancel(callback: CallbackQuery):
    entry_id = int(callback.data.split(":")[1])
    user = await _ensure_user(callback.from_user)
    lang = _lang(user)
    try:
        await callback.message.edit_reply_markup(reply_markup=entry_keyboard(entry_id, lang))
    except TelegramBadRequest:
        pass
    await callback.answer(t(lang, "delete_cancelled"))


@router.callback_query(F.data.startswith("delok:"))
async def cb_delete_confirm(callback: CallbackQuery):
    entry_id = int(callback.data.split(":")[1])
    user = await _ensure_user(callback.from_user)
    lang = _lang(user)
    entry = await db.get_entry(entry_id, user["family_id"])

    if entry is None:
        await callback.answer(t(lang, "entry_not_found"), show_alert=True)
        return
    if not _can_delete(user, entry):
        await callback.answer(t(lang, "no_delete_right"), show_alert=True)
        return

    await db.delete_entry(entry_id, user["family_id"])
    await callback.answer(t(lang, "deleted"))
    try:
        await callback.message.delete()
    except TelegramBadRequest:
        # Eski xabarni o'chirib bo'lmaydi — hech bo'lmasa tugmalarini olib tashlaymiz
        try:
            await callback.message.edit_reply_markup(reply_markup=None)
        except TelegramBadRequest:
            pass


# ---------------------------------------------------------------- FSM oqimlari


@router.message(SearchEntry.waiting_query)
async def handle_search_query(message: Message, state: FSMContext):
    user = await _ensure_user(message.from_user)
    lang = _lang(user)
    query = (message.text or "").strip()
    if len(query) < 2:
        await message.answer(t(lang, "search_too_short"))
        return

    data = await state.get_data()
    category_id = data.get("category_id")
    await state.clear()

    entries = await db.search_entries(
        user["family_id"], query, category_id=category_id, limit=SEARCH_LIMIT
    )
    await _show_results(message, entries, user, query, category_id)


@router.message(AddEntry.waiting_content)
async def handle_new_entry(message: Message, state: FSMContext):
    user = await _ensure_user(message.from_user)
    lang = _lang(user)
    data = await state.get_data()
    category_id = data.get("category_id")

    if category_id is None:
        await state.clear()
        await message.answer(t(lang, "add_lost_category"))
        return

    category = await db.get_category(category_id)
    if category is None:
        await state.clear()
        await message.answer(t(lang, "category_gone"))
        return

    family_id, user_id = user["family_id"], user["id"]
    caption = message.caption

    if message.text:
        await db.add_entry(family_id, category_id, user_id, "text", text_content=message.text)
    elif message.photo:
        await db.add_entry(
            family_id, category_id, user_id, "photo",
            file_id=message.photo[-1].file_id, caption=caption,
        )
    elif message.video:
        await db.add_entry(
            family_id, category_id, user_id, "video",
            file_id=message.video.file_id, caption=caption,
        )
    elif message.document:
        await db.add_entry(
            family_id, category_id, user_id, "document",
            file_id=message.document.file_id, caption=caption,
        )
    elif message.voice:
        await db.add_entry(family_id, category_id, user_id, "voice", file_id=message.voice.file_id)
    elif message.audio:
        await db.add_entry(
            family_id, category_id, user_id, "audio",
            file_id=message.audio.file_id, caption=caption,
        )
    elif message.video_note:
        await db.add_entry(
            family_id, category_id, user_id, "video_note", file_id=message.video_note.file_id
        )
    else:
        await message.answer(t(lang, "unsupported_content"))
        return

    await state.clear()
    await message.answer(t(lang, "saved", name=_esc(localized(category, "name", lang))))
