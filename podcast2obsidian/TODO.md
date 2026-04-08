# TODO

## Yandex Music: геоблокировка на сервере

**Проблема:** Yandex Music отдаёт HTTP 451 (Unavailable For Legal Reasons) при обращении с сервера за пределами РФ. Cookies авторизации не помогают — блокировка по IP.

**Варианты решения:**
1. Добавить поддержку прокси в конфиг (`proxy = socks5://...`) и передавать в yt-dlp через `opts["proxy"]`
2. VPN на сервере (WireGuard/AmneziaWG до РФ-точки)
3. Двухэтапная схема: бот принимает URL → скачивание через прокси/локально → транскрипция на сервере

**Затронутые файлы:**
- `podcast2obsidian/bot/worker.py` — передать proxy в download/fetch_subtitles
- `podcast2obsidian/downloader.py` — добавить proxy параметр в yt-dlp opts
- `podcast2obsidian/config.py` — добавить `proxy` в DEFAULT_CONFIG и _ENV_MAP

**Статус:** на паузе, ждёт решения по прокси/VPN
