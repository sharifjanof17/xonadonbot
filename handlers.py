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
from keyboards import (
    back_to_category_keyboard,
    categories_keyboard,
    category_actions_keyboard,
    confirm_delete_keyboard,
    entries_nav_keyboard,
    entry_keyboard,
)

router = Router()
logger = logging.getLogger(__name__)

MAX_TEXT = 3500      # Telegram matn chegarasi 4096
MAX_CAPTION = 900    # Telegram media izohi chegarasi 1024
SEARCH_LIMIT = 20

ROLE_NAMES = {"asosiy": "oila boshlig'i", "yordamchi": "a'zo", "a_zo": "a'zo"}


class AddEntry(StatesGroup):
    waiting_content = State()


class SearchEntry(StatesGroup):
    waiting_query = State()


# ---------------------------------------------------------------- yordamchilar


async def _ensure_user(tg_user):
    """Message va CallbackQuery uchun ham ishlaydi: foydalanuvchi bazada bo'lishini kafolatlaydi."""
    return await db.get_or_create_user(tg_user.id, tg_user.full_name)


def _esc(value) -> str:
    return html.escape(str(value)) if value is not None else ""


def _trim(text: str, limit: int) -> str:
    text = text or ""
    return text if len(text) <= limit else text[:limit] + " …"


def _can_delete(user, entry) -> bool:
    """Oila boshlig'i ('asosiy') hammasini, qolganlar faqat o'zi qo'shganini o'chira oladi."""
    return user["role"] == "asosiy" or entry["user_id"] == user["id"]


def _entry_header(entry, with_category: bool = False) -> str:
    who = _esc(entry["full_name"] or "Noma'lum")
    when = entry["created_at"].strftime("%d.%m.%Y %H:%M")
    header = f"👤 {who} | 🕒 {when}"
    if with_category and entry.get("category_name"):
        header = f"📂 <b>{_esc(entry['category_name'])}</b>\n{header}"
    return header


async def _send_entry(message: Message, entry, user, with_category: bool = False) -> None:
    """Bitta yozuvni turiga qarab yuboradi (izohi va o'chirish tugmasi bilan)."""
    keyboard = entry_keyboard(entry["id"]) if _can_delete(user, entry) else None
    header = _entry_header(entry, with_category)

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
        await message.answer(f"{header}\n\n⚠️ Noma'lum turdagi yozuv.", reply_markup=keyboard)
        return

    if entry["content_type"] == "video_note":
        await message.answer(header, reply_markup=keyboard)
        await sender(entry["file_id"])
    else:
        await sender(entry["file_id"], caption=caption, reply_markup=keyboard)


async def _show_results(message: Message, entries, user, query: str, category_id: int | None) -> None:
    if not entries:
        text = f"🔍 «{_esc(query)}» bo'yicha hech narsa topilmadi."
        await message.answer(
            text, reply_markup=back_to_category_keyboard(category_id) if category_id else None
        )
        return

    await message.answer(f"🔍 «{_esc(query)}» — {len(entries)} ta natija:")
    for entry in entries:
        await _send_entry(message, entry, user, with_category=category_id is None)
    if category_id:
        await message.answer("Yana amal tanlang:", reply_markup=back_to_category_keyboard(category_id))


# ---------------------------------------------------------------- buyruqlar


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    user = await _ensure_user(message.from_user)
    invite_code = await db.get_family_invite_code(user["family_id"])
    await message.answer(
        "Assalomu alaykum! Bu — oilaviy ma'lumotlar boti.\n\n"
        "Bu yerda oilangiz uchun muhim narsalarni (rasm, video, hujjat, matn) "
        "toifalar bo'yicha saqlab, kerak bo'lganda tezda topib olishingiz mumkin.\n\n"
        f"Oilangiz kodi: <code>{_esc(invite_code)}</code>\n"
        "Boshqa a'zolar shu kod bilan /join buyrug'i orqali qo'shilishi mumkin.\n\n"
        "Toifalarni ko'rish uchun /categories, yordam uchun /help.",
    )


