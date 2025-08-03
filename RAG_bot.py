from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
import logging
from Requests import answer
from indexer import reindex
import os
from dotenv import load_dotenv

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Загрузка переменных окружения
load_dotenv()

# Настройки языков
LANGUAGES = {
    'en': {
        'welcome': "🌟 *Welcome to Article Assistant!* 🌟\n\nPlease add an article first to enable question answering",
        'ask_btn': "Ask question",
        'article_btn': "Enter article",
        'lang_btn': "Change language",
        'prompt_btn': "Prompt settings",
        'lang_changed': "Language changed to English",
        'ask_prompt': "📝 Please enter your question about the article:",
        'processing': "🔍 Searching for answer in the article...",
        'indexing': "📚 Indexing article content...",
        'after_answer': "💡 You can ask another question or choose another option below",
        'cancel': "Cancel",
        'error': "❌ Error occurred",
        'enter_url': "🌐 Please enter the article URL:",
        'no_article_error': "⚠️ Please add an article first using the 'Enter article' button",
        'invalid_input': "⚠️ Please use the buttons below to interact with me",
        'index_success': "✅ Article indexed successfully!",
        'chunks_info': "Processed {} content chunks.\n\nYou can now ask questions about this article.",
        'prompt_menu': "✏️ Choose prompt option:",
        'default_prompt': "Use default prompt",
        'custom_prompt': "Write new prompt",
        'enter_custom_prompt': "📝 Enter your custom prompt (e.g., 'Answer in technical style'):",
        'prompt_saved': "✅ Custom prompt saved! Now ask your question.",
        'current_prompt': "Current prompt: {}"
    },
    'ru': {
        'welcome': "🌟 *Добро пожаловать в Ассистент Статей!* 🌟\n\nСначала добавьте статью, чтобы получить возможность задавать вопросы",
        'ask_btn': "Задать вопрос",
        'article_btn': "Ввести статью",
        'lang_btn': "Изменить язык",
        'prompt_btn': "Настройки промпта",
        'lang_changed': "Язык изменен на Русский",
        'ask_prompt': "📝 Пожалуйста, введите ваш вопрос по статье:",
        'processing': "🔍 Ищу ответ в статье...",
        'indexing': "📚 Индексирую содержание статьи...",
        'after_answer': "💡 Вы можете задать другой вопрос или выбрать другую опцию ниже",
        'cancel': "Отмена",
        'error': "❌ Произошла ошибка",
        'enter_url': "🌐 Введите URL статьи:",
        'no_article_error': "⚠️ Сначала добавьте статью, используя кнопку 'Ввести статью'",
        'invalid_input': "⚠️ Пожалуйста, используйте кнопки ниже для взаимодействия",
        'index_success': "✅ Статья успешно проиндексирована!",
        'chunks_info': "Обработано {} фрагментов контента.\n\nТеперь вы можете задавать вопросы по этой статье.",
        'prompt_menu': "✏️ Выберите вариант промпта:",
        'default_prompt': "Использовать стандартный промпт",
        'custom_prompt': "Написать свой промпт",
        'enter_custom_prompt': "📝 Введите ваш промпт (например, 'Отвечай в техническом стиле'):",
        'prompt_saved': "✅ Промпт сохранён! Теперь задайте вопрос.",
        'current_prompt': "Текущий промпт: {}"
    }
}

# Состояния беседы
(
    MAIN_MENU, ENTER_LINK, CHANGE_LANG, 
    ASK_QUESTION, PROMPT_MENU, ENTER_CUSTOM_PROMPT
) = range(6)

