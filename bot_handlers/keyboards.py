from config import ENABLE_PROFILE_RESET_BUTTON
from vk_api.keyboard import VkKeyboard, VkKeyboardColor

from . import texts

EMPTY_KEYBOARD = VkKeyboard.get_empty_keyboard()


# Создает стартовую клавиатуру с одной кнопкой запуска.
def get_start_keyboard():
    keyboard = VkKeyboard(one_time=True, inline=False)
    keyboard.add_button(texts.BUTTON_START, color=VkKeyboardColor.POSITIVE)
    return keyboard.get_keyboard()


# Создает клавиатуру выбора пола для регистрации.
def get_gender_keyboard():
    keyboard = VkKeyboard(one_time=False, inline=False)
    keyboard.add_button(texts.BUTTON_GENDER_MALE, color=VkKeyboardColor.PRIMARY)
    keyboard.add_button(texts.BUTTON_GENDER_FEMALE, color=VkKeyboardColor.PRIMARY)
    return keyboard.get_keyboard()


# Создает клавиатуру выбора предпочтений для регистрации и редактирования.
def get_looking_keyboard():
    keyboard = VkKeyboard(one_time=True, inline=False)
    keyboard.add_button(texts.BUTTON_LOOKING_MALE, color=VkKeyboardColor.PRIMARY)
    keyboard.add_button(texts.BUTTON_LOOKING_FEMALE, color=VkKeyboardColor.PRIMARY)
    keyboard.add_button(texts.BUTTON_LOOKING_ANY, color=VkKeyboardColor.PRIMARY)
    return keyboard.get_keyboard()


# Создает клавиатуру, которая показывается, когда пользователь может добавить еще фото.
def get_photo_more_keyboard():
    keyboard = VkKeyboard(one_time=False, inline=False)
    keyboard.add_button(texts.BUTTON_PHOTO_DONE, color=VkKeyboardColor.POSITIVE)
    return keyboard.get_keyboard()


# Создает клавиатуру для сохранения текущих фото при редактировании.
def get_photo_edit_keyboard():
    keyboard = VkKeyboard(one_time=False, inline=False)
    keyboard.add_button(texts.BUTTON_KEEP_CURRENT, color=VkKeyboardColor.SECONDARY)
    return keyboard.get_keyboard()


