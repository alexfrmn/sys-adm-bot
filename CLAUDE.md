# sys-adm-bot — Claude Code Context

## Проект

Telegram бот для управления каналом @sys_adm — личный блог Alex о:
- IT и выгорании
- AI-автоматизации
- DJ/музыке
- Осознанности и терапии

## Архитектура

```
sys-adm-bot/
├── bot.py           # Основной бот (aiogram 3.x)
├── poster.py        # Автопостинг по расписанию
├── add_post.py      # CLI для добавления постов
├── config.py        # Конфигурация
├── queue.json       # Очередь постов
├── images/          # Картинки для постов
├── posted/          # Архив опубликованных
└── rules/           # Правила контента
    ├── ai-terms-ru.md
    ├── writing-guide.md
    └── deaify-text.md (→ vault skill)
```

## Команды бота

| Команда | Описание |
|---------|----------|
| /start, /help | Меню команд |
| /queue | Очередь постов |
| /prompts | Промпты для картинок |
| /check | Проверка текста на AI-артефакты |
| Фото | Привязка к посту (inline buttons) |

## Формат поста в очереди

```json
{
  "id": 1,
  "scheduled": "2026-02-06T18:00:00+03:00",
  "text": "Текст поста...",
  "image_url": "/opt/lifecoach/sys-adm-bot/images/post_1.jpg",
  "status": "pending",
  "created_at": "2026-02-04T21:45:35+03:00"
}
```

## Pipeline создания постов

```
Questions → Research → Write → Deaify → Publish
```

1. **Questions** — тема, угол, аудитория
2. **Research** — 3-5 источников (опционально)
3. **Write** — черновик по writing-guide.md
4. **Deaify** — 4 критика для удаления AI smell
5. **Publish** — add_post.py → queue.json

## Стиль канала

- Разговорный тон
- Мат — ок
- Личные истории
- Конкретные числа и даты
- Структура: Pain → Insight

## Rules

- `rules/writing-guide.md` — структура и стиль постов
- `rules/ai-terms-ru.md` — терминология
- `.claude/skills/deaify-text/SKILL.md` — удаление AI-артефактов

## Технические детали

- **Python 3.12**
- **aiogram 3.x**
- **Timezone:** Europe/Moscow
- **Posting time:** 18:00 MSK
- **Admin ID:** 219787633

## Systemd

```bash
systemctl status sys-adm-bot
systemctl restart sys-adm-bot
journalctl -u sys-adm-bot -f
```
