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
s - search for a Game IDs using a game's name or a keyword
stop - stop the bot and removes you from my database, YOUR WATCH LIST WILL BE DELETED!
"""
#IMPORTS
import traceback
import logging
import datetime
from time import sleep
from dotenv import load_dotenv
from functools import wraps

import tswitch.variables as var
from tswitch.functions import *
# from tswitch.db import *
import tswitch.db as db

# # external
from telegram.ext import CommandHandler, Filters, MessageHandler, Updater, CallbackContext, CallbackQueryHandler
from telegram import ParseMode, Update, ChatAction, InlineKeyboardMarkup, InlineKeyboardButton
# import telegram

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',level=logging.INFO)
logger = logging.getLogger(__name__)

#importing and testing env variables
def get_script_dir(follow_symlinks=True):
    """function used to get the directory the script is located"""
    if getattr(sys, 'frozen', False): # py2exe, PyInstaller, cx_Freeze
        path = os.path.abspath(sys.executable)
    else:
        path = inspect.getabsfile(get_script_dir)
    if follow_symlinks:
        path = os.path.realpath(path)
    return os.path.dirname(path)
#test if there is a .env file
env_location = f'{get_script_dir()}/.env'
if os.path.isfile(env_location):
    #load from .env
    load_dotenv(dotenv_path=env_location)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

PUSHOVER_APIKEY, PUSHHOVER_USERKEY, PUSHOVER_DEBUG = validate_pushover_debug(os.getenv("PUSHOVER_APIKEY"),
                                                                            os.getenv("PUSHHOVER_USERKEY"),
                                                                            str_to_bool(os.getenv("PUSHOVER_DEBUG"))
                                                                            )

TELEGRAM_ADM_CHATID, TELEGRAM_DEBUG = validate_telegram_debug(os.getenv("TELEGRAM_ADM_CHATID"),
                                                        str_to_bool(os.getenv("TELEGRAM_DEBUG"))
                                                        )

PUSHBULLET_ACESS_TOKEN, PUSHBULLET_DEVICES, PUSHBULLET_DEBUG = validate_pushbullet_debug(os.getenv("PUSHBULLET_ACESS_TOKEN"),
                                                                                        os.getenv("PUSHBULLET_DEVICES"),
                                                                                        str_to_bool(os.getenv("PUSHBULLET_DEBUG"))
                                                                                        )
                                                                                        
NOTIFYRUN_DEBUG = validate_notifyrun_debug(str_to_bool(os.getenv("NOTIFYRUN_DEBUG")))

UNLIMITED_USERS = validate_unlimited_users(os.getenv("UNLIMITED_USERS"))

SEARCH_LIMIT = validate_search_limit(os.getenv("SEARCH_LIMIT"))

#FUNCTIONS

def PushNotif(context: CallbackContext, message: str, title: str, pushover_priority=-1):
    """send push notifications to the ADM for bug report purposes"""
    if message == '':
        message = 'unknown error'
    if message == '':
        message = "Telegram Switch watch bot bug report"

    if PUSHOVER_DEBUG:
        #pushover allows maximum 1024 characters on message and 250 on title
        #detecting if message splitting is needed, split message in various payloads if needed
        max_str_len = 1024
        max_titlestr_len = 250
        
        message_list = []
        if len(message) > max_str_len:
            message_list = [message[i:i+max_str_len] for i in range(0, len(message), max_str_len)]
        else:
            message_list = [message]
        
        if len(title) + (len(message_list)*2 + 4) > max_titlestr_len:
            rm_index = max_titlestr_len - (len(message_list)*2 + 4)
            croped_title = title[:rm_index]
        else:
            croped_title = title

        #trying to notify
        try:
            logging.info(f'ERROR HANDLER [pushover]: trying to send push notification')
            client = Client(PUSHHOVER_USERKEY, 
                            api_token=PUSHOVER_APIKEY)
            
            for index, croped_message in enumerate(message_list):
                client.send_message(croped_message, 
                                    title=f'{croped_title} [{index+1}/{len(message_list)}]', 
                                    priority=pushover_priority)
                sleep(1)
                
            logging.info(f'ERROR HANDLER [pushover]: push notification sent')
        except Exception as e:
            logging.info(f'ERROR HANDLER [pushover]: unable to send push notification {e}')
            
    if PUSHBULLET_DEBUG:
        #Ppushbullet seems to not limit messages, but I'll limit it to 10k characters just in case
        #detecting if message splitting is needed, split message in various payloads if needed
        max_str_len = 10000
        max_titlestr_len = 250
        
        message_list = []
        if len(message) > max_str_len:
            message_list = [message[i:i+max_str_len] for i in range(0, len(message), max_str_len)]
        else:
            message_list = [message]
        
        if len(title) + (len(message_list)*2 + 4) > max_titlestr_len:
            rm_index = max_titlestr_len - (len(message_list)*2 + 4)
            croped_title = title[:rm_index]
        else:
            croped_title = title
            
        #trying to notify
        try:
            logging.info(f'ERROR HANDLER [pushbullet]: trying to send push notification')
            pb = Pushbullet(PUSHBULLET_ACESS_TOKEN)
            
            for index, croped_message in enumerate(message_list):
                if len(PUSHBULLET_DEVICES) > 0:
                    for device in pb.devices:
                        if device.nickname in PUSHBULLET_DEVICES:
                            pb.push_note(f'{croped_title} [{index+1}/{len(message_list)}]', croped_message, device=device)
                else:
                    pb.push_note(f'{croped_title} [{index+1}/{len(message_list)}]', croped_message)
                sleep(1)
                
            logging.info(f'ERROR HANDLER [pushbullet]: push notification sent')
        except Exception as e:
            logging.info(f'ERROR HANDLER [pushbullet]: unable to send push notification {e}')
    
    if NOTIFYRUN_DEBUG:
        #it's not documented but with my tests notify.run limits messages to around 3900 characters, I'm setting the max to 3000 just to be on the safe side
        #detecting if message splitting is needed, split message in various payloads if needed
        max_titlestr_len = 250
        max_str_len = 3000 - max_titlestr_len
        
        message_list = []
        if len(message) > max_str_len:
            message_list = [message[i:i+max_str_len] for i in range(0, len(message), max_str_len)]
        else:
            message_list = [message]
        
        if len(title) + (len(message_list)*2 + 5) > max_titlestr_len:
            rm_index = max_titlestr_len - (len(message_list)*2 + 5)
            croped_title = title[:rm_index]
        else:
            croped_title = title
        
        #trying to notify
        try:
            logging.info(f'ERROR HANDLER [notify.run]: trying to send push notification')
            notify = Notify()
            # notify.send(f'{title}\n{message}')
            for index, croped_message in enumerate(message_list):
                notify.send(f'{croped_title} [{index+1}/{len(message_list)}]\n{croped_message}')
            
            logging.info(f'ERROR HANDLER [notify.run]: push notification sent')
        except Exception as e:
            logging.info(f'ERROR HANDLER [notify.run]: unable to send push notification {e}')
    
    if TELEGRAM_DEBUG:
        #telegram limits a max 4096 characters per message
        
        #detecting if message splitting is needed, split message in various payloads if needed
        max_titlestr_len = 250
        max_str_len = 4096 - max_titlestr_len
        
        message_list = []
        if len(message) > max_str_len:
            message_list = [message[i:i+max_str_len] for i in range(0, len(message), max_str_len)]
        else:
            message_list = [message]
        
        if len(title) + (len(message_list)*2 + 27) > max_titlestr_len:
            rm_index = max_titlestr_len - (len(message_list)*2 + 27)
            croped_title = title[:rm_index]
        else:
            croped_title = title
        
        #trying to notify
        try:
            logging.info(f'ERROR HANDLER [telegram]: trying to send push notification')
            for index, croped_message in enumerate(message_list):
                try:
                    context.bot.send_message(chat_id=TELEGRAM_ADM_CHATID, 
                                            text=f"<b>🔴{croped_title} [{index+1}/{len(message_list)}]</b>\n<code>{croped_message}</code>",
                                            parse_mode=ParseMode.HTML)
                except:
                    pass
                    context.bot.send_message(chat_id=TELEGRAM_ADM_CHATID, 
                                            text=f"🔴{croped_title} [{index+1}/{len(message_list)}]\n\n{croped_message}")
                
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

def get_bot_data(context: CallbackContext):
    bot_data_dict = context.bot_data
    return bot_data_dict

def get_user_id(update: Update):
    """get user id from update"""
    try:
        return str(update.message.from_user.id)
    except AttributeError:
        return False

def parse_args_from_value(value):
    """parse arguments from value"""
    value = value.partition(' ')[2].replace('\n',' ').upper()
    value_list = []
    for i in [x for x in value.split(' ') if x != '']:
        if len(i) == 16 and i.endswith('800'):
            value_list.append(f'{i[:-3]}000')
        else:
             value_list.append(i)
    return value_list

#telegram functions
def send_typing_action(func):
    """Sends typing action while processing func command.
    Source: https://github.com/python-telegram-bot/python-telegram-bot/wiki/Code-snippets#send-a-chat-action"""
    @wraps(func)
    def command_func(update, context, *args, **kwargs):
        context.bot.send_chat_action(chat_id=update.effective_message.chat_id, action=ChatAction.TYPING)
        return func(update, context,  *args, **kwargs)
    return command_func

