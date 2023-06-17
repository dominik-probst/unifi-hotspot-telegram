import logging
import json
import warnings

from typing import List
from telegram import __version__ as TG_VER
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, User
from telegram.ext import (
    Application,
    CallbackContext,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
)
from pyunifi.controller import Controller

from unifi_hotspot_telegram.sqlite_connector import SQLiteConnector
from unifi_hotspot_telegram.i18n_manager import I18nManager
from unifi_hotspot_telegram.time_conversions import (
    convert_minutes_into_human_readable_string,
)


class TelegramBot:
    def __init__(
        self,
        bot_password: str,
        telegram_token: str,
        unifi_username: str,
        unifi_password: str,
        unifi_ip: str = "192.168.1.1",
        unifi_api_version: str = "UDMP-unifiOS",
        unifi_ssl_verify: bool = True,
        locale: str = "en",
        bot_accept_options: List[int] = [60, 1440, 4320, 10080],
    ) -> None:
        """Initialize the TelegramBot class.

        Args:
            bot_password (str): The password for registration of new chats (used for the "\register [password]" command)
            telegram_token (str): The Telegram bot token.
            unifi_username (str): The username for the UniFi controller.
            unifi_password (str): The password for the UniFi controller.
            unifi_ip (str, optional): The IP address of the UniFi controller. Defaults to "192.168.1.1".
            unifi_api_version (str, optional): The API version of the UniFi controller. Defaults to "UDMP-unifiOS". Options are [v4|v5|unifiOS|UDMP-unifiOS] (as described in https://github.com/finish06/pyunifi)
            unifi_ssl_verify (bool, optional): Whether to verify the SSL certificate of the UniFi controller. Defaults to True.
            locale (str, optional): The locale to use for the telegram bot. Defaults to 'en'. Options are [de|en]
            bot_accept_options (List[int], optional): A list of options (in minutes) for the user to select from when accepting a request. Defaults to [60, 1440, 4320, 10080] (1 hour, 1 day, 3 days, 1 week)
        """
        self.bot_password = bot_password
        self.telegram_token = telegram_token
        self.unifi_username = unifi_username
        self.unifi_password = unifi_password
        self.unifi_ip = unifi_ip
        self.unifi_api_version = unifi_api_version
        self.unifi_ssl_verify = unifi_ssl_verify

        self.i18n_manager = I18nManager(default_locale=locale)
        self.logger = logging.getLogger(__name__)
        self.application = Application.builder().token(telegram_token).build()
        self.db_connector = SQLiteConnector()

        valid_options = all(
            isinstance(opt, int) and opt > 0 for opt in bot_accept_options
        )
        if valid_options:
            self.bot_accept_options = bot_accept_options
        else:
            warnings.warn(
                "The provided bot_accept_options are invalid. Using default options instead."
            )
            self.bot_accept_options = [60, 1440, 4320, 10080]

    def __del__(self) -> None:
        """Clean up resources when the TelegramBot instance is deleted."""
        del self.db_connector

    def run(self) -> None:
        """Run the Telegram bot."""
        # Add handlers for commands
        self.application.add_handler(CommandHandler("register", self.register))
        self.application.add_handler(CommandHandler("help", self.help))
        self.application.add_handler(CommandHandler("start", self.start))

        # Add handler for inline keyboard buttons
        self.application.add_handler(CallbackQueryHandler(self.button))

        # Add a command to check for incoming requests regularly (default interval is 2 seconds)
        self.application.job_queue.run_repeating(
            self.check_requests, interval=2, first=0
        )

        # Run the bot until the user presses Ctrl-C
        self.application.run_polling()

    async def register(self, update: Update, context: CallbackContext) -> None:
        """Handle the register command.

        Args:
            update (telegram.Update): The update object.
            context (telegram.ext.CallbackContext): The callback context.
        """
        # Check if a password was provided
        if len(context.args) == 0:
            await update.message.reply_text(
                self.i18n_manager.translate("telegram_bot.register_password_required")
            )
            return

        password = context.args[0]
        chat_id = update.message.chat.id

        # Get all already registered chats
        known_chats = self.db_connector.get_known_chats()

        # If the chat is already registered, send a message
        if chat_id in known_chats:
            update.message.reply_text(
                self.i18n_manager.translate("telegram_bot.register_already_registered")
            )
        else:
            # Else check if the password is correct
            if password == self.bot_password:
                # If the password is correct, add the chat to the database
                self.db_connector.add_chat(chat_id)

                await update.message.reply_text(
                    self.i18n_manager.translate("telegram_bot.register_success")
                )
            else:
                # If the password is wrong, send a message
                # WARNING: There is currently no protection against brute force attacks
                # => If necessary it might be a good idea to limit the number of tries per telegram user
                await update.message.reply_text(
                    self.i18n_manager.translate("telegram_bot.register_wrong_password")
                )

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the start command.

        Args:
            update (telegram.Update): The update object.
            context (telegram.ext.CallbackContext): The callback context.
        """
        await update.message.reply_text(
            self.i18n_manager.translate("telegram_bot.start_tooltip")
        )

    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the help command.

        Args:
            update (telegram.Update): The update object.
            context (telegram.ext.CallbackContext): The callback context.
        """
        await update.message.reply_text(
            self.i18n_manager.translate("telegram_bot.help_tooltip")
        )

    async def button(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle the button callback query.

        Args:
            update (telegram.Update): The update object.
            context (telegram.ext.CallbackContext): The callback context.
        """
        query = update.callback_query

        # CallbackQueries need to be answered
        await query.answer()

        # Get the data from the callback query
        data = json.loads(query.data)
        duration = data["duration"]
        id = data["id"]

        # Get the messages and the request from the database
        messages = self.db_connector.get_messages(id)
        request = self.db_connector.get_request(id)
        name = request["name"]
        mac = request["mac"]

        # Get the the person who confirmed/denied the request
        confirmator = self.get_confirmator(query.from_user)

        # Add the confirmation to the database
        self.db_connector.add_confirmation(id, duration, confirmator)

        # Create the pyunifi controller instance
        # (We create the instance here and not in the constructor, because pyunifi seems to tend to lose the login after a while.)
        controller = Controller(
            self.unifi_ip,
            self.unifi_username,
            self.unifi_password,
            version=self.unifi_api_version,
            ssl_verify=self.unifi_ssl_verify,
        )

        # Authorize the guest
        controller.authorize_guest(mac, duration)

        # Compile the text to change the telegram messages to (to avoid the request being confirmed/denied multiple times)
        text = self.i18n_manager.translate(
            "telegram_bot.button_and_check_requests_access_requested",
            name=name,
            mac=mac,
        )
        text += "\n\n"

        if int(duration) > 0:
            human_readable_duration = convert_minutes_into_human_readable_string(
                int(duration), self.i18n_manager
            )

            text += self.i18n_manager.translate(
                "telegram_bot.button_access_granted",
                confirmator=confirmator,
                duration=human_readable_duration,
            )
        else:
            text += self.i18n_manager.translate(
                "telegram_bot.button_access_denied", confirmator=confirmator
            )

        # Change the request messages in all chats it was sent to
        for message in messages:
            await context.bot.edit_message_text(
                text, message["chat_id"], message["message_id"]
            )

    async def check_requests(self, context: CallbackContext) -> None:
        """Check for incoming requests.

        Args:
            context (telegram.ext.CallbackContext): The callback context.
        """
        # Get all open requests (= requests that were not sent to the telegram chats yet)
        open_requests = self.db_connector.get_open_requests()

        # For each open request ...
        for request in open_requests:
            id = request["id"]
            name = request["name"]
            mac = request["mac"]

            self.db_connector.update_request_sent_status(id)

            # ... send  a query to all registered chats
            known_chats = self.db_connector.get_known_chats()

            for known_chat in known_chats:
                chat_id = known_chat["chat_id"]
                keyboard = []

                # Add the different "accept" options
                keyboard_accept_options = []
                for duration in self.bot_accept_options:
                    duration_str = convert_minutes_into_human_readable_string(
                        duration, self.i18n_manager
                    )
                    button = InlineKeyboardButton(
                        duration_str,
                        callback_data=json.dumps({"duration": str(duration), "id": id}),
                    )
                    keyboard_accept_options.append(button)
                keyboard.append(keyboard_accept_options)

                # Add "deny" option
                deny_button = InlineKeyboardButton(
                    self.i18n_manager.translate(
                        "telegram_bot.check_requests_deny_access"
                    ),
                    callback_data=json.dumps({"duration": "-1", "id": id}),
                )
                keyboard.append([deny_button])

                reply_markup = InlineKeyboardMarkup(keyboard)

                message = self.i18n_manager.translate(
                    "telegram_bot.button_and_check_requests_access_requested",
                    name=name,
                    mac=mac,
                )
                message += "\n\n"
                message += self.i18n_manager.translate(
                    "telegram_bot.check_requests_confirm_access"
                )

                # Send the message and save the message id in the database (to be able to change the message later once the request was confirmed/denied)
                message_object = await context.bot.send_message(
                    chat_id=chat_id, text=message, reply_markup=reply_markup
                )

                message_id = message_object.message_id

                self.db_connector.insert_message(id, chat_id, message_id)

    def get_confirmator(self, user: User) -> str:
        """Combine the user's name, last name and username to a string.

        Args:
            user (telegram.User): The Telegram user.

        Returns:
            str: The confirmator string.
        """
        confirmator = ""

        if hasattr(user, "first_name"):
            confirmator += user.first_name + " "
        if hasattr(user, "last_name"):
            confirmator += user.last_name
        if hasattr(user, "username"):
            confirmator += " (@" + user.username + ")"

        return confirmator
