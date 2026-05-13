from __future__ import annotations

from io import BytesIO

import pytest

from conftest import count_rows, fetch_one, login, logout, register


def test_index_page_opens_and_shows_empty_feed(client):
    response = client.get("/")

    assert response.status_code == 200
    assert "MediaHub Lab" in response.text
    assert "Лента" in response.text
    assert "Пока пусто" in response.text


def test_register_creates_user_and_redirects_to_login(client, app_module):
    response = register(client, "student01", "1234")

    assert response.status_code == 200
    assert "Registered" in response.text
    assert "Вход" in response.text
    assert count_rows(app_module.DB_PATH, "users") == 1


def test_duplicate_registration_shows_user_exists(client, app_module):
    register(client, "student01", "1234")
    response = register(client, "student01", "1234")

    assert response.status_code == 200
    assert "User exists" in response.text
    assert count_rows(app_module.DB_PATH, "users") == 1


def test_user_can_login_after_registration(client):
    register(client, "student01", "1234")

    response = login(client, "student01", "1234")

    assert response.status_code == 200
    assert "student01" in response.text
    assert "Новый пост" in response.text
    assert "Выйти" in response.text


def test_wrong_login_shows_error_message(client):
    response = login(client, "unknown", "bad-password")

    assert response.status_code == 200
    assert "Wrong credentials" in response.text
    assert "Вход" in response.text


def test_anonymous_user_is_redirected_to_login_when_opening_new_post(client):
    response = client.get("/post/new", follow_redirects=True)

    assert response.status_code == 200
    assert "Вход" in response.text
    assert "Опубликовать" not in response.text


def test_logged_user_can_create_text_post(client, app_module):
    register(client, "student01", "1234")
    login(client, "student01", "1234")

    response = client.post(
        "/post/new",
        data={"text": "Автоматизированная тестовая публикация"},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert "Автоматизированная тестовая публикация" in response.text
    assert "student01" in response.text
    assert count_rows(app_module.DB_PATH, "posts") == 1


def test_logged_user_can_upload_image_with_allowed_extension(client, app_module):
    register(client, "student01", "1234")
    login(client, "student01", "1234")

    response = client.post(
        "/post/new",
        data={
            "text": "Пост с изображением",
            "media": (BytesIO(b"fake image content"), "picture.png"),
        },
        content_type="multipart/form-data",
        follow_redirects=True,
    )

    post = fetch_one(app_module.DB_PATH, "SELECT * FROM posts WHERE text = ?", ("Пост с изображением",))

    assert response.status_code == 200
    assert "Пост с изображением" in response.text
    assert post is not None
    assert post["media"].endswith("_picture.png")


def test_upload_with_forbidden_extension_is_rejected(client, app_module):
    register(client, "student01", "1234")
    login(client, "student01", "1234")

    response = client.post(
        "/post/new",
        data={
            "text": "Этот пост не должен быть создан",
            "media": (BytesIO(b"not an image"), "virus.exe"),
        },
        content_type="multipart/form-data",
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert "Unsupported format" in response.text
    assert count_rows(app_module.DB_PATH, "posts") == 0


def test_author_can_delete_own_post(client, app_module):
    register(client, "student01", "1234")
    login(client, "student01", "1234")
    client.post("/post/new", data={"text": "Пост для удаления"}, follow_redirects=True)

    post = fetch_one(app_module.DB_PATH, "SELECT * FROM posts WHERE text = ?", ("Пост для удаления",))
    response = client.post(f"/post/delete/{post['id']}", follow_redirects=True)

    assert response.status_code == 200
    assert "Post deleted" in response.text
    assert "Пост для удаления" not in response.text
    assert count_rows(app_module.DB_PATH, "posts") == 0


def test_user_cannot_delete_another_users_post(client, app_module):
    register(client, "author", "1234")
    login(client, "author", "1234")
    client.post("/post/new", data={"text": "Чужой пост"}, follow_redirects=True)
    post = fetch_one(app_module.DB_PATH, "SELECT * FROM posts WHERE text = ?", ("Чужой пост",))

    logout(client)
    register(client, "other", "1234")
    login(client, "other", "1234")

    response = client.post(f"/post/delete/{post['id']}", follow_redirects=True)

    assert response.status_code == 200
    assert "You cannot delete" in response.text
    assert count_rows(app_module.DB_PATH, "posts") == 1


def test_delete_unknown_post_shows_message(client):
    register(client, "student01", "1234")
    login(client, "student01", "1234")

    response = client.post("/post/delete/999", follow_redirects=True)

    assert response.status_code == 200
    assert "Post not found" in response.text


@pytest.mark.slow
def test_slow_api_returns_expected_json(client):
    response = client.get("/api/slow")

    assert response.status_code == 200
    assert response.get_json() == {"status": "ok", "delay": 3}