def unknown(update: Update, context: CallbackContext):
    response_message = "Unknown command..."
    update.message.reply_text(response_message)

@send_typing_action
def settings(update: Update, context: CallbackContext):
    """used to change user's preferences on notifications"""
    user_id = get_user_id(update)
    
    value = update.message.text.partition(' ')[2]
    value_list = [x for x in value.split(' ') if x != '']
    
    # Load old values
    user_db = db.find('user_data', {"_id":user_id})
    if user_db['options']['notify_all'] == 1: #user is already wathcing all
        notify_all_keyboard = InlineKeyboardButton(text='Notify All [ON]', callback_data='notify_all_on')
    else:
        notify_all_keyboard = InlineKeyboardButton(text='Notify All [OFF]', callback_data='notify_all_off')
    
    if user_db['options']['mute'] == 1: #user is already muted
        mute_keyboard = InlineKeyboardButton(text='Mute [ON]', callback_data='mute_on')
    else:
        mute_keyboard = InlineKeyboardButton(text='Mute [OFF]', callback_data='mute_off')

    
    keyboard = [[notify_all_keyboard, mute_keyboard],
                [InlineKeyboardButton(text='Close Settings', callback_data='close_settings')]
                ]
    
    markup = InlineKeyboardMarkup(keyboard)
    
    reply_text = "<b>⚙️Settings</b>\nThe follwing settings options are available:\
                    \n\n<b>Notify All:</b> when this option is ON you'll receive notifications when ANY nintendo switch game gets a new update. When the option is OFF you'll only be notified when games in your watch list gets a new update (you can see these games at /l).\
                    \n\n<b>Mute:</b> this will mute the bot and you won't be notified when a game gets new updates. This will also mute announcements from the bot admin\
                    \n\n<b>Close Settings:</b> will close the settings, you can reopen settings again with /settings."
    
    update.message.reply_text(reply_text,
                                parse_mode=ParseMode.HTML,
                                reply_markup=markup
                                )
    
    
    # #printing results
    # if len(value_list) == 0:
    #     logging.info(f'USER REQUEST {user_id}: user requested notify settings.')
    #     #set user notify_all to 1 on mongodb
    #     res = db.update_document_gen('user_data', 
    #                                     {'_id': user_id},
    #                                     {'$set': {'options.notify_all': 1} }
    #                                     )
        
    #     if res.modified_count > 0:
    #         logging.info(f'USER REQUEST {user_id}: user will bypass watching list and be notified about every game.')
    #         reply_text = "<b>Done!</b>\nYou'll now receive notifications about any Switch game that gets an update, if it becomes annoying to you, all you need to do is run /notifyall again and you'll come back to only being notified about games that are your waching list (you can add games there with /a and what's already there with /l)"
    #     else:
    #         reply_text = "<b>Whoaa, 
    #     #remove user from mongo
    #     a = db.rm_from_collection('user_data', user_id)
    #     print(a.deleted_count)
            
    #     logging.info(f'USER REQUEST {user_id}: user removed from database.')
    #     update.message.reply_text(reply_text, 
    #                             parse_mode=ParseMode.HTML)
            