@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "<b>Buyruqlar</b>\n"
        "/categories — 42 ta toifa ro'yxati\n"
        "/search so'z — barcha toifalar ichidan matn bo'yicha qidirish\n"
        "/family — oila kodi va a'zolar ro'yxati\n"
        "/join KOD — kod orqali oilaga qo'shilish\n"
        "/cancel — boshlangan amalni bekor qilish\n\n"
        "<b>Qanday saqlanadi</b>\n"
        "Toifa → ➕ Qo'shish → matn, rasm, video, hujjat yoki ovozli xabar yuboring.\n\n"
        "<b>O'chirish</b>\n"
        "Har bir yozuv ostidagi 🗑 tugma. Oila boshlig'i hamma yozuvni, "
        "qolgan a'zolar faqat o'zi qo'shganini o'chira oladi."
    )


@router.message(Command("join"))
async def cmd_join(message: Message, command: CommandObject, state: FSMContext):
    if not command.args:
        await message.answer("Iltimos, kodni ham yozing: /join ABC123")
        return
    await state.clear()
    family = await db.join_family(message.from_user.id, message.from_user.full_name, command.args)
    if family is None:
        await message.answer("Bunday kod bilan oila topilmadi. Kodni tekshirib qayta urinib ko'ring.")
        return
    await message.answer("Oilaga muvaffaqiyatli qo'shildingiz! Endi /categories buyrug'idan foydalaning.")


@router.message(Command("family"))
async def cmd_family(message: Message):
    user = await _ensure_user(message.from_user)
    invite_code = await db.get_family_invite_code(user["family_id"])
    members = await db.list_family_members(user["family_id"])

    lines = [
        f"Oilangiz kodi: <code>{_esc(invite_code)}</code>",
        "Buni oila a'zolaringizga yuboring, ular <code>/join KOD</code> orqali qo'shiladi.",
        "",
        f"<b>A'zolar ({len(members)}):</b>",
    ]
    for member in members:
        role = ROLE_NAMES.get(member["role"], "a'zo")
        mark = " ⭐️" if member["role"] == "asosiy" else ""
        name = _esc(member["full_name"] or "Noma'lum")
        lines.append(f"• {name} — {role}{mark}")

    await message.answer("\n".join(lines))


@router.message(Command("categories"))
async def cmd_categories(message: Message, state: FSMContext):
    await state.clear()
    await _ensure_user(message.from_user)
    categories = await db.list_categories()
    await message.answer(
        "📂 Oila guruhlari — kerakli toifani tanlang:",
        reply_markup=categories_keyboard(categories, page=0),
    )


@router.message(Command("search"))
async def cmd_search(message: Message, command: CommandObject, state: FSMContext):
    if not command.args or len(command.args.strip()) < 2:
        await message.answer(
            "Qidirish uchun so'z yozing, masalan: <code>/search pasport</code>\n"
            "(kamida 2 ta harf)"
        )
        return
    await state.clear()
    user = await _ensure_user(message.from_user)
    query = command.args.strip()
    entries = await db.search_entries(user["family_id"], query, limit=SEARCH_LIMIT)
    await _show_results(message, entries, user, query, category_id=None)


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Bekor qilindi.")


# ---------------------------------------------------------------- toifalar


@router.callback_query(F.data.startswith("page:"))
async def cb_page(callback: CallbackQuery):
    page = int(callback.data.split(":")[1])
    categories = await db.list_categories()
    try:
        await callback.message.edit_text(
            "📂 Oila guruhlari — kerakli toifani tanlang:",
            reply_markup=categories_keyboard(categories, page=page),
        )
    except TelegramBadRequest:
        await callback.message.answer(
            "📂 Oila guruhlari — kerakli toifani tanlang:",
            reply_markup=categories_keyboard(categories, page=page),
        )
    await callback.answer()


