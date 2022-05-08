from typing import Dict
from telegram import Chat, Update
from telegram.ext import CallbackContext

from automatimebot import STOP_CODE
from automatimebot.abc import CompleteSession, Session
from automatimebot.handlers.utils import (
    get_chat_name,
    get_user_name,
    pretty_time_delta,
    task_comment_txt,
    try_delete_message,
)
from automatimebot.database import add_complete_session
from automatimebot.logging import get_logger

LOGGER = get_logger(__name__)


def stop_msg_format(complete_session: CompleteSession):
    session = complete_session.session
    human_timestamp = pretty_time_delta(complete_session.duration.total_seconds())
    return (
        f"{STOP_CODE} {session.author} stopped working"
        f"{task_comment_txt(session)} after {human_timestamp} [{complete_session.duration}]"
    )


def handle_stop(
    update: Update,
    context: CallbackContext,
    workers_in_chats: Dict[Chat, Dict[str, Session]],
):
    author = get_user_name(update.effective_user)
    chat = get_chat_name(update.effective_chat)
    date = update.message.date

    if not try_delete_message(
        context.bot, update.effective_chat, update.message.message_id
    ):
        return

    if chat in workers_in_chats and author in workers_in_chats[chat]:
        session = workers_in_chats[chat].pop(author)
        complete_session = CompleteSession(session, date)
        add_complete_session(chat, complete_session)
        msg = stop_msg_format(complete_session)
        context.bot.send_message(chat_id=update.effective_chat.id, text=msg)
        LOGGER.info(f"Update on {chat}: {msg}")
        return author