@send_typing_action
def stop(update: Update, context: CallbackContext):
    """used to remove user from database, can only be toggled by user request"""
    user_id = get_user_id(update)
    
    value = update.message.text.partition(' ')[2]
    value_list = [x for x in value.split(' ') if x != '']
    #printing results
    if len(value_list) == 0:
        update.message.reply_text("<b>ATENTION! Ths will delete your current watch list and stop the bot!</b>\nIf that's what you want, send the bot this:\n<code>/stop yes</code>", 
                                  parse_mode=ParseMode.HTML)
    else:
        if value_list[0] == 'yes':
            logging.info(f'USER REQUEST {user_id}: user requested to be removed from database.')
            
            #remove user from mongo
            a = db.rm_from_collection('user_data', user_id)
            print(a.deleted_count)
                
            logging.info(f'USER REQUEST {user_id}: user removed from database.')
            update.message.reply_text("<b>Done!</b>\nYour data was removed and the bot won't notify you anymore!", 
                                  parse_mode=ParseMode.HTML)

@send_typing_action
def start(update: Update, context: CallbackContext):
    #TODO move user database creation from other functions into start!
    update.message.reply_text(var.START_MESSAGE,
                              parse_mode=ParseMode.HTML)

@send_typing_action
def search(update: Update, context: CallbackContext):
    """search function"""
    user_id = get_user_id(update)
    value = update.message.text.partition(' ')[2].strip()
    value = str_to_alphanum(value) #remove non alphanum but keep spaces
    
    logging.info(f'USER REQUEST {user_id}: user requested to search the database for {value}')
    if len(value) > 0:
        result = db.search('titledb', { "name" : {"$regex" : value, '$options' : 'i'}, "_id" : {"$regex" : '000$'} }, 'rank')
        #TODO test if it's passing telegram's character limit for messages
        if len(result) > 0:
            #strip results
            if len(result) > SEARCH_LIMIT:
                result = result[:SEARCH_LIMIT]
            
            reply_text = ''
            for game_dict in result:
                reply_text += f"\n\n<b>Name:</b> {test_dict_key(game_dict, 'name')}\n<b>Base Game ID:</b> <code>{test_dict_key(game_dict, '_id')}</code>\n<b>Update ID:</b> <code>{test_dict_key(game_dict, 'updateId')}</code>\n<b>Latest Version:</b> v{test_dict_key(game_dict, 'latestVersion')}\n<b>Region:</b> {test_dict_key(game_dict, 'region')}"
                # reply_text += f"\n<code>{i['_id']}</code> - {i['name']}"

            messages_list = split_message(reply_text, "📺<b>Search Games</b>")

    
            for message in messages_list:
                update.message.reply_text(message,
                                        parse_mode=ParseMode.HTML)

            # update.message.reply_text(reply_text,
            #                         parse_mode=ParseMode.HTML)
            
        else:
            update.message.reply_text("📺<b>Search Games</b>\nNo games found with the given keyword.",
                                    parse_mode=ParseMode.HTML)
    else:
        update.message.reply_text("📺<b>Search Games</b>\nYou need a keyword to search the database.\nExample: <code>/s paper mario</code>",
                        parse_mode=ParseMode.HTML)
        
        

