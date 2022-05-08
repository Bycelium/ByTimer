from typing import Dict
from telegram import Chat, Update
from telegram.ext import CallbackContext

from automatimebot import ISWORKING, SUMMARY
from automatimebot.abc import Session
from automatimebot.handlers.utils import get_chat_name, get_user_name
from automatimebot.handlers.start import (
    handle_current_tasks_dict,
    send_session_start,
    handle_start,
)
from automatimebot.handlers.stop import handle_stop
from automatimebot.handlers.load_tasks import store_task, handle_load_task
from automatimebot.handlers.show_data import (
    handle_is_working,
    handle_summary,
    data_menu,
)


class AutomatimeBot:
    def __init__(self) -> None:
        self.workers_in_chats: Dict[Chat, Dict[str, Session]] = {}
        self.current_tasks_dict: dict = None
        self.wait_comment: str = None
        self.wait_tasks: str = None

    def start(self, update: Update, context: CallbackContext):
        chat = get_chat_name(update.effective_chat)
        if chat not in self.workers_in_chats:
            self.workers_in_chats[chat] = {}

        task_dict, username = handle_start(update, context)
        if task_dict is not None:
            self.current_tasks_dict = task_dict
        if username is not None:
            self.wait_comment = username

    def start_session(
        self,
        update: Update,
        context: CallbackContext,
        comment: str,
    ) -> Session:
        author = get_user_name(update.effective_user)
        chat = get_chat_name(update.effective_chat)
        date = update.message.date

        task = (
            self.current_tasks_dict
            if isinstance(self.current_tasks_dict, str)
            else None
        )
        session = Session(author, date, comment, task)
        self.workers_in_chats[chat][author] = session
        return session

    def stop(self, update: Update, context: CallbackContext):
        return handle_stop(update, context, self.workers_in_chats)

    def data_menu(self, update: Update, context: CallbackContext):
        return data_menu(update, context)

    def load_task(self, update: Update, context: CallbackContext):
        author = get_user_name(update.effective_user)
        self.wait_tasks = author
        return handle_load_task(update, context)

    def messageHandler(self, update: Update, context: CallbackContext):
        text: str = update.message.text
        author = get_user_name(update.effective_user)
        if self.wait_comment is not None and author == self.wait_comment:
            session = self.start_session(update, context, text)
            self.wait_comment = None
            self.current_tasks_dict = None
            return send_session_start(update, context, session)
        if self.wait_tasks is not None and author == self.wait_tasks:
            self.wait_tasks = None
            return store_task(update, context)

    def queryHandler(self, update: Update, context: CallbackContext):
        text: str = update.callback_query.data
        if isinstance(self.current_tasks_dict, dict):
            self.current_tasks_dict, username = handle_current_tasks_dict(
                update, context, self.current_tasks_dict
            )
            if username is not None:
                self.wait_comment = username
            return
        if text == ISWORKING:
            return handle_is_working(update, context, self.workers_in_chats)
        if text.startswith(SUMMARY):
            return handle_summary(update, context)

    @staticmethod
    def unknown(update: Update, context: CallbackContext):
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Sorry, I didn't understand that command.",
        )