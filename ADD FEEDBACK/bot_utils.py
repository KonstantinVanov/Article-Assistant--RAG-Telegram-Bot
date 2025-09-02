def get_feedback_keyboard(lang: str):
    return ReplyKeyboardMarkup([
        [KeyboardButton(FEEDBACK_BUTTONS[lang]['like_btn']), 
         KeyboardButton(FEEDBACK_BUTTONS[lang]['dislike_btn'])],
        [KeyboardButton(LANGUAGES[lang]['cancel'])]
    ], resize_keyboard=True)