# def broadcast(update: Update, context: CallbackContext):
#     """broadcast message to every user"""
#     user_id = get_user_id(update)
#     #only run if chat id is adm
#     if user_id == TELEGRAM_ADM_CHATID:
#         value = update.message.text.partition(' ')[2]
#         # Load chat values
            # try:
            #     stored_game_ids = get_bot_data(context)[user_id]
            # except KeyError:
            #     stored_game_ids = []
                
@send_typing_action
def list_watched(update: Update, context: CallbackContext):
    """used to return the current watch list to the user"""
    logging.info(f'USER REQUEST: user asked for list_watched.')
    
    user_id = get_user_id(update)
    if user_id == False:
        logging.warning("List watched: unable to get user_id, skipping")
        return
    
    value = update.message.text.partition(' ')[2]

    user_db = db.find('user_data', {"_id":user_id})

    if user_db == None:
        #no user_db, init one
        user_db = db.touch_user('user_data', user_id)
        stored_game_ids = []
    else:
        stored_game_ids = user_db['watched_games']

    
    
    #printing results
    if len(stored_game_ids) > 0:
        #load titledb for the IDs in stored_game_ids
        title_db = db.search('titledb', {'_id': {'$in':stored_game_ids}}, order_key='name' )
        reply_text = ''
        for game_dict in title_db: 
            reply_text += f"\n\n<b>Name:</b> {test_dict_key(game_dict, 'name')}\n<b>Base Game ID:</b> <code>{test_dict_key(game_dict, '_id')}</code>\n<b>Update ID:</b> <code>{test_dict_key(game_dict, 'updateId')}</code>\n<b>Latest Version:</b> v{test_dict_key(game_dict, 'latestVersion')}\n<b>Region:</b> {test_dict_key(game_dict, 'region')}"
            # reply_text += f"\n<code>{game_dict['_id']}</code> - {game_dict['name']} ({game_dict['region']})"
        
        if len(value) != 0:
            logging.info(f'USER REQUEST {user_id}: user called /l but provided arguments.')
            reply_text += "\n\n<i>PSA: You provided arguments to /l and this is not needed, so next time just use /l</i>"
        
        messages_list = split_message(reply_text, f"📺<b>The following game IDs are in your watch list</b>")
        
    else:
        logging.info(f'USER REQUEST {user_id}: user have no games in his watching list.')
        messages_list = [f"📺<b>No games found</b>\nSeems like you didn't add any games to your watch list, try adding them with the /a command"]
    
    
    for message in messages_list:
        update.message.reply_text(message,
                                parse_mode=ParseMode.HTML)
    

