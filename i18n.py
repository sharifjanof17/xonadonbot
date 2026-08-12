"""Bot matnlari: o'zbekcha (uz) va ruscha (ru).

t(lang, "kalit", ...) — matnni tanlangan tilda qaytaradi.
localized(record, "name", lang) — bazadagi ustunning tilga mos variantini oladi.
"""

DEFAULT_LANG = "uz"
LANGUAGES = {"uz": "🇺🇿 O'zbekcha", "ru": "🇷🇺 Русский"}

TEXTS: dict[str, dict[str, str]] = {
    # --- til
    "choose_language": {
        "uz": "Tilni tanlang:",
        "ru": "Выберите язык:",
    },
    "language_saved": {
        "uz": "✅ Til o'zgartirildi: O'zbekcha",
        "ru": "✅ Язык изменён: Русский",
    },
    # --- start / help
    "start": {
        "uz": (
            "Assalomu alaykum! Bu — oilaviy ma'lumotlar boti.\n\n"
            "Bu yerda oilangiz uchun muhim narsalarni (rasm, video, hujjat, matn) "
            "toifalar bo'yicha saqlab, kerak bo'lganda tezda topib olishingiz mumkin.\n\n"
            "Oilangiz kodi: <code>{code}</code>\n"
            "Boshqa a'zolar shu kod bilan /join buyrug'i orqali qo'shilishi mumkin.\n\n"
            "Toifalarni ko'rish uchun /categories, yordam uchun /help."
        ),
        "ru": (
            "Здравствуйте! Это — бот семейных данных.\n\n"
            "Здесь вы можете хранить всё важное для семьи (фото, видео, документы, текст) "
            "по категориям и быстро находить нужное.\n\n"
            "Код вашей семьи: <code>{code}</code>\n"
            "Другие члены семьи присоединяются по этому коду командой /join.\n\n"
            "Список категорий — /categories, помощь — /help."
        ),
    },
    "help": {
        "uz": (
            "<b>Buyruqlar</b>\n"
            "/categories — 42 ta toifa ro'yxati\n"
            "/search so'z — barcha toifalar ichidan matn bo'yicha qidirish\n"
            "/family — oila kodi va a'zolar ro'yxati\n"
            "/join KOD — kod orqali oilaga qo'shilish\n"
            "/til — tilni o'zgartirish\n"
            "/cancel — boshlangan amalni bekor qilish\n\n"
            "<b>Qanday saqlanadi</b>\n"
            "Toifa → ➕ Qo'shish → bot aynan shu toifaga nima kerakligini so'raydi, "
            "siz matn, rasm, video, hujjat yoki ovozli xabar yuborasiz.\n\n"
            "<b>O'chirish</b>\n"
            "Har bir yozuv ostidagi 🗑 tugma. Oila boshlig'i hamma yozuvni, "
            "qolgan a'zolar faqat o'zi qo'shganini o'chira oladi."
        ),
        "ru": (
            "<b>Команды</b>\n"
            "/categories — список из 42 категорий\n"
            "/search слово — поиск по тексту во всех категориях\n"
            "/family — код семьи и список членов\n"
            "/join КОД — присоединиться к семье по коду\n"
            "/til — сменить язык\n"
            "/cancel — отменить начатое действие\n\n"
            "<b>Как сохранять</b>\n"
            "Категория → ➕ Добавить → бот спросит, что именно нужно для этой категории, "
            "вы отправляете текст, фото, видео, документ или голосовое.\n\n"
            "<b>Удаление</b>\n"
            "Кнопка 🗑 под каждой записью. Глава семьи может удалить любую запись, "
            "остальные — только свои."
        ),
    },
    # --- oila
    "join_usage": {
        "uz": "Iltimos, kodni ham yozing: /join ABC123",
        "ru": "Пожалуйста, укажите код: /join ABC123",
    },
    "join_not_found": {
        "uz": "Bunday kod bilan oila topilmadi. Kodni tekshirib qayta urinib ko'ring.",
        "ru": "Семья с таким кодом не найдена. Проверьте код и попробуйте снова.",
    },
    "join_ok": {
        "uz": "Oilaga muvaffaqiyatli qo'shildingiz! Endi /categories buyrug'idan foydalaning.",
        "ru": "Вы успешно присоединились к семье! Теперь используйте /categories.",
    },
    "family_header": {
        "uz": (
            "Oilangiz kodi: <code>{code}</code>\n"
            "Buni oila a'zolaringizga yuboring, ular <code>/join KOD</code> orqali qo'shiladi.\n\n"
            "<b>A'zolar ({count}):</b>"
        ),
        "ru": (
            "Код вашей семьи: <code>{code}</code>\n"
            "Отправьте его родным — они присоединятся командой <code>/join КОД</code>.\n\n"
            "<b>Члены семьи ({count}):</b>"
        ),
    },
    "role_head": {"uz": "oila boshlig'i", "ru": "глава семьи"},
    "role_member": {"uz": "a'zo", "ru": "член семьи"},
    "unknown_person": {"uz": "Noma'lum", "ru": "Неизвестно"},
    # --- toifalar
    "categories_title": {
        "uz": "📂 Oila guruhlari — kerakli toifani tanlang:",
        "ru": "📂 Семейные категории — выберите нужную:",
    },
    "category_not_found": {
        "uz": "Bunday toifa topilmadi.",
        "ru": "Такая категория не найдена.",
    },
    "category_card": {
        "uz": "<b>{name}</b>\n<i>{description}</i>\n\nSaqlangan yozuvlar: {count}",
        "ru": "<b>{name}</b>\n<i>{description}</i>\n\nСохранённых записей: {count}",
    },
    # --- qo'shish
    "add_intro": {
        "uz": "<b>{name}</b> toifasiga qo'shish.\n\n{prompt}\n\n<i>Bekor qilish uchun /cancel.</i>",
        "ru": "Добавление в категорию <b>{name}</b>.\n\n{prompt}\n\n<i>Для отмены — /cancel.</i>",
    },
    "add_prompt_default": {
        "uz": "✍️ Matn, rasm, video, hujjat yoki ovozli xabar yuboring.",
        "ru": "✍️ Отправьте текст, фото, видео, документ или голосовое сообщение.",
    },
    "saved": {
        "uz": "✅ Saqlandi! («{name}»)\n\nYana qo'shish uchun /categories dan foydalaning.",
        "ru": "✅ Сохранено! («{name}»)\n\nЧтобы добавить ещё — /categories.",
    },
    "unsupported_content": {
        "uz": "Bu turdagi kontentni saqlay olmayman. Matn, rasm, video, hujjat yoki ovozli xabar yuboring.",
        "ru": "Такой тип содержимого я сохранить не могу. Отправьте текст, фото, видео, документ или голосовое.",
    },
    "add_lost_category": {
        "uz": "Qaysi toifaga qo'shishni bilmayapman. /categories dan qaytadan tanlang.",
        "ru": "Не понимаю, в какую категорию добавить. Выберите заново через /categories.",
    },
    "category_gone": {
        "uz": "Bu toifa endi mavjud emas. /categories dan qaytadan tanlang.",
        "ru": "Этой категории больше нет. Выберите заново через /categories.",
    },
    # --- ko'rish
    "entries_empty": {
        "uz": "<b>{name}</b> toifasida hali hech narsa yo'q.",
        "ru": "В категории <b>{name}</b> пока ничего нет.",
    },
    "entries_header": {
        "uz": "<b>{name}</b> — jami {total} ta yozuv (sahifa {page}/{pages}):",
        "ru": "<b>{name}</b> — всего записей: {total} (страница {page}/{pages}):",
    },
    "page_label": {"uz": "Sahifa {page}/{pages}", "ru": "Стр. {page}/{pages}"},
    "unknown_entry_type": {
        "uz": "⚠️ Noma'lum turdagi yozuv.",
        "ru": "⚠️ Запись неизвестного типа.",
    },
    # --- qidiruv
    "search_usage": {
        "uz": "Qidirish uchun so'z yozing, masalan: <code>/search pasport</code>\n(kamida 2 ta harf)",
        "ru": "Укажите слово для поиска, например: <code>/search паспорт</code>\n(минимум 2 буквы)",
    },
    "search_prompt": {
        "uz": (
            "🔍 <b>{name}</b> ichidan qidirish.\n\n"
            "Qidirmoqchi bo'lgan so'zni yuboring. Bekor qilish uchun /cancel."
        ),
        "ru": (
            "🔍 Поиск в категории <b>{name}</b>.\n\n"
            "Отправьте слово для поиска. Для отмены — /cancel."
        ),
    },
    "search_too_short": {
        "uz": "Kamida 2 ta harfdan iborat so'z yuboring yoki /cancel yozing.",
        "ru": "Отправьте слово хотя бы из 2 букв или напишите /cancel.",
    },
    "search_empty": {
        "uz": "🔍 «{query}» bo'yicha hech narsa topilmadi.",
        "ru": "🔍 По запросу «{query}» ничего не найдено.",
    },
    "search_results": {
        "uz": "🔍 «{query}» — {count} ta natija:",
        "ru": "🔍 «{query}» — найдено: {count}",
    },
    # --- o'chirish
    "delete_ask": {"uz": "Rostdan o'chirilsinmi?", "ru": "Действительно удалить?"},
    "deleted": {"uz": "🗑 O'chirildi.", "ru": "🗑 Удалено."},
    "delete_cancelled": {"uz": "Bekor qilindi.", "ru": "Отменено."},
    "entry_not_found": {
        "uz": "Yozuv topilmadi — ehtimol allaqachon o'chirilgan.",
        "ru": "Запись не найдена — возможно, она уже удалена.",
    },
    "no_delete_right": {
        "uz": "Bu yozuvni faqat uni qo'shgan a'zo yoki oila boshlig'i o'chira oladi.",
        "ru": "Удалить эту запись может только её автор или глава семьи.",
    },
    "cancelled": {"uz": "Bekor qilindi.", "ru": "Отменено."},
    "more_actions": {"uz": "Yana amal tanlang:", "ru": "Выберите следующее действие:"},
    # --- tugmalar
    "btn_add": {"uz": "➕ Qo'shish", "ru": "➕ Добавить"},
    "btn_view": {"uz": "👀 Ko'rish ({count})", "ru": "👀 Посмотреть ({count})"},
    "btn_search": {"uz": "🔍 Qidirish", "ru": "🔍 Поиск"},
    "btn_back_categories": {"uz": "⬅️ Toifalarga qaytish", "ru": "⬅️ К категориям"},
    "btn_back_category": {"uz": "⬅️ Toifaga qaytish", "ru": "⬅️ К категории"},
    "btn_back": {"uz": "⬅️ Orqaga", "ru": "⬅️ Назад"},
    "btn_prev": {"uz": "⬅️ Oldingi", "ru": "⬅️ Предыдущая"},
    "btn_next": {"uz": "Keyingi ➡️", "ru": "Следующая ➡️"},
    "btn_delete": {"uz": "🗑 O'chirish", "ru": "🗑 Удалить"},
    "btn_delete_yes": {"uz": "✅ Ha, o'chirilsin", "ru": "✅ Да, удалить"},
    "btn_delete_no": {"uz": "❌ Yo'q", "ru": "❌ Нет"},
}

# Navigatsiya xabarini tanib olish uchun (barcha tillardagi "Sahifa" boshlanishi)
PAGE_LABEL_PREFIXES = tuple(
    text.split("{")[0] for text in TEXTS["page_label"].values() if text.split("{")[0]
)


def normalize(lang: str | None) -> str:
    return lang if lang in LANGUAGES else DEFAULT_LANG


def t(lang: str | None, key: str, **kwargs) -> str:
    text = TEXTS[key][normalize(lang)]
    return text.format(**kwargs) if kwargs else text


def localized(record, field: str, lang: str | None) -> str:
    """Bazadagi ustunning tilga mos variantini qaytaradi (ru bo'lmasa — asosiysi)."""
    if normalize(lang) == "ru":
        value = record[f"{field}_ru"]
        if value:
            return value
    return record[field] or ""
