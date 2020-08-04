#!/usr/bin/python3
# coding=utf-8
# Created by evertonstz
""" This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.
You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>. """


# botfater descriptions
"""
start - show the help message again
a - add a game to your watching list
r - remove a game from your watching list
l - show the games that are in your watch list
stop - stop the bot and removes you from my database, YOUR WATCH LIST WILL BE DELETED!
"""
#optional dependencies
try: 
    from notify_run import Notify
except ImportError: 
    notify_run = None
    
try: 
    from pushover import Client
except ImportError: 
    Client = None

# from pynps.cli import cli_main
import traceback
import logging
from time import sleep
from dotenv import load_dotenv
import tswitch.variables as var
from tswitch.functions import *

#importing env variables
load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_ADM_CHATID = os.getenv("TELEGRAM_ADM_CHATID")
PUSHHOVER_USERKEY = os.getenv("PUSHHOVER_USERKEY")
PUSHOVER_APIKEY = os.getenv("PUSHOVER_APIKEY")

# # external
# import os, sys, inspect

from telegram.ext import CommandHandler, Filters, MessageHandler, Updater, PicklePersistence
import telegram

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',level=logging.INFO)
logger = logging.getLogger(__name__)

#functions
def PushNotif(context, text, title, priority):
    """send push notifications to the ADM for bug report purposes"""
    if text == '':
        text = 'unknown error'
    if title == '':
        title = "Telegram Switch watch bot bug report"

    if var.PUSHOVER:
        try:
            logging.info(f'ERROR HANDLER [pushover]: trying to send push notification')
            client = Client(PUSHHOVER_USERKEY, 
                            api_token=PUSHOVER_APIKEY)
            client.send_message(text, 
                                title=title, 
                                priority=priority)
            logging.info(f'ERROR HANDLER [pushover]: push notification sent')
        except Exception as e:
            logging.info(f'ERROR HANDLER [pushover]: unable to send push notification {e}')
    
    if var.NOTIFY_RUN:
        try:
            logging.info(f'ERROR HANDLER [notify.run]: trying to send push notification')
            notify = Notify()
            notify.send(f'{title}\n{text}')
            logging.info(f'ERROR HANDLER [notify.run]: push notification sent')
        except Exception as e:
            logging.info(f'ERROR HANDLER [notify.run]: unable to send push notification {e}')
    
    if var.TELEGRAM_DEBUG:
        try:
            logging.info(f'ERROR HANDLER [telegram]: trying to send push notification')
            try:
                context.bot.send_message(chat_id=TELEGRAM_ADM_CHATID, 
                                        text=f"<b>🔴{title}</b>\n<code>{text}</code>",
                                        parse_mode=telegram.ParseMode.HTML)
            except:
                context.bot.send_message(chat_id=TELEGRAM_ADM_CHATID, 
                                        text=f"🔴{title}\n{text}")
                
            logging.info(f'ERROR HANDLER [telegram]: push notification sent')
        except Exception as e:
            logging.info(f'ERROR HANDLER [telegram]: unable to send push notification {e}')
      
def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    
    logger.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))

    #TODO try to convert exc_traceback into a string
    PushNotif("Uncaught exception, possible force exit", "Uncaught exception, possible force exit", 0)

sys.excepthook = handle_exception

def get_script_dir(follow_symlinks=True):
    """function used to get the directory the script is located"""
    if getattr(sys, 'frozen', False): # py2exe, PyInstaller, cx_Freeze
        path = os.path.abspath(sys.executable)
    else:
        path = inspect.getabsfile(get_script_dir)
    if follow_symlinks:
        path = os.path.realpath(path)
    return os.path.dirname(path)


#telegram functions
def unknown(update, context):
    response_message = "Unknown command..."
    update.message.reply_text(response_message)