@send_typing_action                               
def rm_games(update: Update, context: CallbackContext):
    """used to remove games from users watch list"""
    user_id = get_user_id(update)

    #filter the user values for possible valid game IDs
    value_list = parse_args_from_value(update.message.text)
    
    logging.info(f'USER REQUEST {user_id}: user databse interaction: rm_games, provided IDs {value_list}.')
    
    if len(value_list) == 0:
        logging.info(f'USER REQUEST {user_id}: user called /r but provided no arguments.')
        update.message.reply_text("📺<b>You didn't enter any Game ID</b>\nTo use /r you must provide at least one Game ID, multiple IDs must to be separated by a space.\n\nExample: <code>/a 01000320000CC000 0100DA900B67A000</code>\n\n<i>PSA: Don't know the game's ID? Try using /l to list all the games you're currently wathing</i>",
                                  parse_mode=ParseMode.HTML)
        return
    if len(value_list) > var.USER_LIMIT and user_id not in UNLIMITED_USERS:
        logging.info(f'USER REQUEST {user_id}: user gave too many IDS: {len(value_list)}')
        update.message.reply_text(f"📺<b>You entered too many Game IDs</b>\nThis bot can remove {var.USER_LIMIT} IDs per operation.",
                                  parse_mode=ParseMode.HTML)
        return      
    
    
    reply_dict = {x:'🔴Invalid Game ID' for x in value_list}
    
    valid_game_ids = list(set([x for x in value_list if x.isalnum() and len(x) == 16]))
    logging.info(f'USER REQUEST {user_id}: valid game ids provided by user {valid_game_ids}.')

    #adding valid ids to reply dictionary
    for i in valid_game_ids:
        reply_dict[i] = '🟠Not on watch list'
    
    # Load old values
    user_db = db.find('user_data', {"_id":user_id})

    if user_db == None:
        #no user_db, init one
        user_db = db.touch_user('user_data', user_id)
        stored_game_ids = []
    else:
        stored_game_ids = user_db['watched_games']

    logging.info(f'USER REQUEST {user_id}: game ids user already have saved {stored_game_ids}.')
    
    #adding game ids the user is already watchin
    for i in stored_game_ids:
        if i in value_list:
            reply_dict[i] = '🟢Removed from watch list'
    
    # filter out games that are already in the list
    game_ids = list(set(stored_game_ids)-set(valid_game_ids))
    logging.info(f'USER REQUEST {user_id}: game ids that will be resaved in users db {game_ids}.')
    
    # Store dicts on user_db and update them on mongodb
    user_db['watched_games'] = sorted(game_ids)
    db.update_collection('user_data', user_db)

    #making reply string
    reply_text = '📺<b>The following procedures were made</b>'
    for i in reply_dict:
        reply_text += f"\n{reply_dict[i]}: <code>{i}</code>"
        
    if 'Removed from watch list' in reply_text:
        reply_text += "\n\n<i>You won't be getting notifications for</i> 🟢 <i>anymore!</i>"
    else:
        reply_text += "\n\nTo use /r you must provide at least one Game ID that's on your watch list, multiple IDs must to be separated by a space.\n\nExample: <code>/a 01000320000CC000 0100DA900B67A000</code>\n\n<i>PSA: Don't know the game's ID? Try using /l to list all the games you're currently wathing</i>"
    
    update.message.reply_text(reply_text,
                            parse_mode=ParseMode.HTML)