# Стандартный промпт
DEFAULT_PROMPT = {
    'en': """Expert Research Assistant Guidelines:

1. Source Accuracy:
   - Strictly use ONLY the provided context
   - For missing info: "The article doesn't specify"
   - Never hallucinate facts

2. Response Structure:
   - Core Answer (1 bolded sentence)
   - Key Evidence (3-5 bullet points max)
   - Practical Implications (when relevant)
   - Limitations (if data is incomplete)

3. Technical Content:
   - Code: ```python\n...\n``` 
   - Formulas: $E=mc^2$ format
   - Terms: "API (Application Programming Interface)"

4. Language Rules:
   - Match question's language
   - Auto-correct grammar subtly
   - Use ISO standards for dates/units

Context:
{context}

Question: {question}""",

    'ru': """Инструкции для эксперта-аналитика:

1. Точность данных:
   - Используйте ТОЛЬКО предоставленный контекст
   - При отсутствии данных: "В статье не указано"
   - Запрещено "додумывать" факты

2. Структура ответа:
   - Основной ответ (1 предложение жирным)
   - Доказательства (3-5 пунктов списка)
   - Практическое применение (если уместно)
   - Ограничения (при неполных данных)

3. Техническое оформление:
   - Код: ```python\n...\n```
   - Формулы: $E=mc^2$ 
   - Термины: "API (программный интерфейс)"

4. Языковые правила:
   - Соответствие языку вопроса
   - Коррекция ошибок в ответе
   - Даты/единицы в формате ISO

Контекст:
{context}

Вопрос: {question}"""
}

def get_main_menu_keyboard(lang: str, has_article: bool = False):
    """Создает клавиатуру главного меню"""
    buttons = []
    if has_article:
        buttons.append([KeyboardButton(LANGUAGES[lang]['ask_btn'])])
    buttons.extend([
        [KeyboardButton(LANGUAGES[lang]['article_btn'])],
        [KeyboardButton(LANGUAGES[lang]['lang_btn']), KeyboardButton(LANGUAGES[lang]['prompt_btn'])]
    ])
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)

def get_prompt_menu_keyboard(lang: str):
    """Клавиатура меню промптов"""
    return ReplyKeyboardMarkup([
        [KeyboardButton(LANGUAGES[lang]['default_prompt'])],
        [KeyboardButton(LANGUAGES[lang]['custom_prompt'])],
        [KeyboardButton(LANGUAGES[lang]['cancel'])]
    ], resize_keyboard=True)

def get_lang_menu_keyboard():
    """Создает меню выбора языка"""
    return ReplyKeyboardMarkup([
        [KeyboardButton("English 🇬🇧"), KeyboardButton("Русский 🇷🇺")]
    ], resize_keyboard=True)

