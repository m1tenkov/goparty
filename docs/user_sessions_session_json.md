# `user_sessions.session_json`

Таблица `user_sessions` хранит runtime-состояние диалога пользователя с ботом. Это не основной источник анкетных данных, а техническое состояние сценария.

Основные данные пользователя хранятся отдельно:

- анкета - `profiles`;
- игры - `user_games`;
- фотографии - `user_photos`;
- фильтры - `user_filters` и `user_filter_games`;
- действия - `interactions`.

## Пример структуры

```json
{
  "step": "STATE_BROWSE",
  "current_candidate": null,
  "browse_mode": "new",
  "history_candidate_action": null,
  "history_cursor_id": null,
  "history_cursor_created_at": null,
  "pending_like_profile": null,
  "like_message_target_vk_user_id": null,
  "like_message_resume_step": null,
  "report_target_vk_user_id": null,
  "report_resume_step": null,
  "had_photos_before_edit": false,
  "resume_step": null,
  "suppress_post_match_prompt": false
}
```

Поле `pending_like_profile` хранит временные данные анкеты входящего лайка только на уровне сценария. Сам факт лайка хранится в `interactions`, а не в отдельной таблице.
