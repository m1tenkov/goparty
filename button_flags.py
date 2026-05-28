ADMIN_BUTTON_FLAGS = {
    542646585: {
        "profile_reset": True,
        "clear_history": True,
    },
    186649696: {
        "profile_reset": True,
        "clear_history": True,
    },
}


def _get_flags(vk_user_id):
    try:
        return ADMIN_BUTTON_FLAGS.get(int(vk_user_id), {})
    except (TypeError, ValueError):
        return {}


def can_reset_profile(vk_user_id):
    return bool(_get_flags(vk_user_id).get("profile_reset"))


def can_clear_history(vk_user_id):
    return bool(_get_flags(vk_user_id).get("clear_history"))
