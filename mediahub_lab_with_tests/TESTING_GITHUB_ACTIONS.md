# Автоматизированное тестирование MediaHub Lab в GitHub Actions

## Что добавлено

В проект добавлены:

- `tests/conftest.py` — общие фикстуры для тестов;
- `tests/test_app_routes.py` — функциональные тесты Flask-маршрутов;
- `tests/test_ui_selenium.py` — UI-тесты через Selenium и Chrome;
- `pytest.ini` — настройки pytest;
- `requirements-dev.txt` — зависимости для тестирования;
- `.github/workflows/python-tests.yml` — workflow для GitHub Actions.

## Какие проверки выполняются

Тесты проверяют:

1. открытие главной страницы;
2. регистрацию пользователя;
3. невозможность повторной регистрации одного логина;
4. вход с корректным логином и паролем;
5. сообщение об ошибке при неправильном входе;
6. запрет создания поста без авторизации;
7. создание текстового поста;
8. загрузку изображения с разрешённым расширением;
9. запрет загрузки файла с запрещённым расширением;
10. удаление своего поста;
11. запрет удаления чужого поста;
12. обработку удаления несуществующего поста;
13. работу `/api/slow`;
14. базовые UI-сценарии через Selenium.

## Как запустить тесты локально

```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
pytest -q
```

Только функциональные тесты без Selenium:

```bash
pytest -q tests/test_app_routes.py
```

Только UI-тесты Selenium:

```bash
pytest -q -m ui
```

## Как запустить в GitHub Actions

1. Загрузите проект в GitHub-репозиторий.
2. Убедитесь, что файл находится по пути:

```text
.github/workflows/python-tests.yml
```

3. Выполните `git add .`, `git commit` и `git push`.
4. Откройте вкладку **Actions** в GitHub.
5. Выберите workflow **MediaHub automated tests**.
6. Проверьте результат запуска.

## Важный момент

Тесты используют временную базу данных и временную папку `uploads`. Поэтому они не портят настоящую базу проекта `instance/mediahub.sqlite3`.
