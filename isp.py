
from instapy import InstaPy
from instapy import smart_run
import random as r
import schedule
import time
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters

# Replace with your actual Telegram bot token
telegram_token = '7647515503:AAGS7t15F-BC-JewX6EcnpuBK2z-YOYGwP8'
chat_id = '6437994839'  # The chat ID where your bot will send messages

# Store user credentials
user_credentials = {}

def bot_action(tag, action_type, count, username, password, comment_text=None):
    session = InstaPy(username=username, password=password, headless_browser=True)
    session.login()

    with smart_run(session):
        if action_type == 'like':
            session.like_by_tags([tag], amount=count)
        elif action_type == 'follow':
            session.set_do_follow(True, percentage=r.randint(40, 60))
            session.follow_user_followers(tag, amount=count)
        elif action_type == 'comment':
            session.set_do_comment(True, percentage=100)
            session.set_comments([comment_text])
            session.comment_by_tags([tag], amount=count)
        else:
            send_telegram_message("Invalid action type.")

    send_telegram_message(f"Thank you! Your order has been completed. The {action_type} action has been performed on {count} posts/users under the hashtag: {tag}!")

def send_telegram_message(text):
    bot = Bot(token=telegram_token)
    bot.send_message(chat_id=chat_id, text=text)

def start(update, context):
    keyboard = [
        [
            InlineKeyboardButton("Like Instagram Posts", callback_data='like'),
            InlineKeyboardButton("Comment on Instagram Posts", callback_data='comment'),
            InlineKeyboardButton("Follow Instagram Users", callback_data='follow')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("Welcome! What do you want? Choose an option below:", reply_markup=reply_markup)

def action_choice(update, context):
    query = update.callback_query
    action_type = query.data
    context.user_data['action_type'] = action_type  # Save action type for later use

    query.answer()
    query.edit_message_text(text=f"Please send the hashtag or keyword you want to target for {action_type}:")

def handle_message(update, context):
    user_message = update.message.text
    action_type = context.user_data.get('action_type')

    if user_message.startswith('#') or ' ' in user_message:  # Check if it's a hashtag or keyword
        context.user_data['tag'] = user_message  # Save tag/keyword
        update.message.reply_text(f"Got it! You've sent the tag/keyword: {user_message}. How many posts/users would you like to {action_type}?")
        return
    else:
        send_telegram_message("Please send a valid hashtag or keyword.")

def handle_count(update, context):
    user_message = update.message.text
    if user_message.isdigit():  # Check if the input is a number
        count = int(user_message)
        action_type = context.user_data.get('action_type')
        tag = context.user_data.get('tag')

        if action_type == 'comment':
            # Ask for the comment text if action is 'comment'
            update.message.reply_text("Please send the comment text you want to use for the posts.")
            return

        if update.message.chat.id in user_credentials:  # Check if credentials are provided
            username, password = user_credentials[update.message.chat.id]
            # Call the bot function with the action, count, username, password, and tag
            bot_action(tag, action_type, count, username, password)
            update.message.reply_text(f"Thank you! Your order is being processed for {count} posts/users under the tag {tag}.")
        else:
            update.message.reply_text("Please provide your Instagram credentials first (username and password).")
    else:
        update.message.reply_text("Please send a valid number.")

def handle_comment(update, context):
    comment_text = update.message.text
    action_type = context.user_data.get('action_type')
    count = context.user_data.get('count')
    tag = context.user_data.get('tag')

    if update.message.chat.id in user_credentials:
        username, password = user_credentials[update.message.chat.id]
        # Call the bot action for comment with the provided comment text
        bot_action(tag, action_type, count, username, password, comment_text)
        update.message.reply_text(f"Thank you! Your order is being processed for commenting on {count} posts under the tag {tag}.")
    else:
        update.message.reply_text("Please provide your Instagram credentials first (username and password).")

def set_credentials(update, context):
    # Prompt the user for Instagram credentials
    update.message.reply_text("Please enter your Instagram username:")
    return "username"

def save_username(update, context):
    username = update.message.text
    context.user_data['username'] = username
    update.message.reply_text("Please enter your Instagram password:")
    return "password"

def save_password(update, context):
    password = update.message.text
    # Store the credentials for this user
    user_credentials[update.message.chat.id] = (context.user_data['username'], password)
    update.message.reply_text("Your credentials have been saved successfully!")

    # Return to the main menu
    start(update, context)

# Telegram bot setup
updater = Updater(token=telegram_token, use_context=True)
dispatcher = updater.dispatcher

# Commands to trigger bot actions
start_handler = CommandHandler('start', start)
action_choice_handler = CallbackQueryHandler(action_choice)
status_handler = CallbackQueryHandler(status, pattern='^status$')

# Handling text messages (Hashtags/Keywords, Like count, and credentials)
message_handler = MessageHandler(Filters.text & ~Filters.command, handle_message)
count_handler = MessageHandler(Filters.text & ~Filters.command, handle_count)
comment_handler = MessageHandler(Filters.text & ~Filters.command, handle_comment)

# Handlers for username and password
set_credentials_handler = CommandHandler('set_credentials', set_credentials)
save_username_handler = MessageHandler(Filters.text, save_username)
save_password_handler = MessageHandler(Filters.text, save_password)

dispatcher.add_handler(start_handler)
dispatcher.add_handler(action_choice_handler)
dispatcher.add_handler(status_handler)
dispatcher.add_handler(message_handler)
dispatcher.add_handler(count_handler)
dispatcher.add_handler(comment_handler)

# Handlers for credentials
dispatcher.add_handler(set_credentials_handler)
dispatcher.add_handler(save_username_handler)
dispatcher.add_handler(save_password_handler)

updater.start_polling()

# Schedule the bot to run at specific times (Optional, if you want to schedule other actions)
schedule.every().day.at("07:15").do(bot)
schedule.every().day.at("16:37").do(bot)

# Run the scheduled tasks (optional)
while True:
    schedule.run_pending()
    time.sleep(15)
