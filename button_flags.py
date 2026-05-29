BUTTONS_FOR_EVERYONE = 1
BUTTONS_FOR_ADMINS = 2
BUTTONS_FOR_NOBODY = 3

# 1 - show and enable both buttons for every user.
# 2 - show and enable both buttons only for ADMIN_VK_IDS.
# 3 - hide and disable both buttons for every user.
RESET_HISTORY_BUTTON_MODE = BUTTONS_FOR_EVERYONE

ADMIN_VK_IDS = {
    542646585,
    186649696,
}


def _normalize_vk_user_id(vk_user_id):
    try:
        return int(vk_user_id)
    except (TypeError, ValueError):
        return None


def can_use_reset_history_buttons(vk_user_id):
    if RESET_HISTORY_BUTTON_MODE == BUTTONS_FOR_EVERYONE:
        return True
    if RESET_HISTORY_BUTTON_MODE == BUTTONS_FOR_ADMINS:
        return _normalize_vk_user_id(vk_user_id) in ADMIN_VK_IDS
    return False


def can_reset_profile(vk_user_id):
    return can_use_reset_history_buttons(vk_user_id)


def can_clear_history(vk_user_id):
    return can_use_reset_history_buttons(vk_user_id)
