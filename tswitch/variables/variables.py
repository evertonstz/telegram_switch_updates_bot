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
PUSHOVER_DEBUG = True
#Notify run https://notify.run/
NOTIFYRUN_DEBUG = False 