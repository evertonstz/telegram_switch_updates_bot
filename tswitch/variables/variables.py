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

#TODO turn this file into a settings.ini ?
# Versioning
VERSION = '0.0.1'

# Bot parameters
VERSION_CHECKING_INTERVAL = 3600  #this is the interval in seconds NXVERSION will be checked by the JobQueue 
TITLEDB_CHECKING_INTERVAL = 86400 #this is the interval in seconds TITLEDB will be checked by the JobQueue
USER_LIMIT = 15
# github databases
NXVERSION = 'https://github.com/16BitWonder/nx-versions'
TITLEDB = 'https://github.com/blawar/titledb'
# NXVERSION = 'https://github.com/evertonstz/nx-versions'

# Debug Options 
# #TODO add more services
#Telegram
TELEGRAM_DEBUG = True
#Pushover https://pushover.net/
PUSHOVER_DEBUG = False
#Notify run https://notify.run/
NOTIFYRUN_DEBUG = False

#message shown by /start
START_MESSAGE = "Hi! This bot is still alpha and is kinda barebones and bugs are kinds expected. It checks every hour for new updates and every day for new titles in titleDB\n\n<b>What it can do:</b>\n➕Subscribe to any valid Game ID provided by the user\n➕Notify the user when any of his games in the watching list gets an update\
                \n\n<b>To be implemented:</b>\n➖Receive full game metadata (for now, you can only see the game and update IDs when the bot notifies you about a new update) \
                \n\n<b>Commands:</b> \
                \n/a - add a game to your watching list, games can only be added by their GAME ID, multiple IDs must to be separated by a space \
                \n\n/r - remove a game from your watching list, games can only be removed by their GAME ID, multiple IDs must to be separated by a space \
                \n\n/l - show the games that are in your watch list \
                \n\n/stop - stop the bot and removes you from my database, <b>YOUR WATCH LIST WILL BE DELETED!</b> If you ever come back you'll need to reenter your Game IDs \
                \n\n\n<i>PSA: The bot should be able to notify me automatically for most bugs and erros, but feel free to contact me at:\nTelegram: @evertonstz \nDiscord: Identify as chinese#6975</i>"
