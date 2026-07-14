# iphotos-cleanup

Находит в библиотеке macOS «Фото» снимки, импортированные «мусорными» приложениями
(каршеринг, самокаты и т.п.), и собирает их в альбом для ручной проверки и удаления.

Приложение-источник хранится в `Photos.sqlite` в поле
`ZADDITIONALASSETATTRIBUTES.ZIMPORTEDBYBUNDLEIDENTIFIER`. Скрипт работает
**только с копией** базы — оригинальная библиотека не изменяется (кроме
создания альбома через AppleScript при `--make-album`).

## Использование

```bash
# посмотреть все приложения-источники с количеством фото
python3 cleanup.py --library "/Volumes/Photo/Photos Library.photoslibrary" --list-apps

# отчёт (dry-run): сколько фото и за какие месяцы
python3 cleanup.py --library "/Volumes/Photo/Photos Library.photoslibrary" \
  --bundle-id today.youdrive.rent --bundle-id whoosh.bike --bundle-id my.Carharing

# собрать найденное в альбом для проверки
python3 cleanup.py --library "..." --bundle-id today.youdrive.rent --make-album
```

Дальше вручную: открыть альбом в Photos → ⌘A → ⌘⌫. Снимки уходят в
«Недавно удалённые» и хранятся там 30 дней — откат возможен.

## Почему удаление ручное

AppleScript-словарь Photos не умеет удалять медиафайлы — это ограничение Apple.
Автоматизация возможна через PhotoKit (pyobjc), но осознанно не сделана:
ручной шаг даёт финальный контроль перед удалением.

## Известные bundle ID

| Bundle ID | Приложение |
|---|---|
| `today.youdrive.rent` | СитиДрайв (бывш. YouDrive) |
| `whoosh.bike` | Whoosh (самокаты) |
| `my.Carharing` | Делимобиль |

Требования: macOS, Python 3.9+ (только stdlib). Photos должен быть открыт
с той же библиотекой, что передана в `--library` (скрипт проверяет это
пробой на одном снимке перед полным прогоном).
