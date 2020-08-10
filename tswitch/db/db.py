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
import os, sys
import inspect
import datetime
from pymongo import MongoClient
from dotenv import load_dotenv

def get_script_dir(follow_symlinks=True):
    """function used to get the directory the script is located"""
    if getattr(sys, 'frozen', False): # py2exe, PyInstaller, cx_Freeze
        path = os.path.abspath(sys.executable)
    else:
        path = inspect.getabsfile(get_script_dir)
    if follow_symlinks:
        path = os.path.realpath(path)
    return os.path.dirname(path)

env_location = f'{os.path.dirname(os.path.dirname(get_script_dir()))}/.env'
if os.path.isfile(env_location):
    #load from .env
    load_dotenv(dotenv_path=env_location)

MONGO_URL, MONGO_PORT, MONGO_DBNAME = os.getenv("MONGO_URL"), os.getenv("MONGO_PORT"), os.getenv("MONGO_DBNAME")

if MONGO_DBNAME in [None, '']:
    MONGO_DBNAME = 'telegram_switch_bot'
    
    
client = MongoClient(MONGO_URL, int(MONGO_PORT))
data = client[MONGO_DBNAME]


def find(collection: str, search_dict: dict):
    return data[collection].find_one(search_dict)

def return_collection(collection: str):
    return list(data[collection].find())

def is_id_on_db(collection: str, search_dict: dict):
    if data[collection].find_one(search_dict) == None:
        return False
    else:
        return True

def add_to_collection(collection: str, new_dict: dict):
    #add date of last interation
    new_dict['last_interaction'] = datetime.datetime.now()
    return data[collection].insert_one(new_dict).inserted_id

def rm_from_collection(collection: str, user_id: str):
    return data[collection].delete_one({'_id':user_id})

def update_collection(collection: str, new_dict: dict):
    #remove id from update_dict
    update_dict = {x:new_dict[x] for x in new_dict if x != '_id'}
    #add date of last interation
    update_dict['last_interaction'] = datetime.datetime.now()
    return data[collection].update_one({'_id': new_dict['_id']}, {'$set': update_dict})
    
def list_collections():
    return data.list_collection_names()
