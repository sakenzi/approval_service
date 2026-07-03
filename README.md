# approval-service

## Запуск

1. Создайте и активируйте виртуальное окружение:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Linux/macOS
   .\.venv\Scripts\activate  # Windows
   ```
2. Установите зависимости:
   ```bash
   pip install -r requirements.txt
   pip install pytest pytest-asyncio httpx aiosqlite
   ```
3. Запустите приложение:
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   или
   run.py
   ```

## Auth stub

Для локального запуска сервис принимает заглушку авторизации через заголовки:
- `X-Workspace-Id`
- `X-User-Id`
- `X-User-Actions`

Пример:
```http
X-Workspace-Id: ws-1
X-User-Id: usr_1
X-User-Actions: approval:create,approval:read,approval:decide
```

## Тесты

```bash
pytest -q
```
