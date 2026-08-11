from aiogram import F, Router
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

import db
from keyboards import back_to_category_keyboard, categories_keyboard, category_actions_keyboard

router = Router()


class AddEntry(StatesGroup):
    waiting_content = State()


async def _ensure_user(message: Message):
    user = await db.get_user(message.from_user.id)
    if user is None:
        user = await db.create_user_with_new_family(
            message.from_user.id, message.from_user.full_name
        )
    return user


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    user = await _ensure_user(message)
    invite_code = await db.get_family_invite_code(user["family_id"])
    await message.answer(
        "Assalomu alaykum! Bu — oilaviy ma'lumotlar boti.\n\n"
        "Bu yerda oilangiz uchun muhim narsalarni (rasm, video, hujjat, matn) "
        "toifalar bo'yicha saqlab, kerak bo'lganda tezda topib olishingiz mumkin.\n\n"
        f"Oilangiz kodi: <code>{invite_code}</code>\n"
        "Boshqa a'zolar shu kod bilan /join buyrug'i orqali qo'shilishi mumkin.\n\n"
        "Toifalarni ko'rish uchun /categories buyrug'ini yuboring.",
        parse_mode="HTML",
    )


@router.message(Command("join"))
async def cmd_join(message: Message, command: CommandObject):
    if not command.args:
        await message.answer("Iltimos, kodni ham yozing: /join ABC123")
        return
    family = await db.join_family(message.from_user.id, message.from_user.full_name, command.args)
    if family is None:
        await message.answer("Bunday kod bilan oila topilmadi. Kodni tekshirib qayta urinib ko'ring.")
        return
    await message.answer("Oilaga muvaffaqiyatli qo'shildingiz! Endi /categories buyrug'idan foydalaning.")


@router.message(Command("family"))
async def cmd_family(message: Message):
    user = await _ensure_user(message)
    invite_code = await db.get_family_invite_code(user["family_id"])
    await message.answer(
        f"Oilangiz kodi: <code>{invite_code}</code>\n"
        "Buni oila a'zolaringizga yuboring, ular /join {kod} orqali qo'shiladi.",
        parse_mode="HTML",
    )


@router.message(Command("categories"))
async def cmd_categories(message: Message, state: FSMContext):
    await state.clear()
    await _ensure_user(message)
    categories = await db.list_categories()
    await message.answer(
        "📂 Oila guruhlari — kerakli toifani tanlang:",
        reply_markup=categories_keyboard(categories, page=0),
    )


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Bekor qilindi.")


@router.callback_query(F.data.startswith("page:"))
async def cb_page(callback: CallbackQuery):
    page = int(callback.data.split(":")[1])
    categories = await db.list_categories()
    await callback.message.edit_text(
        "📂 Oila guruhlari — kerakli toifani tanlang:",
        reply_markup=categories_keyboard(categories, page=page),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("cat:"))
async def cb_category(callback: CallbackQuery):
    category_id = int(callback.data.split(":")[1])
    category = await db.get_category(category_id)
    user = await db.get_user(callback.from_user.id)
    count = await db.count_entries(user["family_id"], category_id)
    await callback.message.edit_text(
        f"<b>{category['name']}</b>\n<i>{category['description']}</i>\n\n"
        f"Saqlangan yozuvlar: {count}",
        parse_mode="HTML",
        reply_markup=category_actions_keyboard(category_id, count),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("add:"))
async def cb_add(callback: CallbackQuery, state: FSMContext):
    category_id = int(callback.data.split(":")[1])
    await state.set_state(AddEntry.waiting_content)
    await state.update_data(category_id=category_id)
    category = await db.get_category(category_id)
    await callback.message.edit_text(
        f"<b>{category['name']}</b> toifasiga qo'shish.\n\n"
        "Matn, rasm, video yoki hujjat yuboring. Bekor qilish uchun /cancel yozing.",
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("view:"))
async def cb_view(callback: CallbackQuery):
    category_id = int(callback.data.split(":")[1])
    user = await db.get_user(callback.from_user.id)
    entries = await db.list_entries(user["family_id"], category_id)
    category = await db.get_category(category_id)

    if not entries:
        await callback.message.edit_text(
            f"<b>{category['name']}</b> toifasida hali hech narsa yo'q.",
            parse_mode="HTML",
            reply_markup=back_to_category_keyboard(category_id),
        )
        await callback.answer()
        return

    await callback.answer()
    await callback.message.answer(f"<b>{category['name']}</b> — {len(entries)} ta yozuv:", parse_mode="HTML")

    for entry in entries[:20]:  # oxirgi 20 tasi bilan cheklaymiz
        who = entry["full_name"] or "Noma'lum"
        when = entry["created_at"].strftime("%d.%m.%Y %H:%M")
        caption = f"👤 {who} | 🕒 {when}"
        if entry["content_type"] == "text":
            await callback.message.answer(f"{caption}\n\n{entry['text_content']}")
        elif entry["content_type"] == "photo":
            await callback.message.answer_photo(entry["file_id"], caption=caption)
        elif entry["content_type"] == "video":
            await callback.message.answer_video(entry["file_id"], caption=caption)
        elif entry["content_type"] == "document":
            await callback.message.answer_document(entry["file_id"], caption=caption)
        elif entry["content_type"] == "voice":
            await callback.message.answer_voice(entry["file_id"], caption=caption)

    await callback.message.answer(
        "Yana amal tanlang:", reply_markup=back_to_category_keyboard(category_id)
    )


@router.message(AddEntry.waiting_content)
async def handle_new_entry(message: Message, state: FSMContext):
    data = await state.get_data()
    category_id = data["category_id"]
    user = await db.get_user(message.from_user.id)

    if message.text:
        await db.add_entry(user["family_id"], category_id, user["id"], "text", text_content=message.text)
    elif message.photo:
        await db.add_entry(
            user["family_id"], category_id, user["id"], "photo",
            file_id=message.photo[-1].file_id, caption=message.caption,
        )
    elif message.video:
        await db.add_entry(
            user["family_id"], category_id, user["id"], "video",
            file_id=message.video.file_id, caption=message.caption,
        )
    elif message.document:
        await db.add_entry(
            user["family_id"], category_id, user["id"], "document",
            file_id=message.document.file_id, caption=message.caption,
        )
    elif message.voice:
        await db.add_entry(
            user["family_id"], category_id, user["id"], "voice",
            file_id=message.voice.file_id,
        )
    else:
        await message.answer("Bu turdagi kontentni saqlay olmayman. Matn, rasm, video yoki hujjat yuboring.")
        return

    await state.clear()
    category = await db.get_category(category_id)
    await message.answer(
        f"✅ Saqlandi! («{category['name']}»)\n\nYana qo'shish uchun /categories dan foydalaning."
    )
