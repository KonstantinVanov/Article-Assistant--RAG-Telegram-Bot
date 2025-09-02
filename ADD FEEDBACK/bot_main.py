from bot_config import FEEDBACK

FEEDBACK: [
    MessageHandler(filters.TEXT & ~filters.COMMAND, handle_feedback)
],