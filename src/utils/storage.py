import sqlite3

# ponytail: синхронный sqlite, таблицы на десятки строк; aiosqlite — если начнёт блокировать loop
_conn: sqlite3.Connection | None = None

SCHEMA_VERSION = 1


def init(path: str = "bot.db") -> None:
    global _conn
    _conn = sqlite3.connect(path)
    with _conn:
        version = _conn.execute("PRAGMA user_version").fetchone()[0]
        if version < 1:
            _conn.execute(
                "CREATE TABLE IF NOT EXISTS names("
                "user_id INTEGER PRIMARY KEY, name TEXT NOT NULL)"
            )
            _conn.execute(
                "CREATE TABLE IF NOT EXISTS summary_chats("
                "chat_id INTEGER PRIMARY KEY, title TEXT)"
            )
        # Будущие изменения схемы: if version < 2: ALTER ... (существующие таблицы не трогать).
        _conn.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")


def _db() -> sqlite3.Connection:
    if _conn is None:
        raise RuntimeError("storage.init() was not called")
    return _conn


def set_name(user_id: int, name: str) -> None:
    with _db() as c:
        c.execute(
            "INSERT INTO names(user_id, name) VALUES(?, ?) "
            "ON CONFLICT(user_id) DO UPDATE SET name = excluded.name",
            (user_id, name),
        )


def delete_name(user_id: int) -> None:
    with _db() as c:
        c.execute("DELETE FROM names WHERE user_id = ?", (user_id,))


def get_names() -> dict[int, str]:
    return dict(_db().execute("SELECT user_id, name FROM names ORDER BY name"))


def add_chat(chat_id: int, title: str | None) -> None:
    with _db() as c:
        c.execute(
            "INSERT INTO summary_chats(chat_id, title) VALUES(?, ?) "
            "ON CONFLICT(chat_id) DO UPDATE SET title = excluded.title",
            (chat_id, title),
        )


def remove_chat(chat_id: int) -> None:
    with _db() as c:
        c.execute("DELETE FROM summary_chats WHERE chat_id = ?", (chat_id,))


def get_chats() -> dict[int, str | None]:
    return dict(
        _db().execute("SELECT chat_id, title FROM summary_chats ORDER BY title")
    )


def is_chat_allowed(chat_id: int) -> bool:
    row = (
        _db()
        .execute("SELECT 1 FROM summary_chats WHERE chat_id = ?", (chat_id,))
        .fetchone()
    )
    return row is not None


if __name__ == "__main__":
    init(":memory:")
    assert get_names() == {} and get_chats() == {}
    assert not is_chat_allowed(-100)  # пустой список = /summary выключен везде
    set_name(1, "Айдын")
    set_name(1, "Айдын2")
    set_name(2, "Боб")
    assert get_names() == {1: "Айдын2", 2: "Боб"}
    delete_name(1)
    assert get_names() == {2: "Боб"}
    add_chat(-100, "Чат")
    add_chat(-100, "Чат2")
    assert get_chats() == {-100: "Чат2"} and is_chat_allowed(-100)
    assert not is_chat_allowed(-200)
    remove_chat(-100)
    assert get_chats() == {} and not is_chat_allowed(-100)
    init(":memory:")  # повторный init не падает
    print("ok")