def stop(update, context):
    """used to remove user from database, can only be toggled by user request"""
    user_id = update.message.from_user.id
    key = "Watched IDs"
    value = update.message.text.partition(' ')[2]
    value_list = [x for x in value.split(' ') if x != '']
    #printing results
    if len(value_list) == 0:
        update.message.reply_text("<b>ATENTION! Ths will delete your current watch list and stop the bot!</b>\nIf that's what you want, send the bot this:\n<code>/stop yes</code>", 
                                  parse_mode=telegram.ParseMode.HTML)
    else:
        if value_list[0] == 'yes':
            logging.info(f'USER REQUEST {user_id}: user requested to be removed from database.')
            
            # blacking user's dictionary
            try:
                context.bot_data.pop(str(user_id))
            except KeyError:
                pass
                
            logging.info(f'USER REQUEST {user_id}: user removed from database.')
            update.message.reply_text("<b>Done!</b>\nYour data was removed and the bot won't notify you anymore!", 
                                  parse_mode=telegram.ParseMode.HTML)

    

def start(update, context):
    #TODO make user options here, including exit and delete options
    response_message = "Hi! This bot is still alpha and is kinda barebones and bugs are kinds expected. It checks every hour for new updates and every day for new titles in titleDB\n\n<b>What it can do:</b>\n➕Subscribe to any valid Game ID provided by the user\n➕Notify the user when any of his games in the watching list gets an update\
                        \n\n<b>To be implemented:</b>\n➖Receive full game metadata (for now, you can only see the game and update IDs when the bot notifies you about a new update) \
                        \n\n<b>Commands:</b> \
                        \n/a - add a game to your watching list, games can only be added by their GAME ID, multiple IDs must to be separated by a space \
                        \n\n/r - remove a game from your watching list, games can only be removed by their GAME ID, multiple IDs must to be separated by a space \
                        \n\n/l - show the games that are in your watch list \
                        \n\n/stop - stop the bot and removes you from my database, <b>YOUR WATCH LIST WILL BE DELETED!</b> If you ever come back you'll need to reenter your Game IDs \
                        \n\n\n<i>PSA: The bot should be able to notify me automatically for most bugs and erros, but feel free to contact me at:\nTelegram: @evertonstz \nDiscord: Identify as chinese#6975</i>"
    update.message.reply_text(response_message,
                              parse_mode=telegram.ParseMode.HTML)

def list_watched(update, context):
    """used to return the current watch list to the user"""
    user_id = update.message.from_user.id
    key = "Watched IDs"
    value = update.message.text.partition(' ')[2]

    # Load old values
    try:
        stored_game_ids = sorted(context.bot_data[str(user_id)])
    except KeyError:
        stored_game_ids = []
    
    logging.info(f'USER REQUEST {user_id}: game ids user already have saved {stored_game_ids}.')

    #printing results
    if len(stored_game_ids) > 0:
        reply_text = f"📺<b>The following game IDs are in your watch list</b>"
        for i in stored_game_ids:
            reply_text += f"\n{i}"
    else:
        logging.info(f'USER REQUEST {user_id}: user have no games in his watching list.')
        reply_text = f"📺<b>No games found</b>\nSeems like you didn't add any games to your watch list, try adding them with the /a command"
    
    if len(value) != 0:
        logging.info(f'USER REQUEST {user_id}: user called /l but provided arguments.')
        reply_text += "\n\n<i>PSA: You provided arguments to /l and this is not needed, so next time just use /l</i>"
    
    update.message.reply_text(reply_text,
                              parse_mode=telegram.ParseMode.HTML)
                                  
