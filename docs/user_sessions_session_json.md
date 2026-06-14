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

Фильтры поиска не записываются в `session_json`: они сохраняются отдельно в `user_filters` и `user_filter_games`. В `session_json` остаются только данные, необходимые для восстановления текущего диалогового шага после перезапуска приложения.

Служебные поля используются так:

- `browse_mode` показывает, смотрит ли пользователь новые анкеты или историю;
- `history_candidate_action`, `history_cursor_id` и `history_cursor_created_at` нужны для перехода к предыдущим анкетам из `interactions`;
- `like_message_target_vk_user_id` и `like_message_resume_step` восстанавливают сценарий после лайка с сообщением;
- `report_target_vk_user_id` и `report_resume_step` восстанавливают сценарий после ввода причины жалобы;
- `had_photos_before_edit` позволяет при редактировании фото предложить оставить текущие фотографии;
- `resume_step` возвращает пользователя к предыдущему сценарию после обработки входящего лайка;
- `suppress_post_match_prompt` подавляет лишнюю подсказку после мэтча, возникшего при ответе на входящий лайк.
