from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, 
    filters, ContextTypes, ConversationHandler, CallbackQueryHandler
)
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from RAG_bot.config import (
    LANGUAGES, DEFAULT_PROMPT, MAIN_MENU, ENTER_LINK, CHANGE_LANG,
    ASK_QUESTION, PROMPT_MENU, ENTER_CUSTOM_PROMPT, SUMMARIZE_DOC,
    init_db, logger
)
from Requests import answer
from indexer import reindex
import os
import sqlite3
import logging

# Initialize logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Keyboard functions
def get_main_menu_keyboard(lang: str, has_article: bool = False):
    buttons = []
    if has_article:
        buttons.append([KeyboardButton(LANGUAGES[lang]['ask_btn'])])
        buttons.append([KeyboardButton(LANGUAGES[lang]['summarize_btn'])])
    buttons.extend([
        [KeyboardButton(LANGUAGES[lang]['article_btn'])],
        [KeyboardButton(LANGUAGES[lang]['lang_btn']), KeyboardButton(LANGUAGES[lang]['prompt_btn'])]
    ])
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)

def get_prompt_menu_keyboard(lang: str):
    return ReplyKeyboardMarkup([
        [KeyboardButton(LANGUAGES[lang]['default_prompt'])],
        [KeyboardButton(LANGUAGES[lang]['custom_prompt'])],
        [KeyboardButton(LANGUAGES[lang]['cancel'])]
    ], resize_keyboard=True)

def get_lang_menu_keyboard():
    return ReplyKeyboardMarkup([
        [KeyboardButton("English 🇬🇧"), KeyboardButton("Русский 🇷🇺")]
    ], resize_keyboard=True)

def get_cancel_keyboard(lang: str):
    return ReplyKeyboardMarkup([[KeyboardButton(LANGUAGES[lang]['cancel'])]], resize_keyboard=True)

# Handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['lang'] = 'en'
    context.user_data['has_article'] = False
    context.user_data['current_prompt'] = DEFAULT_PROMPT['en']
    lang = context.user_data['lang']
    
    await update.message.reply_text(
        text=LANGUAGES[lang]['welcome'],
        parse_mode="HTML",
        reply_markup=get_main_menu_keyboard(lang, has_article=False),
        disable_web_page_preview=True
    )
    return MAIN_MENU

async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get('lang', 'en')
    has_article = context.user_data.get('has_article', False)
    text = update.message.text
    
    valid_commands = [
        LANGUAGES[lang]['ask_btn'],
        LANGUAGES[lang]['article_btn'],
        LANGUAGES[lang]['lang_btn'],
        LANGUAGES[lang]['prompt_btn'],
        LANGUAGES[lang]['summarize_btn'],
        LANGUAGES[lang]['cancel']
    ]
    
    if text not in valid_commands:
        await update.message.reply_text(
            LANGUAGES[lang]['invalid_input'],
            reply_markup=get_main_menu_keyboard(lang, has_article)
        )
        return MAIN_MENU
    
    if text == LANGUAGES[lang]['ask_btn']:
        if not has_article:
            await update.message.reply_text(
                LANGUAGES[lang]['no_article_error'],
                reply_markup=get_main_menu_keyboard(lang, has_article)
            )
            return MAIN_MENU
        
        await update.message.reply_text(
            LANGUAGES[lang]['ask_prompt'],
            reply_markup=get_cancel_keyboard(lang)
        )
        return ASK_QUESTION
    
    if text == LANGUAGES[lang]['article_btn']:
        await update.message.reply_text(
            LANGUAGES[lang]['enter_url'],
            reply_markup=get_cancel_keyboard(lang)
        )
        return ENTER_LINK
    
    if text == LANGUAGES[lang]['lang_btn']:
        await update.message.reply_text(
            "Выберите язык:" if lang == 'ru' else "Select language:",
            reply_markup=get_lang_menu_keyboard()
        )
        return CHANGE_LANG
    
    if text == LANGUAGES[lang]['prompt_btn']:
        await update.message.reply_text(
            LANGUAGES[lang]['prompt_menu'],
            reply_markup=get_prompt_menu_keyboard(lang)
        )
        return PROMPT_MENU
    
    if text == LANGUAGES[lang]['summarize_btn']:
        if not has_article:
            await update.message.reply_text(
                LANGUAGES[lang]['no_article_error'],
                reply_markup=get_main_menu_keyboard(lang, has_article)
            )
            return MAIN_MENU
        return await handle_summarize(update, context)
    
    return MAIN_MENU

