import html
import logging
import re

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramAPIError
from aiogram.filters import Command
from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardMarkup,
    KeyboardButton,
    KeyboardButtonRequestChat,
    KeyboardButtonRequestUsers,
    Message,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder

from utils import storage
from utils.config import ADMIN_IDS

logger = logging.getLogger(__name__)

router = Router(name=__name__)
# Не админ: бот молчит (хендлеры не матчатся, команда уходит в другие роутеры).
router.message.filter(F.chat.type == "private", F.from_user.id.in_(ADMIN_IDS))
router.callback_query.filter(F.from_user.id.in_(ADMIN_IDS))

CANCEL = "Отмена"
MAX_NAME = 64


class AdminCb(CallbackData, prefix="adm"):
    action: str
    id: int = 0


class AddName(StatesGroup):
    user = State()
    name = State()


class AddChat(StatesGroup):
    chat = State()


def parse_user_id(text: str) -> int | None:
    m = re.fullmatch(r"[0-9]{1,16}", text.strip())
    return int(m[0]) if m and int(m[0]) > 0 else None


def parse_chat_id(text: str) -> int | None:
    m = re.fullmatch(r"-?[0-9]{1,16}", text.strip())
    return int(m[0]) if m and int(m[0]) != 0 else None


def clean_name(text: str) -> str | None:
    name = " ".join(text.split())  # переносы и повторные пробелы -> один пробел
    return name if 1 <= len(name) <= MAX_NAME else None


NAME_LINE = re.compile(r"\s*(\d{1,16})(?:\s*[:=\-–—]\s*|\s+)(.+)")


def parse_name_lines(text: str) -> tuple[list[tuple[int, str]], list[str]]:
    """Строки `id имя` / `id: имя` -> (валидные пары, нераспознанные строки)."""
    ok: list[tuple[int, str]] = []
    bad: list[str] = []
    for line in filter(None, (s.strip() for s in text.splitlines())):
        m = NAME_LINE.fullmatch(line)
        uid = parse_user_id(m[1]) if m else None
        name = clean_name(m[2]) if m else None
        if uid is None or name is None:
            bad.append(line)
        else:
            ok.append((uid, name))
    return ok, bad


def _short(s: str | None, n: int = 30) -> str:
    s = s or "?"
    return s if len(s) <= n else s[: n - 1] + "…"


def _menu() -> tuple[str, InlineKeyboardMarkup]:
    kb = InlineKeyboardBuilder()
    kb.button(text="👤 Имена", callback_data=AdminCb(action="names"))
    kb.button(text="💬 Чаты /summary", callback_data=AdminCb(action="chats"))
    kb.adjust(1)
    return "Админ-панель", kb.as_markup()


# ponytail: списки без пагинации (лимит ~90 кнопок / 4096 символов); пагинация — если записей станет больше
def _names_view() -> tuple[str, InlineKeyboardMarkup]:
    names = storage.get_names()
    text = "👤 Имена в сводке (заменяют имя из Telegram)\n\n" + (
        "\n".join(f"{uid} — {html.escape(n)}" for uid, n in names.items()) or "Пусто"
    )
    kb = InlineKeyboardBuilder()
    for uid, n in names.items():
        kb.button(
            text=f"❌ {_short(n)}", callback_data=AdminCb(action="del_name", id=uid)
        )
    kb.button(text="➕ Добавить", callback_data=AdminCb(action="add_name"))
    kb.button(text="⬅️ Назад", callback_data=AdminCb(action="menu"))
    kb.adjust(1)
    return text, kb.as_markup()


def _chats_view() -> tuple[str, InlineKeyboardMarkup]:
    chats = storage.get_chats()
    text = "💬 Чаты, где работает /summary\n\n" + (
        "\n".join(f"{html.escape(t or '?')} ({cid})" for cid, t in chats.items())
        or "Список пуст — /summary нигде не работает"
    )
    kb = InlineKeyboardBuilder()
    for cid, t in chats.items():
        kb.button(
            text=f"❌ {_short(t)}", callback_data=AdminCb(action="del_chat", id=cid)
        )
    kb.button(text="➕ Добавить", callback_data=AdminCb(action="add_chat"))
    kb.button(text="⬅️ Назад", callback_data=AdminCb(action="menu"))
    kb.adjust(1)
    return text, kb.as_markup()