def rm_games(update, context):
    """used to remove games from users watch list"""
    user_id = update.message.from_user.id
    key = "Watched IDs"
    value = update.message.text.partition(' ')[2].replace('\n',' ')

    #filter the user values for possible valid game IDs
    #TODO more test is needed, maybe look for these IDs in the database to confirm a game exist
    value_list = []
    for i in [x for x in value.split(' ') if x != '']:
        if len(i) == 16 and i.endswith('800'):
            value_list.append(f'{i[:-3]}000')
        else:
             value_list.append(i)
             
    logging.info(f'USER REQUEST {user_id}: user databse interaction: rm_games, provided IDs {value_list}.')
    
    if len(value_list) == 0:
        logging.info(f'USER REQUEST {user_id}: user called /r but provided no arguments.')
        update.message.reply_text("📺<b>You didn't enter any Game ID</b>\nTo use /r you must provide at least one Game ID, multiple IDs must to be separated by a space\n\nExample: <code>/a 01000320000CC000 0100DA900B67A000</code>",
                                  parse_mode=telegram.ParseMode.HTML)
        return
    if len(value_list) > var.USER_LIMIT:
        logging.info(f'USER REQUEST {user_id}: user gave too many IDS{len(value_list)}')
        update.message.reply_text(f"📺<b>You entered too many Game IDs</b>\nThis bot can remove {var.USER_LIMIT} IDs per operation.",
                                  parse_mode=telegram.ParseMode.HTML)
        return      
    
    
    reply_dict = {x:'🔴Invalid Game ID' for x in value_list}
    
    valid_game_ids = list(set([x for x in value_list if x.isalnum() and len(x) == 16]))
    logging.info(f'USER REQUEST {user_id}: valid game ids provided by user {valid_game_ids}.')

    #adding valid ids to reply dictionary
    for i in valid_game_ids:
        reply_dict[i] = '🟠Not on watch list'
    
    # Load old values
    try:
        stored_game_ids = context.bot_data[str(user_id)]
    except KeyError:
        stored_game_ids = []

    logging.info(f'USER REQUEST {user_id}: game ids user already have saved {stored_game_ids}.')
    
    #adding game ids the user is already watchin
    for i in stored_game_ids:
        if i in value_list:
            reply_dict[i] = '🟢Removed from watch list'
    
    # filter out games that are already in the list
    game_ids = list(set(stored_game_ids)-set(valid_game_ids))
    logging.info(f'USER REQUEST {user_id}: game ids that will be resaved in users db {game_ids}.')
    # Store value
    context.bot_data[str(user_id)] = sorted(game_ids)

    #making reply string
    reply_text = '📺<b>The following procedures were made</b>'
    for i in reply_dict:
        reply_text += f"\n{reply_dict[i]}: {i}"
        
    if 'Removed from watch list' in reply_text:
        reply_text += "\n\n<i>You won't be getting notifications for</i> 🟢 <i>anymore!</i>"
    
    update.message.reply_text(reply_text,
                            parse_mode=telegram.ParseMode.HTML)

def add_games(update, context):
    """used to add games to user database, calls for AddToUserDB()"""
    user_id = update.message.from_user.id
    key = "Watched IDs"
    value = update.message.text.partition(' ')[2].replace('\n',' ')

    #filter the user values for possible valid game IDs
    #TODO more test is needed, maybe look for these IDs in the database to confirm a game exist
    value_list = []
    for i in [x for x in value.split(' ') if x != '']:
        if len(i) == 16 and i.endswith('800'):
            value_list.append(f'{i[:-3]}000')
        else:
            value_list.append(i)
             
    logging.info(f'USER REQUEST {user_id}: user databse interaction: add_games, provided IDs {value_list}.')
    
    if len(value_list) == 0:
        logging.info(f'USER REQUEST {user_id}: user called /a but provided no arguments.')
        update.message.reply_text("📺<b>You didn't enter any Game ID</b>\nTo use /a you must provide at least one Game ID, multiple IDs must to be separated by a space\n\nExample: <code>/a 01000320000CC000 0100DA900B67A000</code>",
                                  parse_mode=telegram.ParseMode.HTML)
        return
    if len(value_list) > var.USER_LIMIT:
        logging.info(f'USER REQUEST {user_id}: user gave too many IDS{len(value_list)}')
        update.message.reply_text(f"📺<b>You entered too many Game IDs</b>\nThis bot can only monitor {var.USER_LIMIT} IDs per user.",
                                  parse_mode=telegram.ParseMode.HTML)
        return      
    
    
    reply_dict = {x:'🔴Invalid Game ID' for x in value_list}
    
    valid_game_ids = list(set([x for x in value_list if x.isalnum() and len(x) == 16 and x.endswith('000')]))
    logging.info(f'USER REQUEST {user_id}: valid game ids provided by user {valid_game_ids}.')
    
    #adding valid ids to reply dictionary
    for i in valid_game_ids:
        reply_dict[i] = '🟢Added on watch list'
    
    # Load old values
    try:
        stored_game_ids = context.bot_data[str(user_id)]
    except KeyError:
        stored_game_ids = []

    logging.info(f'USER REQUEST {user_id}: game ids user already have saved {stored_game_ids}.')
    
    #adding game ids the user is already watchin
    for i in stored_game_ids:
        if i in value_list:
            reply_dict[i] = '🟠Already on watch list'
    
    # filter out games that are already in the list
    game_ids = list(set(valid_game_ids+stored_game_ids))
    
    if len(game_ids) > var.USER_LIMIT:
        logging.info(f'USER REQUEST {user_id}: user gave too many IDS{len(value_list)}')
        update.message.reply_text(f"📺<b>You entered too many Game IDs</b>\nThis bot can only monitor {var.USER_LIMIT} IDs per user.",
                                  parse_mode=telegram.ParseMode.HTML)
        return   
    
    logging.info(f'USER REQUEST {user_id}: game ids that will be resaved in users db {game_ids}.')
    # Store value
    context.bot_data[str(user_id)] = sorted(game_ids)

    #making reply string
    reply_text = '📺<b>The following procedures were made</b>'
    for i in reply_dict:
        reply_text += f"\n{reply_dict[i]}: {i}"
    
    if 'Added on watch list' in reply_text:
        reply_text += "\n\n<i>I'll let you know when</i> 🟢 <i>get new updates!</i>"
        
    update.message.reply_text(reply_text,
                              parse_mode=telegram.ParseMode.HTML)
   
 