# Создает основную клавиатуру обзора для заполненной анкеты.
def get_review_keyboard():
    keyboard = VkKeyboard(one_time=False, inline=False)
    keyboard.add_button(texts.BUTTON_REVIEW_BROWSE, color=VkKeyboardColor.POSITIVE)
    keyboard.add_line()
    keyboard.add_button(texts.BUTTON_EDIT_PROFILE, color=VkKeyboardColor.PRIMARY)
    keyboard.add_button(texts.BUTTON_EDIT_ABOUT, color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_button(texts.BUTTON_EDIT_GAMES, color=VkKeyboardColor.PRIMARY)
    keyboard.add_button(texts.BUTTON_EDIT_PHOTO, color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    if ENABLE_PROFILE_RESET_BUTTON:
        keyboard.add_button(texts.BUTTON_RESET, color=VkKeyboardColor.NEGATIVE)
    keyboard.add_button(texts.BUTTON_DEACTIVATE_PROFILE, color=VkKeyboardColor.SECONDARY)
    return keyboard.get_keyboard()


# Создает меню-клавиатуру для редактирования основных полей анкеты.
def get_edit_profile_keyboard():
    keyboard = VkKeyboard(one_time=False, inline=False)
    keyboard.add_button(texts.BUTTON_EDIT_NAME, color=VkKeyboardColor.PRIMARY)
    keyboard.add_button(texts.BUTTON_EDIT_AGE, color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_button(texts.BUTTON_EDIT_GENDER, color=VkKeyboardColor.PRIMARY)
    keyboard.add_button(texts.BUTTON_EDIT_LOOKING, color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_button(texts.BUTTON_EDIT_CITY, color=VkKeyboardColor.PRIMARY)
    keyboard.add_button(texts.BUTTON_BACK, color=VkKeyboardColor.SECONDARY)
    return keyboard.get_keyboard()


# Создает клавиатуру редактирования имени с быстрым выбором имени из VK, если оно доступно.
def get_name_edit_keyboard(vk_name):
    keyboard = VkKeyboard(one_time=False, inline=False)
    if vk_name:
        keyboard.add_button(vk_name, color=VkKeyboardColor.PRIMARY)
    else:
        keyboard.add_button(texts.BUTTON_KEEP_CURRENT, color=VkKeyboardColor.SECONDARY)
    return keyboard.get_keyboard()


# Создает клавиатуру редактирования возраста с быстрым выбором текущего возраста.
def get_age_edit_keyboard(current_age):
    keyboard = VkKeyboard(one_time=False, inline=False)
    if current_age:
        keyboard.add_button(str(current_age), color=VkKeyboardColor.PRIMARY)
    else:
        keyboard.add_button(texts.BUTTON_KEEP_CURRENT, color=VkKeyboardColor.SECONDARY)
    return keyboard.get_keyboard()


# Создает клавиатуру регистрации возраста с подсказкой возраста из VK, если он доступен.
def get_age_registration_keyboard(vk_age):
    keyboard = VkKeyboard(one_time=False, inline=False)
    if vk_age:
        keyboard.add_button(str(vk_age), color=VkKeyboardColor.PRIMARY)
        return keyboard.get_keyboard()
    return EMPTY_KEYBOARD


# Создает клавиатуру редактирования пола.
def get_gender_edit_keyboard(vk_gender):
    keyboard = VkKeyboard(one_time=False, inline=False)
    keyboard.add_button(texts.BUTTON_GENDER_MALE, color=VkKeyboardColor.PRIMARY)
    keyboard.add_button(texts.BUTTON_GENDER_FEMALE, color=VkKeyboardColor.PRIMARY)
    return keyboard.get_keyboard()


# Создает клавиатуру редактирования города с быстрым выбором города из VK, если он доступен.
def get_city_edit_keyboard(vk_city):
    keyboard = VkKeyboard(one_time=False, inline=False)
    if vk_city:
        keyboard.add_button(vk_city, color=VkKeyboardColor.PRIMARY)
    else:
        keyboard.add_button(texts.BUTTON_KEEP_CURRENT, color=VkKeyboardColor.SECONDARY)
    return keyboard.get_keyboard()


# Создает inline callback-клавиатуру для выбора игр.
def get_games_keyboard(user):
    keyboard = VkKeyboard(one_time=False, inline=True)
    keyboard.add_callback_button(
        f"{texts.EMOJI_CHECK if user.get('dota2') else texts.EMOJI_CROSS} Dota 2",
        color=VkKeyboardColor.PRIMARY,
        payload={"cmd": "toggle_game", "field": "dota2"},
    )
    keyboard.add_callback_button(
        f"{texts.EMOJI_CHECK if user.get('cs2') else texts.EMOJI_CROSS} CS2",
        color=VkKeyboardColor.PRIMARY,
        payload={"cmd": "toggle_game", "field": "cs2"},
    )
    keyboard.add_callback_button(
        f"{texts.EMOJI_CHECK if user.get('minecraft') else texts.EMOJI_CROSS} Minecraft",
        color=VkKeyboardColor.PRIMARY,
        payload={"cmd": "toggle_game", "field": "minecraft"},
    )
    keyboard.add_line()
    keyboard.add_callback_button(
        f"{texts.EMOJI_CHECK if user.get('mlbb') else texts.EMOJI_CROSS} MLBB",
        color=VkKeyboardColor.PRIMARY,
        payload={"cmd": "toggle_game", "field": "mlbb"},
    )
    keyboard.add_callback_button(
        f"{texts.EMOJI_CHECK if user.get('valorant') else texts.EMOJI_CROSS} Valorant",
        color=VkKeyboardColor.PRIMARY,
        payload={"cmd": "toggle_game", "field": "valorant"},
    )
    keyboard.add_callback_button(
        f"{texts.EMOJI_CHECK if user.get('pubg') else texts.EMOJI_CROSS} PUBG",
        color=VkKeyboardColor.PRIMARY,
        payload={"cmd": "toggle_game", "field": "pubg"},
    )
    keyboard.add_line()
    keyboard.add_callback_button(
        f"{texts.EMOJI_CHECK if user.get('dbd') else texts.EMOJI_CROSS} Dead by Daylight",
        color=VkKeyboardColor.PRIMARY,
        payload={"cmd": "toggle_game", "field": "dbd"},
    )
    keyboard.add_callback_button(
        f"{texts.EMOJI_CHECK if user.get('genshin') else texts.EMOJI_CROSS} Genshin Impact",
        color=VkKeyboardColor.PRIMARY,
        payload={"cmd": "toggle_game", "field": "genshin"},
    )
    keyboard.add_callback_button(
        texts.BUTTON_GAMES_DONE,
        color=VkKeyboardColor.POSITIVE,
        payload={"cmd": "games_done"},
    )
    return keyboard.get_keyboard()


# Создает клавиатуру с универсальной кнопкой «оставить как есть».
def get_keep_current_keyboard():
    keyboard = VkKeyboard(one_time=False, inline=False)
    keyboard.add_button(texts.BUTTON_KEEP_CURRENT, color=VkKeyboardColor.SECONDARY)
    return keyboard.get_keyboard()


# Создает клавиатуру для просмотра новых анкет или истории.
def get_browse_keyboard(viewing_history=False, history_action=None):
    keyboard = VkKeyboard(one_time=False, inline=False)
    if not viewing_history or history_action == "dislike":
        keyboard.add_button(texts.EMOJI_LIKE, color=VkKeyboardColor.POSITIVE)
        keyboard.add_button(texts.EMOJI_MESSAGE, color=VkKeyboardColor.PRIMARY)
        keyboard.add_button(texts.EMOJI_DISLIKE, color=VkKeyboardColor.NEGATIVE)
        keyboard.add_line()
    if viewing_history:
        keyboard.add_button(texts.BUTTON_BACK_TO_NEW, color=VkKeyboardColor.PRIMARY)
        keyboard.add_line()
    keyboard.add_button(texts.BUTTON_BACK_TO_PREVIOUS, color=VkKeyboardColor.SECONDARY)
    keyboard.add_line()
    keyboard.add_button(texts.BUTTON_MY_PROFILE, color=VkKeyboardColor.SECONDARY)
    keyboard.add_button(texts.BUTTON_REPORT, color=VkKeyboardColor.SECONDARY)
    return keyboard.get_keyboard()


# Создает запасную клавиатуру для случая, когда нет анкет для показа.
def get_no_profiles_keyboard():
    keyboard = VkKeyboard(one_time=False, inline=False)
    keyboard.add_button(texts.BUTTON_BACK_TO_PREVIOUS, color=VkKeyboardColor.SECONDARY)
    keyboard.add_line()
    keyboard.add_button(texts.BUTTON_MY_PROFILE, color=VkKeyboardColor.PRIMARY)
    keyboard.add_button(texts.BUTTON_BROWSE, color=VkKeyboardColor.PRIMARY)
    return keyboard.get_keyboard()


# Создает клавиатуру ответа на входящий лайк.
def get_incoming_like_keyboard():
    keyboard = VkKeyboard(one_time=False, inline=False)
    keyboard.add_button(texts.EMOJI_LIKE, color=VkKeyboardColor.POSITIVE)
    keyboard.add_button(texts.EMOJI_MESSAGE, color=VkKeyboardColor.PRIMARY)
    keyboard.add_button(texts.EMOJI_DISLIKE, color=VkKeyboardColor.NEGATIVE)
    keyboard.add_line()
    keyboard.add_button(texts.BUTTON_REPORT, color=VkKeyboardColor.SECONDARY)
    return keyboard.get_keyboard()


# Создает клавиатуру, используемую во время ввода причины жалобы.
def get_report_cancel_keyboard():
    keyboard = VkKeyboard(one_time=False, inline=False)
    keyboard.add_button(texts.BUTTON_CANCEL_REPORT, color=VkKeyboardColor.SECONDARY)
    return keyboard.get_keyboard()


# Создает клавиатуру для сценария «лайк с сообщением».
def get_like_message_keyboard():
    keyboard = VkKeyboard(one_time=False, inline=False)
    keyboard.add_button(texts.BUTTON_BACK_FROM_MESSAGE, color=VkKeyboardColor.SECONDARY)
    return keyboard.get_keyboard()


# Создает простую клавиатуру, которая показывается после мэтчей и завершенных действий.
def get_matches_keyboard():
    keyboard = VkKeyboard(one_time=False, inline=False)
    keyboard.add_button(texts.BUTTON_MY_PROFILE, color=VkKeyboardColor.PRIMARY)
    keyboard.add_button(texts.BUTTON_BROWSE, color=VkKeyboardColor.PRIMARY)
    return keyboard.get_keyboard()


# Создает клавиатуру подтверждения отключения анкеты.
def get_deactivate_confirm_keyboard():
    keyboard = VkKeyboard(one_time=False, inline=False)
    keyboard.add_button(texts.BUTTON_DEACTIVATE, color=VkKeyboardColor.NEGATIVE)
    keyboard.add_button(texts.BUTTON_BACK, color=VkKeyboardColor.SECONDARY)
    return keyboard.get_keyboard()


# Создает клавиатуру подтверждения полного сброса анкеты.
def get_reset_confirm_keyboard():
    keyboard = VkKeyboard(one_time=False, inline=False)
    keyboard.add_button(texts.BUTTON_RESET, color=VkKeyboardColor.NEGATIVE)
    keyboard.add_button(texts.BUTTON_BACK, color=VkKeyboardColor.SECONDARY)
    return keyboard.get_keyboard()
