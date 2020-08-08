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
#IMPORTS
import traceback
import logging
from time import sleep
from dotenv import load_dotenv

import tswitch.variables as var
from tswitch.functions import *

# # external
from telegram.ext import CommandHandler, Filters, MessageHandler, Updater, PicklePersistence, CallbackContext
from telegram import ParseMode, Update
# import telegram

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',level=logging.INFO)
logger = logging.getLogger(__name__)

#importing and testing env variables
load_dotenv()    

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


def get_script_dir(follow_symlinks=True):
    """function used to get the directory the script is located"""
    if getattr(sys, 'frozen', False): # py2exe, PyInstaller, cx_Freeze
        path = os.path.abspath(sys.executable)
    else:
        path = inspect.getabsfile(get_script_dir)
    if follow_symlinks:
        path = os.path.realpath(path)
    return os.path.dirname(path)

def get_bot_data(context: CallbackContext):
    bot_data_dict = context.bot_data
    return bot_data_dict

def get_user_id(update: Update):
    """get user id from update"""
    user_id = str(update.message.from_user.id)      
    return user_id

def parse_args_from_value(value):
    """parse arguments from value"""
    #TODO more test is needed, maybe look for these IDs in the database to confirm a game exist
    value = value.partition(' ')[2].replace('\n',' ')
    value_list = []
    for i in [x for x in value.split(' ') if x != '']:
        if len(i) == 16 and i.endswith('800'):
            value_list.append(f'{i[:-3]}000')
        else:
             value_list.append(i)
    return value_list

#telegram functions
def unknown(update: Update, context: CallbackContext):
    response_message = "Unknown command..."
    update.message.reply_text(response_message)

    
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
            
            # blacking user's dictionary
            try:
                context.bot_data.pop(user_id)
            except KeyError:
                pass
                
            logging.info(f'USER REQUEST {user_id}: user removed from database.')
            update.message.reply_text("<b>Done!</b>\nYour data was removed and the bot won't notify you anymore!", 
                                  parse_mode=ParseMode.HTML)


