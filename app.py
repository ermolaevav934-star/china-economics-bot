import os
import asyncio
import threading
from flask import Flask, jsonify
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ConversationHandler

# ============================================================
# ТОКЕН БОТА - БЕРЁМ ИЗ ПЕРЕМЕННЫХ ОКРУЖЕНИЯ
# ============================================================
TOKEN = os.environ.get("8956267241:AAFJwoo86GF3mtrQ5p6t_Yh7BDUJbEwN7ms")
if not TOKEN:
    raise ValueError("TELEGRAM_TOKEN environment variable not set!")

# Flask приложение для Koyeb
app = Flask(__name__)

# Состояния для ConversationHandler
WAITING_TERM = 1

# База данных избранного
favorites_db = {}

# ============================================================
# 20 ЭКОНОМИЧЕСКИХ ТЕРМИНОВ
# ============================================================
term_data = {
    "通货膨胀": {
        "pinyin": "tōng huò péng zhàng",
        "tones": "1-4-2-4",
        "ru": "Инфляция",
        "example_cn": "控制通货膨胀是央行的主要任务",
        "example_ru": "Контроль инфляции — главная задача центробанка."
    },
    "国内生产总值": {
        "pinyin": "guó nèi shēng chǎn zǒng zhí",
        "tones": "2-4-1-3-3-2",
        "ru": "Валовой внутренний продукт (ВВП)",
        "example_cn": "去年国内生产总值增长了5%",
        "example_ru": "В прошлом году ВВП вырос на 5%."
    },
    "通货紧缩": {
        "pinyin": "tōng huò jǐn suō",
        "tones": "1-4-3-1",
        "ru": "Дефляция",
        "example_cn": "通货紧缩会导致消费需求下降",
        "example_ru": "Дефляция ведёт к снижению потребительского спроса."
    },
    "边际效应": {
        "pinyin": "biān jì xiào yìng",
        "tones": "1-4-4-4",
        "ru": "Предельная полезность",
        "example_cn": "经济学家研究消费的边际效应",
        "example_ru": "Экономисты изучают предельную полезность потребления."
    },
    "机会成本": {
        "pinyin": "jī huì chéng běn",
        "tones": "1-4-2-3",
        "ru": "Альтернативные издержки",
        "example_cn": "选择上大学的机会成本是放弃的工作收入",
        "example_ru": "Альтернативные издержки поступления в университет — потерянный заработок."
    },
    "供需关系": {
        "pinyin": "gōng xū guān xì",
        "tones": "1-1-1-4",
        "ru": "Спрос и предложение",
        "example_cn": "价格由供需关系决定",
        "example_ru": "Цена определяется спросом и предложением."
    },
    "基尼系数": {
        "pinyin": "jī ní xì shù",
        "tones": "1-2-4-4",
        "ru": "Коэффициент Джини",
        "example_cn": "基尼系数衡量收入不平等",
        "example_ru": "Коэффициент Джини измеряет неравенство доходов."
    },
    "恩格尔系数": {
        "pinyin": "ēn gé ěr xì shù",
        "tones": "1-2-3-4-4",
        "ru": "Коэффициент Энгеля",
        "example_cn": "恩格尔系数越高，生活水平越低",
        "example_ru": "Чем выше коэффициент Энгеля, тем ниже уровень жизни."
    },
    "货币政策": {
        "pinyin": "huò bì zhèng cè",
        "tones": "4-4-4-4",
        "ru": "Денежно-кредитная политика",
        "example_cn": "央行实施宽松的货币政策",
        "example_ru": "Центробанк проводит мягкую денежно-кредитную политику."
    },
    "财政政策": {
        "pinyin": "cái zhèng zhèng cè",
        "tones": "2-4-4-4",
        "ru": "Фискальная (бюджетно-налоговая) политика",
        "example_cn": "政府通过财政政策刺激经济",
        "example_ru": "Правительство стимулирует экономику через фискальную политику."
    },
    "量化宽松": {
        "pinyin": "liàng huà kuān sōng",
        "tones": "4-4-1-1",
        "ru": "Количественное смягчение (QE)",
        "example_cn": "美联储推出量化宽松政策",
        "example_ru": "ФРС запускает программу количественного смягчения."
    },
    "垄断": {
        "pinyin": "lǒng duàn",
        "tones": "3-4",
        "ru": "Монополия",
        "example_cn": "反垄断法禁止市场垄断",
        "example_ru": "Антимонопольное законодательство запрещает монополизацию рынка."
    },
    "完全竞争": {
        "pinyin": "wán quán jìng zhēng",
        "tones": "2-2-4-1",
        "ru": "Совершенная конкуренция",
        "example_cn": "完全竞争是理想市场模型",
        "example_ru": "Совершенная конкуренция — идеальная модель рынка."
    },
    "市场失灵": {
        "pinyin": "shì chǎng shī líng",
        "tones": "4-3-1-2",
        "ru": "Фиаско (провал) рынка",
        "example_cn": "外部性会导致市场失灵",
        "example_ru": "Экстерналии ведут к фиаско рынка."
    },
    "国民收入": {
        "pinyin": "guó mín shōu rù",
        "tones": "2-2-1-4",
        "ru": "Национальный доход",
        "example_cn": "国民收入反映经济整体状况",
        "example_ru": "Национальный доход отражает общее состояние экономики."
    },
    "流动性陷阱": {
        "pinyin": "liú dòng xìng xiàn jǐng",
        "tones": "2-4-4-4-3",
        "ru": "Ликвидная ловушка",
        "example_cn": "利率接近于零时出现流动性陷阱",
        "example_ru": "При околонулевых ставках возникает ликвидная ловушка."
    },
    "比较优势": {
        "pinyin": "bǐ jiào yōu shì",
        "tones": "3-4-1-4",
        "ru": "Сравнительное преимущество",
        "example_cn": "国际贸易基于比较优势",
        "example_ru": "Международная торговля основана на сравнительных преимуществах."
    },
    "贸易顺差": {
        "pinyin": "mào yì shùn chā",
        "tones": "4-4-4-1",
        "ru": "Положительное сальдо торгового баланса (профицит)",
        "example_cn": "中国长期保持贸易顺差",
        "example_ru": "Китай долгое время сохраняет положительное торговое сальдо."
    },
    "贸易逆差": {
        "pinyin": "mào yì nì chā",
        "tones": "4-4-4-1",
        "ru": "Дефицит торгового баланса",
        "example_cn": "进口大于出口造成贸易逆差",
        "example_ru": "Импорт, превышающий экспорт, создаёт торговый дефицит."
    },
    "购买力平价": {
        "pinyin": "gòu mǎi lì píng jià",
        "tones": "4-3-4-2-4",
        "ru": "Паритет покупательной способности (ППС)",
        "example_cn": "购买力平价比较各国实际生活水平",
        "example_ru": "Паритет покупательной способности сравнивает реальный уровень жизни в разных странах."
    }
}

