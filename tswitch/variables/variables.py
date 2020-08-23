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
VERSION = '0.0.4'

# Bot parameters
VERSION_CHECKING_INTERVAL = 43200  #this is the interval in seconds NXVERSION will be checked by the JobQueue 
TITLEDB_CHECKING_INTERVAL = 86400 #this is the interval in seconds TITLEDB will be checked by the JobQueue
USER_LIMIT = 50
# github databases
NXVERSION = 'https://github.com/16BitWonder/nx-versions'
TITLEDB = 'https://github.com/RebirthOfficial/titledb'
# NXVERSION = 'https://github.com/evertonstz/nx-versions'

#message shown by /start
START_MESSAGE = "<b>What this bot can do:</b>\n➕Subscribe to any valid Game ID provided by the user\n➕Notify the user when any of his games in the watching list gets an update\n➕Search for Game IDs by providing a game name\n➕Full metadata support\
                \n\n<b>Commands:</b> \
                \n/a - add a game to your watching list, games can only be added by their GAME ID, multiple IDs must to be separated by a space \
                \n\n/r - remove a game from your watching list, games can only be removed by their GAME ID, multiple IDs must to be separated by a space \
                \n\n/l - show the games that are in your watch list \
                \n\n/s - search for a Game IDs using a game's name or a keyword \
                \n\n/settings - bot settings \
                \n\n/stop - stop the bot and removes you from my database, <b>YOUR WATCH LIST WILL BE DELETED!</b> If you ever come back you'll need to reenter your Game IDs and settings \
                \n\nThis bot is open sourced under GNU/GLP3 and respects your privacy, it's made out of love for the Nintendo Switch system, liberty of software/hardware and necessity, the source code is available at: https://github.com/evertonstz/telegram_switch_updates_bot \
                \n\nIf you have any lasting problems with this software, fell free to open a github issue or contact me @evertonstz or on discord <i>Identify as chinese#6975</i>"