def get_cancel_keyboard(lang: str):
    """Кнопка отмены"""
    return ReplyKeyboardMarkup([[KeyboardButton(LANGUAGES[lang]['cancel'])]], resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    context.user_data['lang'] = 'en'  # Язык по умолчанию
    context.user_data['has_article'] = False  # Флаг наличия статьи
    context.user_data['current_prompt'] = DEFAULT_PROMPT['en']  # Стандартный промпт
    lang = context.user_data['lang']
    
    await update.message.reply_text(
        LANGUAGES[lang]['welcome'],
        parse_mode='Markdown',
        reply_markup=get_main_menu_keyboard(lang, has_article=False)
    )
    return MAIN_MENU

async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Главное меню с обработкой ошибок"""
    lang = context.user_data.get('lang', 'en')
    has_article = context.user_data.get('has_article', False)
    text = update.message.text
    
    # Проверяем, является ли ввод одной из кнопок меню
    valid_commands = [
        LANGUAGES[lang]['ask_btn'],
        LANGUAGES[lang]['article_btn'],
        LANGUAGES[lang]['lang_btn'],
        LANGUAGES[lang]['prompt_btn'],
        LANGUAGES[lang]['cancel']
    ]
    
    if text not in valid_commands:
        await update.message.reply_text(
            LANGUAGES[lang]['invalid_input'],
            reply_markup=get_main_menu_keyboard(lang, has_article)
        )
        return MAIN_MENU
    
    # Обработка кнопки "Ask question"
    if text == LANGUAGES[lang]['ask_btn']:
        if not has_article:
            await update.message.reply_text(
                LANGUAGES[lang]['no_article_error'],
                reply_markup=get_main_menu_keyboard(lang, has_article)
            )
            return MAIN_MENU
        
        # Убрано сообщение с текущим промптом
        await update.message.reply_text(
            LANGUAGES[lang]['ask_prompt'],
            reply_markup=get_cancel_keyboard(lang)
        )
        return ASK_QUESTION
    
    
    # Обработка кнопки "Enter article"
    if text == LANGUAGES[lang]['article_btn']:
        await update.message.reply_text(
            LANGUAGES[lang]['enter_url'],
            reply_markup=get_cancel_keyboard(lang)
        )
        return ENTER_LINK
    
    # Обработка кнопки "Change language"
    if text == LANGUAGES[lang]['lang_btn']:
        await update.message.reply_text(
            "Выберите язык:" if lang == 'ru' else "Select language:",
            reply_markup=get_lang_menu_keyboard()
        )
        return CHANGE_LANG
    
    # Обработка кнопки "Prompt settings"
    if text == LANGUAGES[lang]['prompt_btn']:
        await update.message.reply_text(
            LANGUAGES[lang]['prompt_menu'],
            reply_markup=get_prompt_menu_keyboard(lang)
        )
        return PROMPT_MENU
    
    return MAIN_MENU

async def handle_prompt_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка меню промптов"""
    lang = context.user_data.get('lang', 'en')
    text = update.message.text
    
    if text == LANGUAGES[lang]['cancel']:
        await update.message.reply_text(
            "Отменено" if lang == 'ru' else "Canceled",
            reply_markup=get_main_menu_keyboard(lang, context.user_data.get('has_article', False))
        )
        return MAIN_MENU
    
    # Обработка выбора стандартного промпта
    if text == LANGUAGES[lang]['default_prompt']:
        context.user_data['current_prompt'] = DEFAULT_PROMPT[lang]
        await update.message.reply_text(
            LANGUAGES[lang]['current_prompt'].format(DEFAULT_PROMPT[lang]),
            reply_markup=get_main_menu_keyboard(lang, context.user_data.get('has_article', False))
        )
        return MAIN_MENU
    
    # Обработка выбора кастомного промпта
    if text == LANGUAGES[lang]['custom_prompt']:
        await update.message.reply_text(
            LANGUAGES[lang]['enter_custom_prompt'],
            reply_markup=get_cancel_keyboard(lang)
        )
        return ENTER_CUSTOM_PROMPT
    
    return PROMPT_MENU

async def handle_custom_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка ввода кастомного промпта"""
    lang = context.user_data.get('lang', 'en')
    text = update.message.text
    
    if text == LANGUAGES[lang]['cancel']:
        await update.message.reply_text(
            "Отменено" if lang == 'ru' else "Canceled",
            reply_markup=get_main_menu_keyboard(lang, context.user_data.get('has_article', False))
        )
        return MAIN_MENU
    
    # Сохраняем промпт
    context.user_data['current_prompt'] = text
    await update.message.reply_text(
        LANGUAGES[lang]['prompt_saved'],
        reply_markup=get_main_menu_keyboard(lang, context.user_data.get('has_article', False))
    )
    return MAIN_MENU

async def handle_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка вопросов с учетом промпта"""
    lang = context.user_data.get('lang', 'en')
    has_article = context.user_data.get('has_article', False)
    text = update.message.text
    
    if not has_article:
        await update.message.reply_text(
            LANGUAGES[lang]['no_article_error'],
            reply_markup=get_main_menu_keyboard(lang, has_article)
        )
        return MAIN_MENU
    
    if text == LANGUAGES[lang]['cancel']:
        await update.message.reply_text(
            "Отменено" if lang == 'ru' else "Canceled",
            reply_markup=get_main_menu_keyboard(lang, has_article)
        )
        return MAIN_MENU
    
    await update.message.reply_text(LANGUAGES[lang]['processing'])
    
    try:
        # Получаем текущий промпт
        current_prompt = context.user_data.get('current_prompt', DEFAULT_PROMPT[lang])
        
        # Формируем полный запрос с промптом
        full_query = f"{current_prompt}\n\nQuestion: {text}"
        
        response = answer(full_query)  # Передаем промпт + вопрос в функцию answer
        await update.message.reply_text(
            response,
            reply_markup=get_main_menu_keyboard(lang, has_article)
        )
        await update.message.reply_text(
            LANGUAGES[lang]['after_answer'],
            reply_markup=get_main_menu_keyboard(lang, has_article)
        )
    except Exception as e:
        error_msg = f"❌ Ошибка: {str(e)}" if lang == 'ru' else f"❌ Error: {str(e)}"
        await update.message.reply_text(
            error_msg,
            reply_markup=get_main_menu_keyboard(lang, has_article)
        )
    
    return MAIN_MENU

async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка добавления статей с проверкой URL"""
    lang = context.user_data.get('lang', 'en')
    text = update.message.text
    
    if text == LANGUAGES[lang]['cancel']:
        await update.message.reply_text(
            "Отменено" if lang == 'ru' else "Canceled",
            reply_markup=get_main_menu_keyboard(lang, context.user_data.get('has_article', False))
        )
        return MAIN_MENU
    
    # Простая проверка URL
    if not text.startswith(('http://', 'https://')):
        await update.message.reply_text(
            "⚠️ Пожалуйста, введите корректный URL (начинается с http:// или https://)" if lang == 'ru' 
            else "⚠️ Please enter a valid URL (starting with http:// or https://)",
            reply_markup=get_cancel_keyboard(lang)
        )
        return ENTER_LINK
    
    try:
        with open("Link.txt", "w", encoding="utf-8") as f:
            f.write(text)
        
        await update.message.reply_text(LANGUAGES[lang]['indexing'])
        num_chunks = reindex(text)
        
        # Устанавливаем флаг наличия статьи
        context.user_data['has_article'] = True
        
        # Первое сообщение об успешной индексации
        await update.message.reply_text(LANGUAGES[lang]['index_success'])
        
        # Второе сообщение с количеством чанков
        chunks_message = LANGUAGES[lang]['chunks_info'].format(num_chunks)
        await update.message.reply_text(
            chunks_message,
            reply_markup=get_main_menu_keyboard(lang, has_article=True)
        )
    except Exception as e:
        error_msg = (
            f"❌ Ошибка при индексации: {str(e)}" 
            if lang == 'ru' else 
            f"❌ Indexing error: {str(e)}"
        )
        await update.message.reply_text(
            error_msg,
            reply_markup=get_main_menu_keyboard(lang, False)
        )
    
    return MAIN_MENU

async def handle_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Смена языка"""
    lang_map = {"English 🇬🇧": 'en', "Русский 🇷🇺": 'ru'}
    text = update.message.text
    
    if text in lang_map:
        lang = lang_map[text]
        context.user_data['lang'] = lang
        
        # При смене языка сбрасываем промпт на дефолтный для нового языка
        context.user_data['current_prompt'] = DEFAULT_PROMPT[lang]
        
        await update.message.reply_text(
            LANGUAGES[lang]['lang_changed'],
            reply_markup=get_main_menu_keyboard(lang, context.user_data.get('has_article', False))
        )
    else:
        current_lang = context.user_data.get('lang', 'en')
        await update.message.reply_text(
            "Пожалуйста, выберите язык из предложенных" if current_lang == 'ru' else
            "Please select language from the options",
            reply_markup=get_lang_menu_keyboard()
        )
    
    return MAIN_MENU

def main():
    """Запуск бота"""
    TOKEN = os.getenv("TELEGRAM_TOKEN")
    if not TOKEN:
        logger.error("Токен Telegram не найден!")
        raise RuntimeError("Telegram token is missing")
    
    application = ApplicationBuilder().token(TOKEN).build()
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            MAIN_MENU: [MessageHandler(filters.TEXT & ~filters.COMMAND, main_menu)],
            ASK_QUESTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_question)],
            ENTER_LINK: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link)],
            CHANGE_LANG: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_language)],
            PROMPT_MENU: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_prompt_menu)],
            ENTER_CUSTOM_PROMPT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_custom_prompt)]
        },
        fallbacks=[CommandHandler('start', start)]
    )
    
    application.add_handler(conv_handler)
    application.run_polling()

if __name__ == '__main__':
    main()