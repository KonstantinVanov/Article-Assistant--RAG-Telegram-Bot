import os
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, 
    filters, ConversationHandler
)
from bot_handlers import (
    start, main_menu, handle_question, handle_link, 
    handle_language, handle_prompt_menu, handle_custom_prompt, handle_summarize
)
from bot_config import (
    MAIN_MENU, ENTER_LINK, CHANGE_LANG, 
    ASK_QUESTION, PROMPT_MENU, ENTER_CUSTOM_PROMPT, SUMMARIZE_DOC, logger
)

def main():
    from bot_config import init_db
    from bot_utils import cleanup_temp_files
    
    init_db()
    logger.info("Database initialized")
    
    cleanup_temp_files()
    logger.info("Temp files cleaned up")
    
    TOKEN = os.getenv("TELEGRAM_TOKEN")
    if not TOKEN:
        logger.error("Telegram token not found!")
        raise RuntimeError("Telegram token is missing")
    
    application = ApplicationBuilder().token(TOKEN).build()
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            MAIN_MENU: [MessageHandler(filters.TEXT & ~filters.COMMAND, main_menu)],
            ASK_QUESTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_question)],
            ENTER_LINK: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link),
                MessageHandler(filters.Document.ALL, handle_link)
            ],
            CHANGE_LANG: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_language)],
            PROMPT_MENU: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_prompt_menu)],
            ENTER_CUSTOM_PROMPT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_custom_prompt)],
            SUMMARIZE_DOC: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_summarize)]
        },
        fallbacks=[CommandHandler('start', start)],
        allow_reentry=True
    )
    
    application.add_handler(conv_handler)
    
    logger.info("Starting bot...")
    application.run_polling()

if __name__ == '__main__':
    main()