async def handle_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
        current_prompt = context.user_data.get('current_prompt', DEFAULT_PROMPT[lang])
        full_query = f"{current_prompt}\n\nQuestion: {text}"
        
        response = answer(full_query)
        
        # Отправляем ответ без кнопок feedback
        await update.message.reply_text(
            response,
            parse_mode="Markdown"
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
    lang = context.user_data.get('lang', 'en')
    
    # Обработка отмены
    if update.message.text == LANGUAGES[lang]['cancel']:
        await update.message.reply_text(
            "Отменено" if lang == 'ru' else "Canceled",
            reply_markup=get_main_menu_keyboard(lang, context.user_data.get('has_article', False))
        )
        return MAIN_MENU
    
    # Обработка текстовых ссылок
    if update.message.text:
        text = update.message.text
        if not text.startswith(('http://', 'https://')):
            await update.message.reply_text(
                "⚠️ Пожалуйста, введите корректный URL" if lang == 'ru' else "⚠️ Please enter a valid URL",
                reply_markup=get_cancel_keyboard(lang)
            )
            return ENTER_LINK
        
    # Обработка документов (PDF/TXT)
    elif update.message.document:
        file = await update.message.document.get_file()
        ext = update.message.document.file_name.split('.')[-1].lower()
        if ext not in ['pdf', 'txt']:
            await update.message.reply_text(
                "⚠️ Поддерживаются только PDF и TXT файлы" if lang == 'ru' else "⚠️ Only PDF and TXT files are supported",
                reply_markup=get_cancel_keyboard(lang)
            )
            return ENTER_LINK
        
        # Скачиваем файл
        file_path = f"temp_{update.update_id}.{ext}"
        await file.download_to_drive(file_path)
        text = file_path  # Используем путь к файлу для индексации
    
    try:
        await update.message.reply_text(LANGUAGES[lang]['indexing'])
        
        # Индексируем контент
        num_chunks = reindex(text)
        
        context.user_data['has_article'] = True
        
        await update.message.reply_text(LANGUAGES[lang]['index_success'])
        
        chunks_message = LANGUAGES[lang]['chunks_info'].format(num_chunks)
        await update.message.reply_text(
            chunks_message,
            reply_markup=get_main_menu_keyboard(lang, has_article=True)
        )
        
    except Exception as e:
        error_msg = f"❌ Ошибка: {str(e)}" if lang == 'ru' else f"❌ Error: {str(e)}"
        await update.message.reply_text(
            error_msg,
            reply_markup=get_main_menu_keyboard(lang, False)
        )
    finally:
        # Удаляем временный файл, если был загружен
        if update.message.document and os.path.exists(text):
            os.remove(text)
    
    return MAIN_MENU

async def handle_summarize(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get('lang', 'en')
    
    if not context.user_data.get('has_article', False):
        await update.message.reply_text(LANGUAGES[lang]['no_article_error'])
        return MAIN_MENU
    
    await update.message.reply_text(LANGUAGES[lang]['summarizing'])
    
    try:
        embeddings = OpenAIEmbeddings(
            model="text-embedding-3-small",
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url="https://api.proxyapi.ru/openai/v1"
        )
        
        vector_store = FAISS.load_local(
            folder_path="./faiss_index",
            embeddings=embeddings,
            allow_dangerous_deserialization=True
        )

        docs = vector_store.similarity_search("Summarize key points", k=4)
        
        if not docs:
            await update.message.reply_text(LANGUAGES[lang]['no_content'])
            return MAIN_MENU
        
        summary_prompt = DEFAULT_PROMPT['summary_prompt'][lang].format(
            text="\n\n".join([doc.page_content[:500] for doc in docs])
        )
        
        response = answer(summary_prompt)
        
        await update.message.reply_text(
            f"{LANGUAGES[lang]['summary_title']}\n\n{response}",
            reply_markup=get_main_menu_keyboard(lang, has_article=True),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Summary error: {str(e)}")
        await update.message.reply_text(
            f"❌ {LANGUAGES[lang]['error']}: {str(e)}",
            reply_markup=get_main_menu_keyboard(lang, True)
        )
    
    return MAIN_MENU

async def handle_prompt_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get('lang', 'en')
    text = update.message.text
    
    if text == LANGUAGES[lang]['cancel']:
        await update.message.reply_text(
            "Отменено" if lang == 'ru' else "Canceled",
            reply_markup=get_main_menu_keyboard(lang, context.user_data.get('has_article', False))
        )
        return MAIN_MENU
    
    if text == LANGUAGES[lang]['default_prompt']:
        context.user_data['current_prompt'] = DEFAULT_PROMPT[lang]
        await update.message.reply_text(
            LANGUAGES[lang]['current_prompt'].format(DEFAULT_PROMPT[lang]),
            reply_markup=get_main_menu_keyboard(lang, context.user_data.get('has_article', False))
        )
        return MAIN_MENU
    
    if text == LANGUAGES[lang]['custom_prompt']:
        await update.message.reply_text(
            LANGUAGES[lang]['enter_custom_prompt'],
            reply_markup=get_cancel_keyboard(lang)
        )
        return ENTER_CUSTOM_PROMPT
    
    return PROMPT_MENU

async def handle_custom_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get('lang', 'en')
    text = update.message.text
    
    if text == LANGUAGES[lang]['cancel']:
        await update.message.reply_text(
            "Отменено" if lang == 'ru' else "Canceled",
            reply_markup=get_main_menu_keyboard(lang, context.user_data.get('has_article', False))
        )
        return MAIN_MENU
    
    context.user_data['current_prompt'] = text
    await update.message.reply_text(
        LANGUAGES[lang]['prompt_saved'],
        reply_markup=get_main_menu_keyboard(lang, context.user_data.get('has_article', False))
    )
    return MAIN_MENU

async def handle_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang_map = {"English 🇬🇧": 'en', "Русский 🇷🇺": 'ru'}
    text = update.message.text
    
    if text in lang_map:
        lang = lang_map[text]
        context.user_data['lang'] = lang
        context.user_data['current_prompt'] = DEFAULT_PROMPT[lang]
        
        await update.message.reply_text(
            LANGUAGES[lang]['lang_changed'],
            reply_markup=get_main_menu_keyboard(lang, context.user_data.get('has_article', False))
        )
    else:
        current_lang = context.user_data.get('lang', 'en')
        await update.message.reply_text(
            "Пожалуйста, выберите язык" if current_lang == 'ru' else "Please select language",
            reply_markup=get_lang_menu_keyboard()
        )
    
    return MAIN_MENU

def main():
    # Initialize database
    init_db()
    logger.info("Database initialized")
    
    TOKEN = os.getenv("TELEGRAM_TOKEN")
    if not TOKEN:
        logger.error("Telegram token not found!")
        raise RuntimeError("Telegram token is missing")
    
    application = ApplicationBuilder().token(TOKEN).build()
    
    # Setup conversation handler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            MAIN_MENU: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, main_menu),
            ],
            ASK_QUESTION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_question)
            ],
            ENTER_LINK: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link),
                MessageHandler(filters.Document.ALL, handle_link)
            ],
            CHANGE_LANG: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_language)
            ],
            PROMPT_MENU: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_prompt_menu)
            ],
            ENTER_CUSTOM_PROMPT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_custom_prompt)
            ],
            SUMMARIZE_DOC: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_summarize)
            ]
        },
        fallbacks=[CommandHandler('start', start)],
        allow_reentry=True
    )
    
    # Add handlers
    application.add_handler(conv_handler)
    
    # Start bot
    logger.info("Starting bot...")
    application.run_polling()

if __name__ == '__main__':
    main()