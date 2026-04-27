from . import texts


def format_profile_text(name, age, city, games_text, about, include_review=False):
    text = texts.TEMPLATE_PROFILE_TEXT.format(
        name=name,
        age=age,
        city=city,
        emoji_games=texts.EMOJI_GAMES,
        games_text=games_text,
        about=about,
    )
    if include_review:
        text += f"\n\n{texts.MSG_REVIEW_SUFFIX}"
    return text


def format_games_summary(games_text):
    return texts.TEMPLATE_GAMES_SUMMARY.format(
        prefix=texts.MSG_GAMES_SUMMARY_PREFIX,
        games_text=games_text,
    )


def format_like_notification(target_name, liker_profile_text, like_message=None):
    text = texts.TEMPLATE_LIKE_NOTIFICATION.format(
        target_name=target_name,
        emoji_smile=texts.EMOJI_SMILE,
        liker_profile_text=liker_profile_text,
    )
    message = (like_message or "").strip()
    if message:
        text += texts.TEMPLATE_OPTIONAL_MESSAGE.format(
            emoji_message=texts.EMOJI_MESSAGE,
            message=message,
        )
    return text


def format_match_message(profile_text, other_name, vk_link, like_message=None):
    text = texts.TEMPLATE_MATCH_MESSAGE.format(
        profile_text=profile_text,
        emoji_smile=texts.EMOJI_SMILE,
        other_name=other_name,
        vk_link=vk_link,
    )
    message = (like_message or "").strip()
    if message:
        text += texts.TEMPLATE_OPTIONAL_MESSAGE.format(
            emoji_message=texts.EMOJI_MESSAGE,
            message=message,
        )
    return text


def format_report_message(profile_text, reporter_name, reporter_link, reported_name, reported_link, reason_text):
    return texts.TEMPLATE_REPORT_MESSAGE.format(
        profile_text=profile_text,
        reporter_name=reporter_name,
        reporter_link=reporter_link,
        reported_name=reported_name,
        reported_link=reported_link,
        reason_text=reason_text,
    )


def format_done_message(name):
    return texts.TEMPLATE_DONE_MESSAGE.format(name=name)