@send_typing_action
def add_games(update: Update, context: CallbackContext):
    """used to add games to user database, calls for AddToUserDB()"""
    user_id = get_user_id(update)
    #filter the user values for possible valid game IDs
    value_list = parse_args_from_value(update.message.text)
             
    logging.info(f'USER REQUEST {user_id}: user databse interaction: add_games, provided IDs {value_list}.')
    
    if len(value_list) == 0:
        logging.info(f'USER REQUEST {user_id}: user called /a but provided no arguments.')
        update.message.reply_text("📺<b>You didn't enter any Game ID</b>\nTo use /a you must provide at least one Game ID, multiple IDs must to be separated by a space\n\nExample: <code>/a 01000320000CC000 0100DA900B67A000</code>\n\n<i>PSA: Don't know the game's ID? Try searching a game's name with the /s command, the game ID will be in the results</i>",
                                  parse_mode=ParseMode.HTML)
        return
    if len(value_list) > var.USER_LIMIT and user_id not in UNLIMITED_USERS:
        logging.info(f'USER REQUEST {user_id}: user gave too many IDS: {len(value_list)}')
        update.message.reply_text(f"📺<b>You entered too many Game IDs</b>\nThis bot can only monitor {var.USER_LIMIT} IDs per user.",
                                  parse_mode=ParseMode.HTML)
        return      
    
    
    reply_dict = {x:'🔴Invalid Game ID' for x in value_list}
    
    valid_game_ids = list(set([x for x in value_list if x.isalnum() and len(x) == 16 and x.endswith('000') and db.is_id_on_db('titledb', x)]))
    logging.info(f'USER REQUEST {user_id}: valid game ids provided by user {valid_game_ids}.')
    
    #adding valid ids to reply dictionary
    for i in valid_game_ids:
        reply_dict[i] = '🟢Added on watch list'
    
    # Load old values
    user_db = db.find('user_data', {"_id":user_id})

    if user_db == None:
        #no user_db, init one
        user_db = db.touch_user('user_data', user_id)
        stored_game_ids = []
    else:
        stored_game_ids = user_db['watched_games']


    logging.info(f'USER REQUEST {user_id}: game ids user already have saved {stored_game_ids}.')
    
    #adding game ids the user is already watchin
    for i in stored_game_ids:
        if i in value_list:
            reply_dict[i] = '🟠Already on watch list'
    
    # filter out games that are already in the list
    game_ids = list(set(valid_game_ids+stored_game_ids))

    if len(game_ids) > var.USER_LIMIT and user_id not in UNLIMITED_USERS:
        logging.info(f'USER REQUEST {user_id}: user gave too many IDS: {len(value_list)}')
        update.message.reply_text(f"📺<b>You entered too many Game IDs</b>\nThis bot can only monitor {var.USER_LIMIT} IDs per user.",
                                parse_mode=ParseMode.HTML)
        return
    
    logging.info(f'USER REQUEST {user_id}: game ids that will be resaved in users db {game_ids}.')
    
    # Store dicts on user_db and update them on mongodb
    user_db['watched_games'] = sorted(game_ids)
    db.update_collection('user_data', user_db)

    #making reply string
    reply_text = '📺<b>The following procedures were made</b>'
    for i in reply_dict:
        reply_text += f"\n{reply_dict[i]}: <code>{i}</code>"
    
    if 'Added on watch list' in reply_text:
        reply_text += "\n\n<i>I'll let you know when</i> 🟢 <i>get new updates!</i>"
    else:
        reply_text += "\n\nTo use /a you must provide at least one valid Game ID, multiple IDs must to be separated by a space\n\nExample: <code>/a 01000320000CC000 0100DA900B67A000</code>\n\n<i>PSA: Don't know the game's ID? Try searching a game's name with the /s command, the game ID will be in the results</i>"
        
    update.message.reply_text(reply_text,
                              parse_mode=ParseMode.HTML)

def jobqueue_error_handler(context: CallbackContext, traceback: str, log_msg: str):
        #report to the user
        # bot.send_message(chat_id=chat_id, text="Oops, something went wrong around here. I reported this incident to the developer and he'll look into the problem soon!")
        logger.error(msg=log_msg, exc_info=traceback)
        
        #notify adm
        PushNotif(context, traceback, f'Bug report: JobQueue {log_msg}', -1)


