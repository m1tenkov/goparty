# `user_sessions.session_json`

## Зачем это нужно

Бот работает как stateful-сценарий. Пользователь может:

- проходить регистрацию;
- редактировать анкету;
- настраивать фильтры;
- смотреть новые анкеты;
- возвращаться к истории;
- обрабатывать входящие лайки;
- писать сообщение к лайку;
- отправлять жалобу.

Чтобы после следующего сообщения или после перезапуска приложения не терять контекст, часть runtime-состояния сохраняется в таблицу `user_sessions`.

## Что хранится в `session_json`

Поле содержит не анкету целиком, а только временный контекст сценария.

Сейчас в него пишутся:

- `step`
- `current_candidate`
- `games_step_completed`
- `browse_mode`
- `history_candidate_action`
- `history_cursor_id`
- `history_cursor_created_at`
- `pending_like_profile`
- `like_message_target_vk_user_id`
- `like_message_resume_step`
- `report_target_vk_user_id`
- `report_resume_step`
- `had_photos_before_edit`
- `resume_step`
- `suppress_post_match_prompt`

## Что это значит на практике

- `step` показывает текущий экран или шаг диалога.
- `current_candidate` хранит `vk_user_id` анкеты, которую пользователь сейчас смотрит.
- `browse_mode` отличает новые анкеты от режима истории.
- `history_*` поля позволяют листать историю просмотров.
- `pending_like_profile` и `resume_step` нужны для возврата из сценария входящего лайка.
- `like_message_*` используются для лайка с сообщением.
- `report_*` используются для сценария жалобы.
- `had_photos_before_edit` помогает корректно вести редактирование фотографий.
- `suppress_post_match_prompt` используется как служебный флаг после отдельных сценариев мэтча.

## Чего там нет

В `session_json` не хранятся постоянные данные анкеты:

- имя;
- возраст;
- город;
- пол;
- `looking_for`;
- признак использования микрофона `uses_microphone`;
- описание;
- игры;
- фотографии;
- история лайков и мэтчей;
- фильтры поиска.

Эти данные живут в нормализованных таблицах:

- `profiles`
- `user_games`
- `user_photos`
- `interactions`
- `matches`
- `pending_likes`
- `user_filters`
- `user_filter_games`

## Пример содержимого

```json
{
  "step": "STATE_BROWSE",
  "current_candidate": 123456789,
  "games_step_completed": true,
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

## Итог

`user_sessions.session_json` - это слой восстановления контекста. Он нужен, чтобы бот:

- не забывал текущий шаг пользователя;
- корректно возвращался из промежуточных сценариев;
- продолжал работу после перезапуска;
- не смешивал временное runtime-состояние с постоянными данными анкеты.
