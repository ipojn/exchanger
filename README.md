# exchanger

Сервис обмена файлами по коротким ссылкам. Загрузил — получил код из 6 символов — скинул ссылку — через 7 дней файл исчезает.

## Возможности

- Загрузка файла до 100 МБ (стриминг, без загрузки в память)
- Короткий код (6 символов, base62, криптостойкий `secrets`)
- Срок жизни ссылки — 7 дней
- Коды хранятся как SHA-256-хэши (утечка БД не даёт доступа)
- Защита от path traversal (внутренние имена — UUID)
- Атомарная запись через `*.part` + `os.replace`
- Веб-интерфейс (drag&drop + страница скачивания)

## Стек

FastAPI · Jinja2 · SQLAlchemy (в процессе) · SQLite → PostgreSQL

## Запуск

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Открой http://localhost:8000

## API

| Метод | Путь | Описание |
|---|---|---|
| POST | `/upload` | Загрузить файл (multipart) → `{code, url, expires_at}` |
| GET  | `/s/{code}` | HTML-страница скачивания |
| GET  | `/s/{code}/info` | JSON-метаданные |
| GET  | `/s/{code}/download` | Файл (attachment) |

## Roadmap

- [x] Загрузка/скачивание, короткие коды, TTL
- [x] Веб-интерфейс
- [ ] SQLite + SQLAlchemy + Alembic
- [ ] Rate limit на `/s/{code}`
- [ ] `max_downloads` (одноразовые ссылки)
- [ ] Docker + docker-compose
- [ ] Тесты (pytest + httpx)