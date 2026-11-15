from types import SimpleNamespace

from pyrogram import Client

MAX_TEXT = 500
BATCH = 200


def is_relevant(m, thread_id: int | None) -> bool:
    if m.empty or m.service or (m.from_user and m.from_user.is_bot):
        return False
    if (m.text or "").startswith("/"):
        return False
    return thread_id is None or m.message_thread_id == thread_id


def _media_label(m) -> str | None:
    if m.photo:
        return "[фото]"
    if m.video:
        return "[видео]"
    if m.voice:
        return "[голосовое]"
    if m.video_note:
        return "[кружок]"
    if m.sticker:
        return f"[стикер {m.sticker.emoji or ''}]".replace(" ]", "]")
    if m.poll:
        return f"[опрос: {m.poll.question}]"
    if m.document or m.audio or m.animation:
        return "[файл]"
    return None


def format_message(m) -> str:
    if m.from_user:
        author = " ".join(filter(None, (m.from_user.first_name, m.from_user.last_name)))
        if m.from_user.username:
            author += f" (@{m.from_user.username})"
    elif m.sender_chat:
        author = m.sender_chat.title
    else:
        author = "?"
    text = m.text or m.caption or ""
    label = _media_label(m)
    if label:
        text = f"{label} {text}".strip()
    if len(text) > MAX_TEXT:
        text = text[:MAX_TEXT] + "…"
    reply = f" →{m.reply_to_message_id}" if m.reply_to_message_id else ""
    return f"[{m.id}] {author}{reply}: {text}"


async def fetch_lines(
    client: Client,
    chat_id: int,
    before_id: int,
    limit: int,
    thread_id: int | None = None,
) -> list[str]:
    # Боту недоступен getHistory, но get_messages по ID работает (только супергруппы).
    lines: list[str] = []
    scanned = 0
    top = before_id - 1
    while top > 0 and len(lines) < limit and scanned < limit * 2:
        ids = list(range(top, max(top - BATCH, 0), -1))
        scanned += len(ids)
        top -= len(ids)
        for m in await client.get_messages(chat_id, ids, replies=0):
            if is_relevant(m, thread_id) and len(lines) < limit:
                lines.append(format_message(m))
    return lines[::-1]


if __name__ == "__main__":

    def msg(**kw):
        fields = [
            "text",
            "caption",
            "photo",
            "video",
            "voice",
            "video_note",
            "sticker",
            "poll",
            "document",
            "audio",
            "animation",
            "from_user",
            "sender_chat",
            "reply_to_message_id",
            "message_thread_id",
        ]
        base = {f: None for f in fields} | {"id": 1, "empty": False, "service": False}
        return SimpleNamespace(**{**base, **kw})

    def user(first="Ann", last=None, username=None, bot=False):
        return SimpleNamespace(
            first_name=first, last_name=last, username=username, is_bot=bot
        )

    u = user("Ann", "Lee", "ann")
    assert format_message(msg(id=5, from_user=u, text="hi")) == "[5] Ann Lee (@ann): hi"
    assert (
        format_message(
            msg(id=6, from_user=user("Bob"), text="ok", reply_to_message_id=5)
        )
        == "[6] Bob →5: ok"
    )
    assert format_message(msg(from_user=u, photo=1, caption="смотри")).endswith(
        ": [фото] смотри"
    )
    assert format_message(msg(from_user=u, photo=1)).endswith(": [фото]")
    st = SimpleNamespace(emoji="😀")
    assert format_message(msg(from_user=u, sticker=st)).endswith(": [стикер 😀]")
    assert (
        format_message(msg(sender_chat=SimpleNamespace(title="Chan"), text="x"))
        == "[1] Chan: x"
    )
    assert format_message(msg(text="x")) == "[1] ?: x"
    assert format_message(msg(from_user=u, text="a" * 600)).endswith("a" * 500 + "…")
    assert is_relevant(msg(from_user=u, text="hi"), None)
    assert not is_relevant(msg(empty=True), None)
    assert not is_relevant(msg(service=True), None)
    assert not is_relevant(msg(from_user=user(bot=True), text="hi"), None)
    assert not is_relevant(msg(from_user=u, text="/summary"), None)
    assert is_relevant(msg(from_user=u, text="hi", message_thread_id=7), 7)
    assert not is_relevant(msg(from_user=u, text="hi", message_thread_id=8), 7)
    print("ok")