def start(update: Update, context: CallbackContext):
    #TODO make user options here, including exit and delete options
    update.message.reply_text(var.START_MESSAGE,
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
                

def list_watched(update: Update, context: CallbackContext):
    """used to return the current watch list to the user"""
    user_id = get_user_id(update)
    value = update.message.text.partition(' ')[2]

    # Load old values
    try:
        stored_game_ids = get_bot_data(context)[user_id]
    except KeyError:
        stored_game_ids = []
    
    logging.info(f'USER REQUEST {user_id}: game ids user already have saved {stored_game_ids}.')

    #printing results
    if len(stored_game_ids) > 0:
        reply_text = f"📺<b>The following game IDs are in your watch list</b>"
        for i in stored_game_ids:
            reply_text += f"\n<code>{i}</code>"
    else:
        logging.info(f'USER REQUEST {user_id}: user have no games in his watching list.')
        reply_text = f"📺<b>No games found</b>\nSeems like you didn't add any games to your watch list, try adding them with the /a command"
    
    if len(value) != 0:
        logging.info(f'USER REQUEST {user_id}: user called /l but provided arguments.')
        reply_text += "\n\n<i>PSA: You provided arguments to /l and this is not needed, so next time just use /l</i>"
    
    update.message.reply_text(reply_text,
                              parse_mode=ParseMode.HTML)

                               
def rm_games(update: Update, context: CallbackContext):
    """used to remove games from users watch list"""
    user_id = get_user_id(update)

    #filter the user values for possible valid game IDs
    value_list = parse_args_from_value(update.message.text)
    
    logging.info(f'USER REQUEST {user_id}: user databse interaction: rm_games, provided IDs {value_list}.')
    
    if len(value_list) == 0:
        logging.info(f'USER REQUEST {user_id}: user called /r but provided no arguments.')
        update.message.reply_text("📺<b>You didn't enter any Game ID</b>\nTo use /r you must provide at least one Game ID, multiple IDs must to be separated by a space\n\nExample: <code>/a 01000320000CC000 0100DA900B67A000</code>",
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
    try:
        stored_game_ids = get_bot_data(context)[user_id]
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
    # Store dicts on bot_data
    context.bot_data[user_id] = sorted(game_ids)

    #making reply string
    reply_text = '📺<b>The following procedures were made</b>'
    for i in reply_dict:
        reply_text += f"\n{reply_dict[i]}: <code>{i}</code>"
        
    if 'Removed from watch list' in reply_text:
        reply_text += "\n\n<i>You won't be getting notifications for</i> 🟢 <i>anymore!</i>"
    
    update.message.reply_text(reply_text,
                            parse_mode=ParseMode.HTML)


def add_games(update: Update, context: CallbackContext):
    """used to add games to user database, calls for AddToUserDB()"""
    user_id = get_user_id(update)
    #filter the user values for possible valid game IDs
    value_list = parse_args_from_value(update.message.text)
             
    logging.info(f'USER REQUEST {user_id}: user databse interaction: add_games, provided IDs {value_list}.')
    
    if len(value_list) == 0:
        logging.info(f'USER REQUEST {user_id}: user called /a but provided no arguments.')
        update.message.reply_text("📺<b>You didn't enter any Game ID</b>\nTo use /a you must provide at least one Game ID, multiple IDs must to be separated by a space\n\nExample: <code>/a 01000320000CC000 0100DA900B67A000</code>",
                                  parse_mode=ParseMode.HTML)
        return
    if len(value_list) > var.USER_LIMIT and user_id not in UNLIMITED_USERS:
        logging.info(f'USER REQUEST {user_id}: user gave too many IDS: {len(value_list)}')
        update.message.reply_text(f"📺<b>You entered too many Game IDs</b>\nThis bot can only monitor {var.USER_LIMIT} IDs per user.",
                                  parse_mode=ParseMode.HTML)
        return      
    
    
    reply_dict = {x:'🔴Invalid Game ID' for x in value_list}
    
    valid_game_ids = list(set([x for x in value_list if x.isalnum() and len(x) == 16 and x.endswith('000')]))
    logging.info(f'USER REQUEST {user_id}: valid game ids provided by user {valid_game_ids}.')
    
    #adding valid ids to reply dictionary
    for i in valid_game_ids:
        reply_dict[i] = '🟢Added on watch list'
    
    # Load old values
    try:
        stored_game_ids = get_bot_data(context)[user_id]
    except KeyError:
        stored_game_ids = []

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
    # Store dicts on bot_data
    context.bot_data[user_id] = sorted(game_ids)

    #making reply string
    reply_text = '📺<b>The following procedures were made</b>'
    for i in reply_dict:
        reply_text += f"\n{reply_dict[i]}: <code>{i}</code>"
    
    if 'Added on watch list' in reply_text:
        reply_text += "\n\n<i>I'll let you know when</i> 🟢 <i>get new updates!</i>"
        
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
    
    message = f"An exception was raised while handling an update\nUser ID: {user_id}\n\n{tb}"

    # Finally, send the message
    PushNotif(context, message, 'Bug report', -1)
    
    # leting the user know
    try:
        if user_id != TELEGRAM_ADM_CHATID:
            context.bot.send_message(chat_id=user_id, text="Oopsie, something went wrong on my side, I've reported the problem to my owner and he'll deal with it as soon as possible.")
            logging.info(f'ERROR HANDLER: letting the user know there was a problem')
    except Exception as e:
        logging.info(f'ERROR HANDLER: failed to message the user: {e}')

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
    users_to_notify = {}
    try:
        result = UpdateNxversiosDB(f"{get_script_dir()}/database", f"{get_script_dir()}/nx-versions")
    except:
        jobqueue_error_handler(context, traceback.format_exc(), 'nx-versions -> callback_nxversions -> UpdateNxversiosDB')

    # result = [{'Base ID': '01000040098E4000', 'Update Name': '01000040098E4800', 'Update ID': '262140'}, {'Base ID': '0100000000010000', 'Update Name': '0100000000010800', 'Update ID': '65533040'}, {'Base ID': '010000100FB62000', 'Update Name': '010000100FB62800', 'Update ID': '196603'}, {'Base ID': '010000100FB62000', 'Update Name': '010000100FB62800', 'Update ID': '6553304050'}, {'Base ID': '010000300C79C000', 'Update Name': '010000300C79C800', 'Update ID': '3932304050'}, {'Base ID': '010000400F582000', 'Update Name': '010000400F582800', 'Update ID': '6553304050'}, {'Base ID': '010000500B9F4000', 'Update Name': '010000500B9F4800', 'Update ID': '6553304050'}, {'Base ID': '010000500DB50000', 'Update Name': '010000500DB50800', 'Update ID': '26214304050'}, {'Base ID': '01000060085D2000', 'Update Name': '01000060085D2800', 'Update ID': '1310304050'}]
    
    if len(result) > 0:
        logging.info(f'JobQueue [nx-versions]: calling NotifyUsersUpdate')
        users_to_notify = NotifyUsersUpdate(result, get_bot_data(context))
        logging.info(f'JobQueue [nx-versions]: {len(users_to_notify)} users to notify - Notification Dict {users_to_notify}')

        if len(users_to_notify) > 0:
            #this means there are users to be notified, load titledb to get information
            titledb = LoadTitleDB(f"{get_script_dir()}/database")
            for user_id in users_to_notify:
                logging.info(f'JobQueue [nx-versions]: trying to notify {user_id}')
                reply_msg = '📺<b>New updates available</b>\n'
                for index, i in enumerate(users_to_notify[user_id]):
                    logging.info(f'JobQueue [nx-versions]: Userdd ID {user_id} - Update: {i}')
                    #making variables
                    base_id = i['Base ID']
                    
                    try:
                        game_name = titledb[base_id]['name']
                    except KeyError:
                        game_name = 'UNKNOWN TITLE'
                        
                    # game_publisher = titledb[base_id]['publisher']
                    game_update_id = i['Update Name']
                    game_update_version = i['Update ID']
                    if index > 0:
                        reply_msg += '\n\n'
                    reply_msg +=f"<b>{game_name}</b>\n<b>Base ID:</b> <code>{base_id}</code>\n<b>Update ID:</b> <code>{game_update_id}</code>\n<b>Latest version:</b> <code>v{game_update_version}</code>"
                
                sleep(2) #time between each user notification to avoid hitting API limits                 
                context.bot.send_message(chat_id=int(user_id), 
                                        text=reply_msg,
                                        parse_mode=ParseMode.HTML)
                                        
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
    job_titledb = job.run_repeating(callback_titledb, interval=var.TITLEDB_CHECKING_INTERVAL, first=0)
    
    updater.start_polling()

    updater.idle()

if __name__ == '__main__':
    print("press CTRL + C to cancel.") 
    main()