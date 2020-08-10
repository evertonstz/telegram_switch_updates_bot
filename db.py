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
import os
import datetime
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv() 
MONGO_URL, MONGO_PORT, MONGO_DBNAME = os.getenv("MONGO_URL"), os.getenv("MONGO_PORT"), os.getenv("MONGO_DBNAME")

if MONGO_DBNAME in [None, '']:
    MONGO_DBNAME = 'telegram_switch_bot'
    
client = MongoClient(MONGO_URL, int(MONGO_PORT))
data = client[MONGO_DBNAME]

def find(collection, search_dict):
    return data[collection].find_one(search_dict)

def add_to_collection(collection, new_dict):
    #add date of last interation
    new_dict['last_interaction'] = datetime.datetime.now()
    return data[collection].insert_one(new_dict).inserted_id

def rm_from_collection(collection, user_id):
    return data[collection].delete_one({'_id':user_id})

def update_collection(collection, new_dict):
    #remove id from update_dict
    update_dict = {x:new_dict[x] for x in new_dict if x != '_id'}
    #add date of last interation
    update_dict['last_interaction'] = datetime.datetime.now()
    return data[collection].update_one({'_id': new_dict['_id']}, {'$set': update_dict})
    
def list_collections():
    return data.list_collection_names()

# class Database:
#     def __init__(self, url, port:int):
#         self._client = MongoClient(url, int(port))
#         self._data = self._client['telegram_switch_bot']
#         # self._cursor = self._conn.cursor()

#     def __enter__(self):
#         return self

#     def __exit__(self, exc_type, exc_val, exc_tb):
#         return self
#         # self.commit()
#         # self.connection.close()

#     # @property
#     # def connection(self):
#     #     return self._client

#     # @property
#     # def db(self):
#     #     return self._db

#     # def commit(self):
#     #     self.connection.commit()

#     # def execute(self, sql, params=None):
#     #     self.cursor.execute(sql, params or ())
#     def find(self, collection, search_dict):
#         return self._data[collection].find_one(search_dict)
    
#     def add_to_collection(self, collection, new_dict):
#         #add date of last interation
#         new_dict['last_interaction'] = datetime.datetime.now()
#         return self._data[collection].insert_one(new_dict).inserted_id
    
#     def update_collection(self, collection, new_dict):
#         #remove id from update_dict
#         update_dict = {x:new_dict[x] for x in new_dict if x != '_id'}
#         #add date of last interation
#         update_dict['last_interaction'] = datetime.datetime.now()
#         return self._data[collection].update_one({'_id': new_dict['_id']}, {'$set': update_dict})
        
#     def list_collections(self):
#         return self._data.list_collection_names()

#     # def fetchone(self):
#     #     return self.cursor.fetchone()

#     # def query(self, sql, params=None):
#     #     self.cursor.execute(sql, params or ())
#     #     return self.fetchall()