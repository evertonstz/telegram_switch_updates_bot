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
import urllib.parse
from pymongo import MongoClient, UpdateOne
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
MONGO_USERNAME, MONGO_PASS = os.getenv("MONGO_USERNAME"), os.getenv("MONGO_PASS")  

if MONGO_DBNAME in [None, '']:
    MONGO_DBNAME = 'telegram_switch_bot'

if MONGO_USERNAME in [None, ""] or MONGO_PASS in [None, ""]:
    client = MongoClient(MONGO_URL, int(MONGO_PORT))
else:
    username = urllib.parse.quote_plus(MONGO_USERNAME)
    password = urllib.parse.quote_plus(MONGO_PASS)
    
    client = MongoClient(f'mongodb://{username}:{password}@{MONGO_URL}:{MONGO_PORT}/')
    

data = client[MONGO_DBNAME]


def find(collection: str, search_dict: dict):
    return data[collection].find_one(search_dict)

def search(collection: str, search_dict: dict, order_key=None):
    found = list(data[collection].find(search_dict))
    if order_key != None:
        return sorted(found, key=lambda a: (a[order_key] in ['', None], a[order_key]))
    else:
        return found

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

def add_multiple_to_collection(collection: str, list_of_documents: list):
    return data[collection].insert_many(list_of_documents)

def rm_from_collection(collection: str, user_id: str):
    return data[collection].delete_one({'_id':user_id})

def update_multiple_documents(collection: str, new_documents: list, upsert=True):
    list_of_writes = []
    for document in new_documents:
        list_of_writes.append(UpdateOne({'_id': document['_id']}, 
                                        {'$setOnInsert': {'insertionDate':datetime.datetime.utcnow()},
                                        '$set': document
                                        },
                                        upsert=True
                                        )
                            )

    return data[collection].bulk_write(list_of_writes)
    

def update_document(collection: str, query: dict, new_document: dict, upsert=True):
    res = data[collection].update_one(query, 
                                       {'$setOnInsert': {'insertionDate':datetime.datetime.utcnow()},
                                        '$set': new_document
                                        },
                                       upsert=upsert
                                       )
    return res
    

def update_collection(collection: str, new_dict: dict):
    #remove id from update_dict
    update_dict = {x:new_dict[x] for x in new_dict if x != '_id'}
    #add date of last interation
    update_dict['last_interaction'] = datetime.datetime.now()
    return data[collection].update_one({'_id': new_dict['_id']}, {'$set': update_dict})

def touch_user(collection: str, user_id: str):
        user_db = {"_id":user_id, 
                   'watched_games':[], 
                   'options':{'mute':0,
                              'notify_all':0
                              }
                   }
        res = add_to_collection(collection, user_db)
        if res == user_id:
            return user_db
        else:
            raise Exception('NotAddedToMongo')

def list_collections():
    return data.list_collection_names()