@router.callback_query(F.data.startswith("cat:"))
async def cb_category(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    category_id = int(callback.data.split(":")[1])
    category = await db.get_category(category_id)
    if category is None:
        await callback.answer("Bunday toifa topilmadi.", show_alert=True)
        return

    user = await _ensure_user(callback.from_user)
    count = await db.count_entries(user["family_id"], category_id)
    text = (
        f"<b>{_esc(category['name'])}</b>\n<i>{_esc(category['description'])}</i>\n\n"
        f"Saqlangan yozuvlar: {count}"
    )
    keyboard = category_actions_keyboard(category_id, count)
    try:
        await callback.message.edit_text(text, reply_markup=keyboard)
    except TelegramBadRequest:
        # Media xabarni matnga aylantirib bo'lmaydi — yangisini yuboramiz
        await callback.message.answer(text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data.startswith("add:"))
async def cb_add(callback: CallbackQuery, state: FSMContext):
    category_id = int(callback.data.split(":")[1])
    category = await db.get_category(category_id)
    if category is None:
        await callback.answer("Bunday toifa topilmadi.", show_alert=True)
        return

    await _ensure_user(callback.from_user)
    await state.set_state(AddEntry.waiting_content)
    await state.update_data(category_id=category_id)
    text = (
        f"<b>{_esc(category['name'])}</b> toifasiga qo'shish.\n\n"
        "Matn, rasm, video, hujjat yoki ovozli xabar yuboring. Bekor qilish uchun /cancel yozing."
    )
    try:
        await callback.message.edit_text(text)
    except TelegramBadRequest:
        await callback.message.answer(text)
    await callback.answer()


@router.callback_query(F.data.startswith("find:"))
async def cb_find(callback: CallbackQuery, state: FSMContext):
    category_id = int(callback.data.split(":")[1])
    category = await db.get_category(category_id)
    if category is None:
        await callback.answer("Bunday toifa topilmadi.", show_alert=True)
        return

    await _ensure_user(callback.from_user)
    await state.set_state(SearchEntry.waiting_query)
    await state.update_data(category_id=category_id)
    await callback.message.answer(
        f"🔍 <b>{_esc(category['name'])}</b> ichidan qidirish.\n\n"
        "Qidirmoqchi bo'lgan so'zni yuboring. Bekor qilish uchun /cancel."
    )
    await callback.answer()


@router.callback_query(F.data.startswith("view:"))
async def cb_view(callback: CallbackQuery):
    parts = callback.data.split(":")
    category_id = int(parts[1])
    page = int(parts[2]) if len(parts) > 2 else 0

    category = await db.get_category(category_id)
    if category is None:
        await callback.answer("Bunday toifa topilmadi.", show_alert=True)
        return

    user = await _ensure_user(callback.from_user)
    total = await db.count_entries(user["family_id"], category_id)
    await callback.answer()

    if total == 0:
        text = f"<b>{_esc(category['name'])}</b> toifasida hali hech narsa yo'q."
        keyboard = back_to_category_keyboard(category_id)
        try:
            await callback.message.edit_text(text, reply_markup=keyboard)
        except TelegramBadRequest:
            await callback.message.answer(text, reply_markup=keyboard)
        return

    pages = (total + ENTRIES_PAGE_SIZE - 1) // ENTRIES_PAGE_SIZE
    page = max(0, min(page, pages - 1))

    # Sahifa almashtirilayotgan bo'lsa, eski navigatsiya xabarini olib tashlaymiz
    if callback.message.text and callback.message.text.startswith("Sahifa "):
        try:
            await callback.message.delete()
        except TelegramBadRequest:
            pass

    entries = await db.list_entries(
        user["family_id"], category_id, limit=ENTRIES_PAGE_SIZE, offset=page * ENTRIES_PAGE_SIZE
    )
    await callback.message.answer(
        f"<b>{_esc(category['name'])}</b> — jami {total} ta yozuv "
        f"(sahifa {page + 1}/{pages}):"
    )
    for entry in entries:
        await _send_entry(callback.message, entry, user)

    await callback.message.answer(
        f"Sahifa {page + 1}/{pages}", reply_markup=entries_nav_keyboard(category_id, page, pages)
    )


# ---------------------------------------------------------------- o'chirish


@router.callback_query(F.data.startswith("del:"))
async def cb_delete_ask(callback: CallbackQuery):
    entry_id = int(callback.data.split(":")[1])
    user = await _ensure_user(callback.from_user)
    entry = await db.get_entry(entry_id, user["family_id"])

    if entry is None:
        await callback.answer("Yozuv topilmadi — ehtimol allaqachon o'chirilgan.", show_alert=True)
        try:
            await callback.message.edit_reply_markup(reply_markup=None)
        except TelegramBadRequest:
            pass
        return

    if not _can_delete(user, entry):
        await callback.answer(
            "Bu yozuvni faqat uni qo'shgan a'zo yoki oila boshlig'i o'chira oladi.",
            show_alert=True,
        )
        return

    await callback.message.edit_reply_markup(reply_markup=confirm_delete_keyboard(entry_id))
    await callback.answer("Rostdan o'chirilsinmi?")


@router.callback_query(F.data.startswith("delno:"))
async def cb_delete_cancel(callback: CallbackQuery):
    entry_id = int(callback.data.split(":")[1])
    try:
        await callback.message.edit_reply_markup(reply_markup=entry_keyboard(entry_id))
    except TelegramBadRequest:
        pass
    await callback.answer("Bekor qilindi.")


@router.callback_query(F.data.startswith("delok:"))
async def cb_delete_confirm(callback: CallbackQuery):
    entry_id = int(callback.data.split(":")[1])
    user = await _ensure_user(callback.from_user)
    entry = await db.get_entry(entry_id, user["family_id"])

    if entry is None:
        await callback.answer("Yozuv topilmadi — ehtimol allaqachon o'chirilgan.", show_alert=True)
        return
    if not _can_delete(user, entry):
        await callback.answer(
            "Bu yozuvni faqat uni qo'shgan a'zo yoki oila boshlig'i o'chira oladi.",
            show_alert=True,
        )
        return

    await db.delete_entry(entry_id, user["family_id"])
    await callback.answer("🗑 O'chirildi.")
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
    query = (message.text or "").strip()
    if len(query) < 2:
        await message.answer("Kamida 2 ta harfdan iborat so'z yuboring yoki /cancel yozing.")
        return

    data = await state.get_data()
    category_id = data.get("category_id")
    user = await _ensure_user(message.from_user)
    await state.clear()

    entries = await db.search_entries(
        user["family_id"], query, category_id=category_id, limit=SEARCH_LIMIT
    )
    await _show_results(message, entries, user, query, category_id)


@router.message(AddEntry.waiting_content)
async def handle_new_entry(message: Message, state: FSMContext):
    data = await state.get_data()
    category_id = data.get("category_id")
    if category_id is None:
        await state.clear()
        await message.answer("Qaysi toifaga qo'shishni bilmayapman. /categories dan qaytadan tanlang.")
        return

    category = await db.get_category(category_id)
    if category is None:
        await state.clear()
        await message.answer("Bu toifa endi mavjud emas. /categories dan qaytadan tanlang.")
        return

    user = await _ensure_user(message.from_user)
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
        await message.answer(
            "Bu turdagi kontentni saqlay olmayman. Matn, rasm, video, hujjat yoki ovozli xabar yuboring."
        )
        return

    await state.clear()
    await message.answer(
        f"✅ Saqlandi! («{_esc(category['name'])}»)\n\nYana qo'shish uchun /categories dan foydalaning."
    )