def error_handler(update: Update, context: CallbackContext):
    """Log the error and send a telegram message to notify the developer."""
    # Log the error before we do anything else, so we can see it even if something breaks.
    logger.error(msg="Exception while handling an update:", exc_info=context.error)

    # traceback.format_exception returns the usual python message about an exception, but as a
    # list of strings rather than a single string, so we have to join them together.
    tb_list = traceback.format_exception(None, context.error, context.error.__traceback__)
    tb = ''.join(tb_list)
    user_id = get_user_id(update)
    # Build the message with some markup and additional information about what happ ened.
    
    message = f"\n\n{tb}"
    title = f'An exception was raised while handling an update\nUser ID: {user_id}'

    #list of erros that won't notify the adm
    # Finally, send the message
    not_notify_list = ['HTTPError']
    if any(i in tb for i in not_notify_list) is False:
        PushNotif(context, message, title, -1)


    # leting the user know
    # try:
    #     if user_id != TELEGRAM_ADM_CHATID:
    #         context.bot.send_message(chat_id=user_id, text="Oopsie, something went wrong on my side, I've reported the problem to my owner and he'll deal with it as soon as possible.")
    #         logging.info(f'ERROR HANDLER: letting the user know there was a problem')
    # except Exception as e:
    #     logging.info(f'ERROR HANDLER: failed to message the user: {e}')

def button(update, context):
    query = update.callback_query
    # CallbackQueries need to be answered, even if no notification to the user is needed
    # Some clients may have trouble otherwise. See https://core.telegram.org/bots/api#callbackquery
    query.answer()
    
    user_id = str(query.from_user.id)
    
    q_data = format(query.data)
    print('q_data: ', q_data)
    
    if q_data == 'notify_all_on':
        #turn off notify all
        res = db.update_document_gen('user_data', 
                                        {'_id': user_id},
                                        {'$set': {'options.notify_all': 0} }
                                        )
        
        reply_text = "<b>Done!</b>\nYou'll now only receive notifications for games that are in your watching list.\nYou can see these games with /l, add more games to that list with /a and remove with /r"
    elif q_data == 'notify_all_off':
        res = db.update_document_gen('user_data', 
                                        {'_id': user_id},
                                        {'$set': {'options.notify_all': 1} }
                                        )
        reply_text = "<b>Done!</b>\nYou'll be notified when a new update for any Nitendo Switch game comes out.\n\n<i>PSA:Keep in mind you could receive multiple notifications per day, this might become annoying pretty quickly! In case that happens all you need to is disable this feature on /settings</i>"
    
    if q_data == 'mute_on':
        #turn off notify all
        res = db.update_document_gen('user_data', 
                                        {'_id': user_id},
                                        {'$set': {'options.mute': 0} }
                                        )
        
        reply_text = "<b>Done!</b>\nBot will start sending you messages about game updates again!"
    elif q_data == 'mute_off':
        res = db.update_document_gen('user_data', 
                                        {'_id': user_id},
                                        {'$set': {'options.mute': 1} }
                                        )
        reply_text = "<b>Done!</b>\nBot will stop sending you messages about game updates!\n\n<i>PSA: Keep in mind this option will only prevent the bot from messaging you, if you want to receive messages again you can unmute it on /settings, if you want to stop the bot and delete your data from the server for ever, use /stop</i>"
    
    if q_data == 'close_settings':
        reply_text = "<b>⚙️Settings Closed</b>\nYou can reopen it again with /settings"
    
    query.edit_message_text(text=reply_text,
                            parse_mode=ParseMode.HTML
                            )

#job queues
def callback_titledb(context: CallbackContext):
    """this is the callack for titledb's job queue"""  
    logging.info('JobQueue [titledb]: start')
    result = False
    
    try:
        result = UpdateTitleDB(f"{get_script_dir()}/database", f"{get_script_dir()}/titledb")
    except:
        jobqueue_error_handler(context, traceback.format_exc(), 'titledb -> callback_titledb -> UpdateTitleDB')

    if result:
        logging.info('JobQueue [titledb]: titledb updated')
    else:
        logging.info('JobQueue [titledb]: titledb not updated') 
    
    logging.info('JobQueue [titledb]: end') 
    
 