def jobqueue_error_handler(context, traceback, jobqueue):
        #report to the user
        # bot.send_message(chat_id=chat_id, text="Oops, something went wrong around here. I reported this incident to the developer and he'll look into the problem soon!")
        logger.error(msg="Exception while handling an jobqueue update:", exc_info=traceback)
        
        #notify adm
        PushNotif(context, traceback, f'Bug report: JobQueue {jobqueue}', -1)

def error_handler(update, context):
    """Log the error and send a telegram message to notify the developer."""
    # Log the error before we do anything else, so we can see it even if something breaks.
    logger.error(msg="Exception while handling an update:", exc_info=context.error)

    # traceback.format_exception returns the usual python message about an exception, but as a
    # list of strings rather than a single string, so we have to join them together.
    tb_list = traceback.format_exception(None, context.error, context.error.__traceback__)
    tb = ''.join(tb_list)
    user_id = update.message.from_user.id
    # Build the message with some markup and additional information about what happ ened.
    # You might need to add some logic to deal with messages longer than the 4096 character limit.
    message = f"An exception was raised while handling an update\nUser ID: {str(user_id)}\n\n{tb}"

    # Finally, send the message
    PushNotif(context, message, 'Bug report', -1)
    
    # leting the user know
    try:
        if str(user_id) != TELEGRAM_ADM_CHATID:
            context.bot.send_message(chat_id=user_id, text="Oopsie, something went wrong on my side, I've reported the problem to my owner and he'll deal with it as soon as possible.")
            logging.info(f'ERROR HANDLER: letting the user know there was a problem')
    except Exception as e:
        logging.info(f'ERROR HANDLER: failed to message the user: {e}')

