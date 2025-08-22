from telegram import ReplyKeyboardMarkup, KeyboardButton
from bot_config import LANGUAGES
import os
import glob
from datetime import datetime, timedelta
import logger

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

def cleanup_temp_files(max_age_hours=1):
    """Удаляет временные файлы старше указанного времени"""
    try:
        current_time = datetime.now()
        for file_path in glob.glob("temp_*.*"):
            file_time = datetime.fromtimestamp(os.path.getctime(file_path))
            if current_time - file_time > timedelta(hours=max_age_hours):
                os.remove(file_path)
                logger.info(f"Removed temp file: {file_path}")
    except Exception as e:
        logger.error(f"Cleanup error: {str(e)}")