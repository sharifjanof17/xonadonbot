# Oila ma'lumotlari boti

Jadvaldagi 42 ta oila toifasini (rasmlar, hujjatlar, ro'yxatlar, parollar o'rniga saqlanadigan
narsalar va h.k.) Telegram orqali saqlab, kerak bo'lganda tezda topib beruvchi bot.

## Qanday ishlaydi

- `/start` — ro'yxatdan o'tasiz, sizga yangi "oila" va unga qo'shilish kodi yaratiladi
- `/join KOD` — oila a'zolari shu kod bilan bir xil oilaga qo'shiladi (barchasi bitta ma'lumot bazasini ko'radi)
- `/categories` — 42 ta toifa ro'yxati (sahifalab ko'rsatiladi)
- Toifani tanlab **➕ Qo'shish** — matn, rasm, video yoki hujjat yuboriladi va saqlanadi
- **👀 Ko'rish** — o'sha toifada saqlangan barcha narsalar (kim, qachon qo'shgani bilan) chiqadi

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

## Keyingi qadamlar (ixtiyoriy)

- Rollarni (`asosiy` / `yordamchi`) haqiqiy huquq nazoratiga aylantirish (masalan, faqat
  `asosiy` o'chira olsin)
- Toifa ichida qidirish (matn bo'yicha)
- Eslatmalar: masalan hujjat muddati yaqinlashganda bot avtomatik eslatib turishi