def _reply_kb(*buttons: KeyboardButton) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[*buttons], [KeyboardButton(text=CANCEL)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


# --- отмена и меню ---


@router.message(Command("cancel"))
@router.message(F.text == CANCEL)
async def cancel(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Отменено", reply_markup=ReplyKeyboardRemove())
    text, kb = _menu()
    await message.answer(text, reply_markup=kb)


@router.message(Command("admin"))
async def admin(message: Message, state: FSMContext) -> None:
    await state.clear()
    text, kb = _menu()
    await message.answer(text, reply_markup=kb)


@router.callback_query(AdminCb.filter(F.action == "menu"))
async def cb_menu(callback: CallbackQuery) -> None:
    text, kb = _menu()
    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()


# --- имена ---


@router.callback_query(AdminCb.filter(F.action == "names"))
async def cb_names(callback: CallbackQuery) -> None:
    text, kb = _names_view()
    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()


@router.callback_query(AdminCb.filter(F.action == "del_name"))
async def cb_del_name(callback: CallbackQuery, callback_data: AdminCb) -> None:
    storage.delete_name(callback_data.id)
    text, kb = _names_view()
    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer("Удалено")


@router.callback_query(AdminCb.filter(F.action == "add_name"))
async def cb_add_name(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(AddName.user)
    await callback.message.answer(
        "Выберите пользователя кнопкой, пришлите его user_id "
        "или несколько строк «id Имя» сразу",
        reply_markup=_reply_kb(
            KeyboardButton(
                text="Выбрать пользователя",
                request_users=KeyboardButtonRequestUsers(
                    request_id=1, user_is_bot=False, request_name=True
                ),
            )
        ),
    )
    await callback.answer()


async def _add_names_batch(message: Message, state: FSMContext, text: str) -> None:
    ok, bad = parse_name_lines(text)
    bad_text = "\n".join(html.escape(_short(b, 60)) for b in bad[:10])
    if bad_text and len(bad) > 10:
        bad_text += f"\n… и ещё {len(bad) - 10}"
    if not ok:
        await message.answer(f"Не разобрал ни одной строки:\n{bad_text}")
        return
    for uid, name in ok:
        storage.set_name(uid, name)
    await state.clear()
    head = f"Сохранено: {len(ok)}"
    if bad:
        head += f"\nНе разобрал ({len(bad)}):\n{bad_text}"
    await message.answer(head, reply_markup=ReplyKeyboardRemove())
    view, kb = _names_view()
    await message.answer(view, reply_markup=kb)


@router.message(AddName.user)
async def add_name_user(message: Message, state: FSMContext) -> None:
    hint = None
    if message.users_shared and message.users_shared.users:
        u = message.users_shared.users[0]
        user_id = u.user_id
        hint = clean_name(f"{u.first_name or ''} {u.last_name or ''}")
    else:
        text = message.text or ""
        if len(text.split("\n")) > 1 or NAME_LINE.fullmatch(text.strip()):
            await _add_names_batch(message, state, text)
            return
        user_id = parse_user_id(text)
    if user_id is None:
        await message.answer("Нужна кнопка выбора или user_id из цифр")
        return
    await state.update_data(user_id=user_id)
    await state.set_state(AddName.name)
    await message.answer(
        f"Как называть {user_id} в сводке? (до {MAX_NAME} символов)",
        reply_markup=_reply_kb(*([KeyboardButton(text=hint)] if hint else [])),
    )


@router.message(AddName.name)
async def add_name_name(message: Message, state: FSMContext) -> None:
    name = clean_name(message.text or "")
    if name is None:
        await message.answer(f"Нужен текст от 1 до {MAX_NAME} символов")
        return
    user_id = (await state.get_data())["user_id"]
    storage.set_name(user_id, name)
    await state.clear()
    await message.answer("Сохранено", reply_markup=ReplyKeyboardRemove())
    text, kb = _names_view()
    await message.answer(text, reply_markup=kb)


# --- чаты /summary ---


@router.callback_query(AdminCb.filter(F.action == "chats"))
async def cb_chats(callback: CallbackQuery) -> None:
    text, kb = _chats_view()
    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()


@router.callback_query(AdminCb.filter(F.action == "del_chat"))
async def cb_del_chat(callback: CallbackQuery, callback_data: AdminCb) -> None:
    storage.remove_chat(callback_data.id)
    text, kb = _chats_view()
    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer("Удалено")


@router.callback_query(AdminCb.filter(F.action == "add_chat"))
async def cb_add_chat(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(AddChat.chat)
    await callback.message.answer(
        "Выберите группу кнопкой или пришлите chat_id (например -1001234567890)",
        reply_markup=_reply_kb(
            KeyboardButton(
                text="Выбрать группу",
                request_chat=KeyboardButtonRequestChat(
                    request_id=2,
                    chat_is_channel=False,
                    bot_is_member=True,
                    request_title=True,
                ),
            )
        ),
    )
    await callback.answer()


@router.message(AddChat.chat)
async def add_chat(message: Message, state: FSMContext, bot: Bot) -> None:
    if message.chat_shared:
        chat_id = message.chat_shared.chat_id
    else:
        chat_id = parse_chat_id(message.text or "")
    if chat_id is None:
        await message.answer("Нужна кнопка выбора или chat_id из цифр")
        return
    try:
        chat = await bot.get_chat(chat_id)
    except TelegramAPIError:
        await message.answer("Бот не состоит в этом чате")
        return
    if chat.type != "supergroup":
        await message.answer("Сводка работает только в супергруппах")
        return
    storage.add_chat(chat.id, chat.title)
    await state.clear()
    await message.answer("Сохранено", reply_markup=ReplyKeyboardRemove())
    text, kb = _chats_view()
    await message.answer(text, reply_markup=kb)
