# Oila ma'lumotlari boti

Jadvaldagi 42 ta oila toifasini (rasmlar, hujjatlar, ro'yxatlar, parollar o'rniga saqlanadigan
narsalar va h.k.) Telegram orqali saqlab, kerak bo'lganda tezda topib beruvchi bot.

## Qanday ishlaydi

- `/start` — ro'yxatdan o'tasiz, sizga yangi "oila" va unga qo'shilish kodi yaratiladi
- `/join KOD` — oila a'zolari shu kod bilan bir xil oilaga qo'shiladi (barchasi bitta ma'lumot bazasini ko'radi)
- `/categories` — 42 ta toifa ro'yxati (sahifalab ko'rsatiladi)
- `/search so'z` — barcha toifalar ichidan matn va izohlar bo'yicha qidirish
- `/family` — oila kodi va a'zolar ro'yxati (rollari bilan)
- `/help` — qisqacha yordam
- Toifani tanlab **➕ Qo'shish** — matn, rasm, video, hujjat, ovozli xabar yuboriladi va saqlanadi
- **👀 Ko'rish** — o'sha toifadagi yozuvlar 5 tadan sahifalab chiqadi (kim, qachon qo'shgani bilan)
- **🔍 Qidirish** — faqat shu toifa ichidan qidiradi
- **🗑 O'chirish** — har bir yozuv ostida. Oila boshlig'i (`asosiy`) hamma yozuvni,
  qolgan a'zolar faqat o'zi qo'shganini o'chira oladi

## Xavfsizlik

`BOT_TOKEN` faqat `.env` faylida (lokal) yoki Railway'ning Variables bo'limida turadi.
`.env`, `venv/` va `__pycache__/` `.gitignore` orqali git'dan chiqarilgan — ularni hech qachon
commit qilmang. Agar token bir marta repoga tushgan bo'lsa, BotFather'da `/revoke` qilib
yangisini oling: git tarixida qolgan eski token baribir amal qilaveradi.

## Railway'ga joylashtirish

1. **Bot yaratish**: Telegram'da [@BotFather](https://t.me/BotFather) ga yozing, `/newbot`,
   tokenni saqlab qo'ying.
2. **Railway'da loyiha**: railway.app → New Project → shu papkani GitHub repo qilib yuklang
   (yoki Railway CLI: `railway init`, `railway up`).
3. **Postgres qo'shish**: loyihaga "+ New" → "Database" → "PostgreSQL" qo'shing. Railway
   avtomatik `DATABASE_URL` environment variable'ini yaratadi va botga ulaydi.
4. **BOT_TOKEN qo'shish**: loyiha Settings → Variables → `BOT_TOKEN` ni BotFather'dan olgan
   token bilan qo'shing.
5. **Deploy**: Railway `Procfile`'ni ko'rib, `worker: python main.py` jarayonini ishga
   tushiradi. Birinchi ishga tushishda `db.init_db()` avtomatik jadval va 42 toifani yaratadi.

## Lokal ishga tushirish (test uchun)

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # tokenlarni to'ldiring
python main.py
```

## Tuzilishi

- `main.py` — botni ishga tushirish (polling)
- `config.py` — `.env` / environment o'zgaruvchilari
- `db.py` — Postgres sxemasi va barcha so'rovlar
- `storage.py` — FSM holatlarini Postgres'da saqlash (restartdan keyin ham yo'qolmaydi)
- `handlers.py` — buyruqlar va tugmalar mantiqi
- `keyboards.py` — inline klaviaturalar
- `seed_data.py` — 42 ta toifa ro'yxati

## Keyingi qadamlar (ixtiyoriy)

- Eslatmalar: masalan hujjat muddati yaqinlashganda bot avtomatik eslatib turishi
- Yozuvni tahrirlash (hozircha faqat o'chirib, qaytadan qo'shish mumkin)
- Oila boshlig'i a'zolarni chiqarib yuborishi / rol berishi
