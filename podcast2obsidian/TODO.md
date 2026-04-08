# TODO

## YouTube: серверный IP заблокирован как бот

**Проблема:** YouTube отвечает "Sign in to confirm you're not a bot" с серверных/VPS IP-адресов. Cookies с мака не помогают — YouTube видит несоответствие IP. OAuth2 больше не поддерживается в yt-dlp.

**Что пробовали:**
- Cookies с мака → не работает (IP mismatch)
- `yt-dlp --username oauth2` → deprecated, yt-dlp убрал поддержку
- Добавили deno (JS runtime) в Docker → не помогло
- Без cookies → тот же результат

**Варианты решения:**
1. **Домашний сервер с резидентным IP** — самый надёжный вариант (планируется)
2. Резидентный прокси (`proxy = socks5://...` в конфиге → yt-dlp `opts["proxy"]`)
3. VPN с резидентным IP на сервере

**Статус:** на паузе, планируется перенос бота на домашний сервер

---

## Yandex Music: геоблокировка на сервере

**Проблема:** Yandex Music отдаёт HTTP 451 (Unavailable For Legal Reasons) при обращении с сервера за пределами РФ. Cookies авторизации не помогают — блокировка по IP.

**Варианты решения:**
1. Домашний сервер в РФ (планируется)
2. Добавить поддержку прокси в конфиг и передавать в yt-dlp
3. VPN на сервере (WireGuard/AmneziaWG до РФ-точки)
4. Патч yt-dlp для Yandex Music (protocol-relative URL → https, уже применён локально)

**Затронутые файлы:**
- `podcast2obsidian/bot/worker.py` — передать proxy в download/fetch_subtitles
- `podcast2obsidian/downloader.py` — добавить proxy параметр в yt-dlp opts
- `podcast2obsidian/config.py` — добавить `proxy` в DEFAULT_CONFIG и _ENV_MAP

**Статус:** на паузе, планируется перенос бота на домашний сервер

---

## Прокси-поддержка (когда понадобится)

Добавить `PROXY` в .env → `config.py` → передавать в yt-dlp:
```python
# downloader.py
if proxy:
    opts["proxy"] = proxy
```

---

## Мелкие улучшения

- [ ] yt-dlp патч для Yandex Music (protocol-relative URL) — применён локально в venv, нужно автоматизировать или ждать мерж в upstream (yt-dlp/yt-dlp#15087)
- [ ] Кэш whisper-моделей: при первом запуске Docker контейнера модель скачивается заново (~3GB). Можно пре-загрузить в образ или использовать persistent volume
- [ ] Eviction для аудио-кэша (`~/.cache/podcast2obsidian/`) — сейчас файлы копятся бесконечно
