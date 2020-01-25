#!/usr/bin/env python
# -*- coding: utf-8 -*-
# =============================================================================
"""Official SUTD Hostel Hunt Bot

Initial version by https://t.me/kenghin

Further modified by jamestiotio to port to Firebase instead of using MySQL.

Some functions were also enhanced to provide a more wholesome Hostel Hunt experience.

This Bot uses the Updater class to handle the bot.

First, a few handler functions are defined. Then, those functions are passed to
the Dispatcher and registered at their respective places.
Then, the bot is started and runs until we press Ctrl-C on the command line.

Press Ctrl-C on the command line or send a signal to the process to stop the
bot.
"""

# Import libraries
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler, ConversationHandler
from telegram.error import TelegramError, Unauthorized, BadRequest, TimedOut, ChatMigrated, NetworkError
import logging
import time
import random
import re
from functools import wraps
from firebase_connector import FirebaseConnector
from argon2 import PasswordHasher
import quantumrandom

import saved_strings
import credentials

# Enable error logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

# Telegram Bot Auth Key
auth_key = credentials.TELEGRAM_TOKEN

# Initialize FirebaseConnector class
pb = FirebaseConnector()

ph = PasswordHasher()

# GLOBAL VARS
TIME_INTERVAL_BETWEEN_HINTS = 3600  # Unit in seconds
ALL_TOKENS = pb.get_all_tokens()
MASTER_ID = credentials.MASTER_TOKEN  # Bot owner Telegram ID
ADMIN_LIST = credentials.ADMIN_LIST
SUTD_AUTH = credentials.SUTD_AUTH

PORT = credentials.PORT
WEBHOOK_URL = credentials.WEBHOOK_URL

# For /register ConversationHandler purposes
AUTHTOKEN_REGISTER, STUDENTID_REGISTER = range(2)


# Only accessible if `user_id` is registered
def registered_only(func):
    @wraps(func)
    def wrapped(bot, update, *args, **kwargs):
        user_id = update.effective_user.id
        student_id = pb.get_student_id(user_id)

        if (str(user_id) not in pb.get_current_users()) or (int(student_id) == 0):
            print(f'Unauthorized access denied for user {user_id}.')
            bot.send_message(
                chat_id=user_id, text='That command is only available for registered users. Please register first!')
            return
        return func(bot, update, *args, **kwargs)

    return wrapped


# Only accessible if `user_id` is in `ADMIN_LIST`
def restricted(func):
    @wraps(func)
    def wrapped(bot, update, *args, **kwargs):
        user_id = update.effective_user.id
        if user_id not in ADMIN_LIST:
            print(f'Unauthorized admin access denied for user {user_id}.')
            return
        return func(bot, update, *args, **kwargs)

    return wrapped


# Define a few command handlers. These usually take the two arguments bot and
# update. Error handlers also receive the raised TelegramError object in error.

# =============================================================================
# HOUSEKEEPING COMMANDS begin the command with _
# =============================================================================


def _error(bot, update, error):
    """ Error handler. """

    try:
        raise error
    except ChatMigrated as e:
        print(e.new_chat_id)
        return e.new_chat_id

    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, error)


# =============================================================================
# LEVEL 0 COMMANDS
# =============================================================================


def start(bot, update):
    """ Start the bot and gives rules to the player. """

    # Get ID of sender
    user_id = update.effective_user.id

    msg = ('Hi! I am the official bot for SUTD Hostel Hunt 2020. '
           'Collaborate in teams of 5 to collect 4 tokens of the same colour to exchange for prizes!')

    rules = ('These are the rules for SUTD Hostel Hunt 2020:\r\n\r\n'
             '1. Please note that tokens will only be hidden in safe and accessible areas '
             '(e.g. away from ledges, parapets and electrical switch boxes) '
             'throughout the hostel premises.\r\n\r\n'
             '2. Only group leaders with the appropriate authentication tokens '
             'can interact effectively with this bot.\r\n\r\n'
             '3. All information is correct at time of print.')

    # Output message
    bot.send_message(chat_id=user_id, text=msg)
    bot.send_message(chat_id=user_id, text=rules)


def help(bot, update):
    """ Provide bot usage help text to the user. """

    user_id = update.effective_user.id

    help_text = ('These are the possible commands:\r\n\r\n'
                 '• /start to start the bot.\r\n'
                 '• /help to display usage help text for the bot.\r\n'
                 '• /register to register as a participant.\r\n'
                 '• /hint to ask the bot for hints.\r\n'
                 '• /claim <token> to attempt to claim the specified token.')

    bot.send_message(chat_id=user_id, text=help_text)

    if user_id in ADMIN_LIST:
        admin_text = ('These are the possible admin commands:\r\n\r\n'
                      '• /verify <hash> to verify a claim\'s hash.')

        bot.send_message(chat_id=user_id, text=admin_text)


def begin_register(bot, update):
    user_id = update.effective_user.id
    student_id = pb.get_student_id(user_id)

    if (str(user_id) in pb.get_current_users()) and (int(student_id) != 0):
        bot.send_message(
            chat_id=user_id, text='You are already registered. There is no need to register again.')

        return ConversationHandler.END

    else:
        bot.send_message(
            chat_id=user_id, text='Please enter the authentication token that you have received from our House Guardians. '
                                  'Do take note that once you have registered, you would not be able to de-register.\r\n\r\n'
                                  '/cancel to cancel the current registration process.')

        return AUTHTOKEN_REGISTER


def check_auth(bot, update):
    user_id = update.effective_user.id
    if update.message.text == SUTD_AUTH:
        pb.add_user(user_id)
        bot.send_message(
            chat_id=user_id, text='Please enter your student ID for registration.')

        return STUDENTID_REGISTER

    else:
        bot.send_message(
            chat_id=user_id, text='Please enter a valid authentication token.')


