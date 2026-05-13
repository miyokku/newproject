from __future__ import annotations

import os
import sqlite3
from pathlib import Path

import pytest

import app as media_app


@pytest.fixture()
def isolated_app(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Создаёт изолированное приложение с отдельной БД и папкой uploads.

    Благодаря этому тесты не портят настоящую базу данных проекта
    instance/mediahub.sqlite3 и не зависят от уже созданных постов.
    """

    instance_dir = tmp_path / "instance"
    upload_dir = tmp_path / "uploads"
    instance_dir.mkdir()
    upload_dir.mkdir()

    test_db_path = instance_dir / "mediahub_test.sqlite3"

    monkeypatch.setattr(media_app, "DB_PATH", str(test_db_path))
    monkeypatch.setattr(media_app, "UPLOAD_DIR", str(upload_dir))

    media_app.app.config.update(
        TESTING=True,
        SECRET_KEY="test-secret-key",
    )

    media_app.init()

    yield media_app.app


@pytest.fixture()
def client(isolated_app):
    return isolated_app.test_client()


@pytest.fixture()
def app_module():
    return media_app


def register(client, username: str = "student01", password: str = "1234"):
    return client.post(
        "/register",
        data={"username": username, "password": password},
        follow_redirects=True,
    )


def login(client, username: str = "student01", password: str = "1234"):
    return client.post(
        "/login",
        data={"username": username, "password": password},
        follow_redirects=True,
    )


def logout(client):
    return client.get("/logout", follow_redirects=True)


def count_rows(db_path: str, table: str) -> int:
    conn = sqlite3.connect(db_path)
    try:
        return conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    finally:
        conn.close()


def fetch_one(db_path: str, query: str, params: tuple = ()):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        return conn.execute(query, params).fetchone()
    finally:
        conn.close()
