from telegram import ReplyKeyboardMarkup, KeyboardButton
from bot_config import LANGUAGES

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