# ============================================================
# ФУНКЦИИ БОТА
# ============================================================

async def start(update: Update, context):
    user_id = update.effective_user.id
    if user_id not in favorites_db:
        favorites_db[user_id] = []

    keyboard = [
        [InlineKeyboardButton("🔍 Перевести термин", callback_data="translate")],
        [InlineKeyboardButton("📚 Моё избранное", callback_data="favorites")],
        [InlineKeyboardButton("❓ Помощь", callback_data="help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "🇨🇳 ChinaEconomicsBot\n\n"
        "Перевожу китайские экономические термины → русский + пиньинь + примеры.\n\n"
        "Что делать:",
        reply_markup=reply_markup
    )

async def button_handler(update: Update, context):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    data = query.data

    if data == "translate":
        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_main")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "Введите китайский термин (иероглифами)\n\nПример: 流动性",
            reply_markup=reply_markup
        )
        return WAITING_TERM

    elif data == "favorites":
        favs = favorites_db.get(user_id, [])
        if not favs:
            text = "📚 У вас пока нет сохранённых терминов."
        else:
            text = "📚 Ваше избранное:\n\n"
            for idx, term in enumerate(favs, 1):
                ru = term_data.get(term, {}).get("ru", "?")
                text += f"{idx}. {term} — {ru}\n"
            text += "\n🗑️ Чтобы удалить, нажмите /delete"
        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_main")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text, reply_markup=reply_markup)

    elif data == "help":
        text = (
            "❓ Как пользоваться\n\n"
            "1. Нажмите «Перевести термин»\n"
            "2. Введите иероглифы\n"
            "3. Получите перевод + пиньинь + пример\n"
            "4. Сохраняйте в избранное\n\n"
            "🚀 В следующей версии: аудио, экспорт, тесты"
        )
        keyboard = [[InlineKeyboardButton("🔍 Перевести", callback_data="translate")],
                    [InlineKeyboardButton("🔙 Назад", callback_data="back_main")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text, reply_markup=reply_markup)

    elif data == "back_main":
        await start(update, context)

    elif data.startswith("save_"):
        term = data[5:]
        user_favs = favorites_db[user_id]
        if term not in user_favs:
            user_favs.append(term)
        ru = term_data.get(term, {}).get("ru", term)
        msg = f"✅ Сохранено!\n\n«{term} — {ru}»\nдобавлен в избранное.\n\n📚 Всего терминов: {len(user_favs)}"
        keyboard = [
            [InlineKeyboardButton("🔍 Перевести ещё", callback_data="translate")],
            [InlineKeyboardButton("📚 Избранное", callback_data="favorites")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(msg, reply_markup=reply_markup)

    elif data == "new_translate":
        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_main")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "Введите китайский термин (иероглифами)\n\nПример: 流动性",
            reply_markup=reply_markup
        )
        return WAITING_TERM

async def receive_term(update: Update, context):
    user_id = update.effective_user.id
    term = update.message.text.strip()

    if term in term_data:
        info = term_data[term]
        text = (
            f"{term}\n"
            f"{info['pinyin']} (тоны: {info['tones']})\n\n"
            f"🇷🇺 {info['ru']}\n\n"
            f"Пример:\n“{info['example_cn']}”\n→ {info['example_ru']}"
        )
        keyboard = [
            [InlineKeyboardButton("💾 Сохранить в избранное", callback_data=f"save_{term}")],
            [InlineKeyboardButton("🔄 Новый перевод", callback_data="new_translate")],
            [InlineKeyboardButton("📖 Ещё пример", callback_data="more_example")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(text, reply_markup=reply_markup)
    else:
        await update.message.reply_text("❌ Термин не найден. Попробуйте другой (только иероглифами).")

    return ConversationHandler.END

async def more_example(update: Update, context):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("📖 Дополнительные примеры появятся в следующей версии.\nПока используйте основной перевод.")

async def delete_handler(update: Update, context):
    user_id = update.effective_user.id
    favs = favorites_db.get(user_id, [])
    if favs:
        favs.pop()
        await update.message.reply_text("🗑️ Последний термин удалён из избранного.")
    else:
        await update.message.reply_text("Избранное пусто.")

# ============================================================
# ЗАПУСК БОТА В ОТДЕЛЬНОМ ПОТОКЕ
# ============================================================
def run_bot():
    """Запускает Telegram бота в отдельном потоке"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    application = Application.builder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("delete", delete_handler))
    
    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(button_handler, pattern="^translate$")],
        states={
            WAITING_TERM: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_term)]
        },
        fallbacks=[CallbackQueryHandler(button_handler, pattern="^back_main$")]
    )
    application.add_handler(conv_handler)
    application.add_handler(CallbackQueryHandler(button_handler, pattern="^(favorites|help|back_main|save_|new_translate)$"))
    application.add_handler(CallbackQueryHandler(more_example, pattern="^more_example$"))
    
    print("Бот запущен и работает!")
    application.run_polling()

# ============================================================
# FLASK - ДЛЯ KOYEB (health check)
# ============================================================
@app.route('/')
def home():
    return jsonify({"status": "running", "message": "ChinaEconomicsBot is alive!"})

@app.route('/health')
def health():
    return jsonify({"status": "ok"})

# ============================================================
# ЗАПУСК
# ============================================================
if __name__ == "__main__":
    # Запускаем бота в отдельном потоке
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.start()
    
    # Запускаем Flask сервер для health-проверок Koyeb
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)