def studentid_input(bot, update):
    user_id = update.effective_user.id
    student_id = update.message.text

    if not (1000000 <= int(student_id) <= 1006000):  # Do a rough range check
        bot.send_message(
            chat_id=user_id, text="Please enter a valid student ID.")

    else:
        if int(student_id) in pb.get_all_current_student_id():
            msg = "Student ID already registered!"
        else:
            pb.update_student_id(user_id, int(student_id))
            msg = f"Successfully registered, {student_id}!"
        bot.send_message(chat_id=user_id, text=msg)

        return ConversationHandler.END


@registered_only
def hint(bot, update):
    user_id = update.effective_user.id
    # Get current time
    now = time.time()
    # Get last_hint_time
    last_hint_time = pb.get_last_hint_time(user_id)
    # if last_hint_time is None, get new hint
    if last_hint_time is None:
        output_msg = pb.get_hint()

        if output_msg != '':
            pb.update_last_hint_time(user_id, now)

    elif (int(now) - int(last_hint_time) >= TIME_INTERVAL_BETWEEN_HINTS):
        output_msg = pb.get_hint()

        if output_msg != '':
            pb.update_last_hint_time(user_id, now)

    else:
        output_msg = "Please try again in {} seconds.".format(
            int(last_hint_time) + TIME_INTERVAL_BETWEEN_HINTS - int(time.time()))

    if output_msg == '':
        bot.send_message(
            user_id, text='There are no hints currently available. Apologies!')

    else:
        bot.send_message(user_id, text=output_msg)


@registered_only
def claim(bot, update, args=[]):
    user_id = update.effective_user.id

    if len(args) == 1:

        code = args[0]

        if code not in ALL_TOKENS:
            bot.send_message(user_id, text=saved_strings.INVALID_CLAIM_1)

        elif code in pb.get_unclaimed_tokens():

            if str(user_id) in pb.get_all_users():

                # Prevent bot message tampering
                verification_hash = ph.hash(
                    str(code) + str(user_id) + str(time.time()) + str(quantumrandom.hex()))
                pb.claim_token(user_id, code, verification_hash)

                bot.send_message(user_id, text=saved_strings.VALID_CLAIM)
                bot.send_message(user_id, text=f'Please keep this message and present it to the House Guardians as proof when collecting your reward. '
                                               f'Your verification hash is:\r\n\r\n{verification_hash}')

        else:
            bot.send_message(user_id, text=saved_strings.INVALID_CLAIM_2)

    elif len(args) == 0:
        bot.send_message(user_id, text=saved_strings.INVALID_CLAIM_4)

    else:
        bot.send_message(user_id, text=saved_strings.INVALID_CLAIM_3)


# This is risky since it could go over Telegram's rate limits
@restricted
def broadcast(bot, update, args=[]):
    """ To broadcast message to everyone. """

    user_id = update.effective_user.id

    if user_id == MASTER_ID:
        msg = ''
        # TODO: Construct message here
        all_users = pb.get_current_users()
        for user in all_users:
            try:
                bot.send_message(user, text=msg)
            except:
                pass


@restricted
def verify_hash(bot, update, args=[]):
    user_id = update.effective_user.id

    if len(args) == 1:

        auth_hash = args[0]

        if auth_hash in pb.get_all_hash():
            bot.send_message(user_id, text='Hash exists in database.')

        else:
            bot.send_message(user_id, text='Hash does not exist in database.')

    elif len(args) == 0:
        bot.send_message(
            user_id, text='Please enter the hash together with the command.\r\n\r\nFormat of message: /verify <hash>')

    else:
        bot.send_message(
            user_id, text='Please provide one hash at a time!\r\n\r\nFormat of message: /verify <hash>')


# =============================================================================
# OTHER COMMANDS
# =============================================================================


# Fallback function for registration conversation
def fallback(bot, update):
    bot.send_message(chat_id=update.message.chat_id,
                     text='Please finish the current registration process first.')


# Cancel function for registration conversation
def cancel(bot, update):
    bot.send_message(chat_id=update.message.chat_id,
                     text='The current registration process has been cancelled.')

    return ConversationHandler.END


# =============================================================================
# MAIN BOT
# =============================================================================


def main():
    """ Start the bot. """
    # Create the EventHandler and pass it your bot's token.
    updater = Updater(auth_key)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    register_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("register", begin_register)],

        states={
            AUTHTOKEN_REGISTER: [MessageHandler(Filters.text, check_auth)],

            STUDENTID_REGISTER: [MessageHandler(
                Filters.regex('^[0-9]{7}$'), studentid_input)]
        },

        fallbacks=[CommandHandler('cancel', cancel),
                   CommandHandler('start', fallback),
                   CommandHandler('help', fallback),
                   CommandHandler("register", fallback),
                   CommandHandler('hint', fallback),
                   CommandHandler('claim', fallback),
                   CommandHandler('broadcast', fallback),
                   CommandHandler('verify', fallback)],

        per_message=False,

        allow_reentry=False
    )

    dp.add_handler(register_conv_handler)

    # Telegram Commands / Command Handlers
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(CommandHandler("hint", hint))
    dp.add_handler(CommandHandler("claim", claim, pass_args=True))

    # Administrative commands
    # dp.add_handler(CommandHandler("broadcast", broadcast, pass_args=True))
    dp.add_handler(CommandHandler("verify", verify_hash, pass_args=True))

    # Log all errors
    dp.add_error_handler(_error)

    # Start the bot
    # updater.start_polling(timeout=0)

    updater.start_webhook(listen='0.0.0.0', port=PORT, url_path=auth_key)
    updater.bot.set_webhook(WEBHOOK_URL + auth_key)

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