#job queues
def callback_nxversions(context: telegram.ext.CallbackContext):
    """this is the callack for xnversios's job queue"""
    
    logging.info(f'JobQueue [nx-versions]: start')
    result = []
    users_to_notify = {}
    try:
        result = UpdateNxversiosDB(f"{get_script_dir()}/database", f"{get_script_dir()}/nx-versions")
    except:
        jobqueue_error_handler(context, traceback.format_exc(), 'nx-versions -> callback_nxversions -> UpdateNxversiosDB')

    # result = [{'Base ID': '0100000000010000', 'Update Name': '0100000000010800', 'Update ID': '26214050'}, {'Base ID': '010000000EEF0000', 'Update Name': '010000000EEF0800', 'Update ID': '6553304050'}, {'Base ID': '010000100C4B8000', 'Update Name': '010000100C4B8800', 'Update ID': '19660304050'}, {'Base ID': '010000100FB62000', 'Update Name': '010000100FB62800', 'Update ID': '6553304050'}, {'Base ID': '010000300C79C000', 'Update Name': '010000300C79C800', 'Update ID': '3932304050'}, {'Base ID': '010000400F582000', 'Update Name': '010000400F582800', 'Update ID': '6553304050'}, {'Base ID': '010000500B9F4000', 'Update Name': '010000500B9F4800', 'Update ID': '6553304050'}, {'Base ID': '010000500DB50000', 'Update Name': '010000500DB50800', 'Update ID': '26214304050'}, {'Base ID': '01000060085D2000', 'Update Name': '01000060085D2800', 'Update ID': '1310304050'}]
    
    if len(result) > 0:
        logging.info(f'JobQueue [nx-versions]: calling NotifyUsersUpdate')
        users_to_notify = NotifyUsersUpdate(result, context.bot_data)
        logging.info(f'JobQueue [nx-versions]: {len(users_to_notify)} users to notify - Notification Dict {users_to_notify}')

        if len(users_to_notify) > 0:
            for user_id in users_to_notify:
                logging.info(f'JobQueue [nx-versions]: trying to notify {user_id}')
                reply_msg = '📺<b>New updates available</b>\n'
                for i in users_to_notify[user_id]:
                    # print(i)
                    logging.info(f'JobQueue [nx-versions]: Userdd ID {user_id} - Update: {i}')
                    reply_msg += f"<b>Base ID: {i['Base ID']}</b>\nUpdate ID: {i['Update Name']}\nLatest version: v{i['Update ID']}\n\n"
                
                sleep(2) #time between each user notification to avoid hitting API limits                 
                context.bot.send_message(chat_id=int(user_id), 
                                        text=reply_msg,
                                        parse_mode=telegram.ParseMode.HTML)
                                        
                logging.info(f'JobQueue [nx-versions]: notified {user_id}')
    
    logging.info(f'JobQueue [nx-versions]: end') 
    
# main
def main():
    #create db folder
    create_folder(f'{get_script_dir()}/database')
    my_persistence = PicklePersistence(filename=f'{get_script_dir()}/database/user_database.db')

    updater = Updater(token=TELEGRAM_TOKEN, persistence=my_persistence, use_context=True)
    job = updater.job_queue

    dispatcher = updater.dispatcher
    
    #start command
    #TODO respond with a help text
    dispatcher.add_handler(
        CommandHandler('start', start)
    )
    dispatcher.add_handler(
        CommandHandler('stop', stop)
    )


    #add, remove and list games to user database
    dispatcher.add_handler(
        CommandHandler('a', add_games)
    )

    dispatcher.add_handler(
        CommandHandler('r', rm_games)
    )

    dispatcher.add_handler(
        CommandHandler('l', list_watched)
    )

    #unknown command
    dispatcher.add_handler(
        MessageHandler(Filters.command, unknown)
    )

    # log all errors
    # TODO try to make error report work
    dispatcher.add_error_handler(error_handler)

    # add JobQueue for nx-versions and titledb
    #TODO add JobQueue for titledb
    job_nxversions = job.run_repeating(callback_nxversions, interval=var.VERSION_CHECKING_INTERVAL, first=0)
    # job_nxversions = job.run_repeating(callback_nxversions, interval=30, first=0)
    
    updater.start_polling()

    updater.idle()

if __name__ == '__main__':
    print("press CTRL + C to cancel.")
    main()
    
#FUNÇÃO USADA FUTURAMENTE PARA LER QRCODES
# def gender(update, context):
#     user = update.message.from_user
#     logger.info("Gender of %s: %s", user.first_name, update.message.text)
#     update.message.reply_text('I see! Please send me a photo of yourself, '
#                               'so I know what you look like, or send /skip if you don\'t want to.',
#                               reply_markup=ReplyKeyboardRemove())

#     return PHOTO