def callback_nxversions(context: CallbackContext):
    """this is the callack for xnversios's job queue"""
    
    logging.info('JobQueue [nx-versions]: start')
    result = []
    users_to_notify = []
    try:
        result = UpdateNxversiosDB(f"{get_script_dir()}/nx-versions")
    except:
        jobqueue_error_handler(context, traceback.format_exc(), 'nx-versions -> callback_nxversions -> UpdateNxversiosDB')

    
    # result = [{'_id': '0100000000010000', 'version_number': '262144', 'update_id': '0100000000010800'}, 
    #           {'_id': '0100EB6005E90000', 'version_number': '24112', 'update_id': '0100EB6005E90800'}]
    
    if len(result) > 0:
        logging.info(f'JobQueue [nx-versions]: calling user notification system')
        
        result_ids = [x['_id'] for x in result]
        result_index_id = {x['_id']:x for x in result}
        users_to_notify = db.search('user_data', {'watched_games': { '$in': result_ids } })
        
        logging.info(f'JobQueue [nx-versions]: {len(users_to_notify)} users to notify')

        if len(users_to_notify) > 0:
            #load info about all games from titledb
            games_data = [db.find('titledb', {"_id":x['_id']}) for x in result]
            titledb = {x['_id']:x for x in games_data if x is not None}
            
            for user_info in users_to_notify:
                user_id = user_info['_id']
                logging.info(f'JobQueue [nx-versions]: trying to notify {user_id}')
                
                #match games user is watching against games in the result list
                notify_user_ids = list(set(user_info['watched_games']).intersection(result_ids))
                
                reply_text = ''
                for index, base_id in enumerate(notify_user_ids):
                    
                    try:
                        game_dict = titledb[base_id]
                    except:
                        break

                    reply_text += f"\n\n<b>Name:</b> {test_dict_key(game_dict, 'name')}\n<b>Base Game ID:</b> <code>{test_dict_key(game_dict, '_id')}</code>\n<b>Update ID:</b> <code>{test_dict_key(game_dict, 'updateId')}</code>\n<b>Latest Version:</b> v{test_dict_key(game_dict, 'latestVersion')}\n<b>Region:</b> {test_dict_key(game_dict, 'region')}"

                sleep(3) #time between each user notification to avoid hitting API limits
                messages_list = split_message(reply_text, '📺<b>New updates available</b>')
                
                for message in messages_list:
                    context.bot.send_message(chat_id=int(user_id), 
                                            text=message,
                                            parse_mode=ParseMode.HTML)#TODO split message in case it passes telegram character limit
                                        
                logging.info(f'JobQueue [nx-versions]: notified {user_id}')
                
    
    logging.info(f'JobQueue [nx-versions]: end') 
    
# main
def main():
    #create db folder
    updater = Updater(token=TELEGRAM_TOKEN, use_context=True)
    job = updater.job_queue

    dispatcher = updater.dispatcher
    
    #start command
    #TODO respond with a help text
    #TODO implement broadcast for adms
    # dispatcher.add_handler(
    #     CommandHandler('broad', broadcast)
    # )
    
    dispatcher.add_handler(
        CommandHandler('start', start)
    )
    
    dispatcher.add_handler(
        CommandHandler('stop', stop)
    )


    #add, remove and list games to user database
    #TODO add handler to return information to the adm about number of users and database sizes and stats
    dispatcher.add_handler(
        CommandHandler('a', add_games)
    )

    dispatcher.add_handler(
        CommandHandler('r', rm_games)
    )

    dispatcher.add_handler(
        CommandHandler('l', list_watched)
    )
    
    dispatcher.add_handler(
        CommandHandler('s', search)
    ) #TODO deactivate in case SEARCH_LIMIT == 0

    dispatcher.add_handler(
        CommandHandler('settings', settings)
    )
    
    #unknown command
    dispatcher.add_handler(
        MessageHandler(Filters.command, unknown)
    )

    dispatcher.add_handler(
        CallbackQueryHandler(button)
        )

    
    # log all errors
    dispatcher.add_error_handler(error_handler)

    # add JobQueue for nx-versions and titledb
    # job_titledb = job.run_repeating(callback_titledb, interval=var.TITLEDB_CHECKING_INTERVAL, first=0)
    # job_nxversions = job.run_repeating(callback_nxversions, interval=var.VERSION_CHECKING_INTERVAL, first=0)
    
    updater.start_polling()

    updater.idle()

if __name__ == '__main__':
    print("press CTRL + C to cancel.")
    main()