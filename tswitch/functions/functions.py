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
import sys
import inspect
import shutil
import logging
import pickle
import distutils
from json import load
from os.path import isfile, isdir
from distutils import util

from sqlitedict import SqliteDict
import git

import tswitch.variables as var
import tswitch.db as db

#optional dependencies
try: 
    from notify_run import Notify
except ImportError: 
    Notify = None
    
try: 
    from pushover import Client
except ImportError: 
    Client = None
    
try: 
    from pushbullet import Pushbullet
except ImportError: 
    Pushbullet = None

##FUNCTIONS##
def create_folder(location):
    """function used to create folders in the file system"""
    try:
        os.makedirs(location)
        return True
    except:
        return False

def str_to_bool(string: str):
    if string != None:
        try:
            return bool(distutils.util.strtobool(string))
        except ValueError:
            return False
    else:
        return False
    
def validate_pushover_debug(api_key: str, user_key: str, activated: bool):
    if user_key in [None, ''] or Client == None or api_key in [None, '']:
        return (None, None, False)
    else:
        return (api_key, user_key, activated)
    
def validate_telegram_debug(adm_user_id: str, activated: bool):
    if adm_user_id in [None, '']:
        return (None, False)
    else:
        return (adm_user_id, activated)

def validate_pushbullet_debug(acess_token: str, devices: str, activated: bool):
    if acess_token in [None, '']:
        return (None, [], False)
    else:
        devices_ret = []
        if devices not in [None, '']:                  
              devices_ret = [x.strip() for x in devices.split(',') if x.strip() != '']
              
        return (acess_token, devices_ret, activated)
    
def validate_notifyrun_debug(activated: bool):
    if Notify == False:
        return False
    else:
        return activated

def validate_unlimited_users(users: str):
    if users == None or False in [x.strip().isnumeric() for x in users.split(',') if x.strip() != '']:
        return []
    elif users != '':
        return [x.strip() for x in users.split(',') if x.strip() != '']
    else:
        return []


def is_git_repo(path):
    if isdir(path):
        try:
            _ = git.Repo(path).git_dir
            return True
        except git.exc.InvalidGitRepositoryError:
            return False
    else:
        return False

def LoadTitleDB(db_folder, table_name='titledb'):
    """load titledb from SqliteDict"""
    db_location = f"{db_folder}/titledb_database.db"
    db = {}
    if isfile(db_location):
        with SqliteDict(db_location, autocommit=False) as database:
            db = database[table_name]
    
    return(db)
        
#TODO remove db_folder
def UpdateTitleDB(db_folder, repo_folder, collection_name='titledb'):
    """function is used to build and interact with titledb database
    it's suposed to run every day, but the interval can be tweaked at variables.py"""
    # db_location = f"{db_folder}/titledb_database.db"
    repo_file = f'{repo_folder}/titles.US.en.json'
    
    logging.info(f'UPDATE TITLEDB: job started!')

    def UpdateDB():
        #TODO add option to change language
        """adds a the list of dirs to the current database
        """
        #load json file
        with open(f'{repo_folder}/titles.US.en.json') as file:
            titledb_json = load(file)
        
        for id in titledb_json:
            game_dict = titledb_json[id]
            if 'id' in game_dict:
                game_dict.pop('id')
            
            mongo_data = db.find(collection_name, {"_id":id})
            if mongo_data is not None:
                if 'last_interaction' in mongo_data:
                    mong_data_last_interaction = mongo_data['last_interaction']
                    mongo_data.pop('last_interaction')
                else:
                    mong_data_last_interaction = None
                
            insertion = {
                "_id": id,
                "name": "",
                "version": "",
                "region": "",
                "releaseDate": "",
                "rating": "",
                "publisher": "",
                "description": "",
                "size": "",
                "rank": ""
            }
            
            #update insertions game_dict
            insertion.update(game_dict)
            
            #check if insertion and mongo_data are the same
            if insertion != mongo_data:
                if mongo_data is not None:
                    #update on mongo
                    logging.info(f'UPDATE TITLEDB: {id}, information updated on mongo')
                    db.update_collection(collection_name, insertion)
                else:
                    #add to mongo
                    # logging.info(f'UPDATE TITLEDB: {id} added to mongo')
                    db.add_to_collection(collection_name, insertion)

    #check if titledb repository is present, if not, clone it
    rescan_db = False
    if isfile(repo_file) is False or is_git_repo(repo_folder) is False or isdir(repo_folder) is False:
        #remove broken folder
        try:
            shutil.rmtree(repo_folder)
        except:
            pass
        
        logging.info(f'UPDATE TITLEDB [GIT]: cloning titledb to {repo_folder}')
        git.Repo.clone_from(var.TITLEDB, repo_folder)
        logging.info(f'UPDATE TITLEDB [GIT]: cloned')
        rescan_db = True
    
    #check if present repository is behind master
    repo = git.Repo(repo_folder)
    repo.remotes.origin.fetch() 
    commits_behind = len(list(repo.iter_commits('master..origin/master')))
    
    
    if commits_behind != 0:
        #means it's behind, pull from remote
        logging.info(f"UPDATE TITLEDB [GIT]: changes on titledb's remote detected, pulling changes!")
        repo.remotes.origin.pull()
        rescan_db = True
    else:
        logging.info(f"UPDATE TITLEDB [GIT]: no changes on titledb's remote detected.")

    
    #making database
    #it'll parse the entire titledb_database.db every time a update is detected
    result = False
    #determine if it's first run
    first_run = collection_name not in db.list_collections()
    
    if first_run is True or rescan_db is True:
        #update entire database
        logging.info(f'UPDATE TITLEDB: adding titledb to MongoDB')
        UpdateDB()
        result = True
        
    return result


def UpdateNxversiosDB(db_folder, repo_folder, collection_name='versions'): 
    """function is used to build and interact with nx-versions database
    it's suposed to run every hour, but the interval can be tweaked at variables.py"""

    db_location = f"{db_folder}/versions_database.db"
    
    logging.info(f'UPDATE VERSIONS: job started!')
    
    # functions
    def AddtoDB(list_versions):
        """adds a the list of dirs to the current database
        this is a example: list = [{"Base ID":"0100B5B00EF38800", "Update Name":"v131072", "Update ID":"0100B5B00EF38800"}]
        """
        #load json file
        added_to_database = []
        for game_dict in list_versions:
            id = game_dict["_id"]
            mongo_data = db.find(collection_name, {"_id":id})
            if mongo_data is not None:
                if 'last_interaction' in mongo_data:
                    mong_data_last_interaction = mongo_data['last_interaction']
                    mongo_data.pop('last_interaction')
                else:
                    mong_data_last_interaction = None
            
            #check if game_dict and mongo_data are the same
            if game_dict != mongo_data:
                if mongo_data is not None:
                    #update on mongo
                    logging.info(f'UPDATE VERSIONS: {id}, information updated on mongo')
                    db.update_collection(collection_name, game_dict)
                    added_to_database.append(game_dict)
                else:
                    #add to mongo
                    logging.info(f'UPDATE VERSIONS: {id} added to mongo')
                    db.add_to_collection(collection_name, game_dict)
                    added_to_database.append(game_dict)
        return added_to_database
                
    def VersionsToList(versions_text_string):
        return_list = []

        for i in versions_text_string.split("\n"):
            try:
                if i.startswith("id|") or "|" not in i:
                    raise()
                update_id, update_version_latest = i.split("|")
                base_id = update_id[:-3]+"000"
                if next((item for item in return_list if item['_id'] == base_id), None) is None:
                    if update_id.endswith("800"):
                        return_list.append({"_id":base_id,"version_number":update_version_latest, "update_id":update_id})
            except:
                pass
        return return_list

    #check if nx-versions repository is present, if not, clone it
    rescan_db = False
    if isfile(repo_folder+"/versions.txt") is False or is_git_repo(repo_folder) is False or isdir(repo_folder) is False:
        #remove broken folder
        try:
            shutil.rmtree(repo_folder)
        except:
            pass
        
        logging.info(f'UPDATE VERSIONS [GIT]: cloning nx-versions to {repo_folder}')
        
        git.Repo.clone_from(var.NXVERSION, repo_folder)
        logging.info(f'UPDATE VERSIONS [GIT]: cloned')
        rescan_db = True
    
    #check if present repository is behind master
    repo = git.Repo(repo_folder)
    repo.remotes.origin.fetch() 
    commits_behind = len(list(repo.iter_commits('master..origin/master')))
    
    
    if commits_behind != 0:
        #means it's behind, pull from remote
        logging.info(f"UPDATE VERSIONS [GIT]: changes on nx-versions' remote detected, pulling changes!")
        repo.remotes.origin.pull()
        rescan_db = True
    else:
        logging.info(f"UPDATE VERSIONS [GIT]: no changes on nx-versions' remote detected.")

    
    #making database
    #determine if it's first run
    first_run = collection_name not in db.list_collections()
    first_run = True
    #if there's no db file yet, parse entire versions.txt file
    #TODO don't notify users if it's first clone?
    result=[]
    if first_run is True or rescan_db is True:
        #update entire database
        nx_versions_file = False
        if isfile(repo_folder+"/versions.txt") is True:
            with open(repo_folder+"/versions.txt", 'r') as file:
                nx_versions_file = file.read()
                
            if nx_versions_file is not False:
                result = AddtoDB(VersionsToList(nx_versions_file))
                logging.info(f'UPDATE VERSIONS: {len(result)} updates found in this run')
            else:
                logging.info(f'UPDATE VERSIONS [ERROR]: no version file located at: {repo_folder+"/versions.txt"}')
        else:
            logging.info(f'UPDATE VERSIONS [ERROR]: no version file located at: {repo_folder+"/versions.txt"}')

    #result isused by the bot to know if runing the check cicle for user is necessary or not
    return result


def NotifyUsersUpdate(update_list):
    """used to match new updates with ids users are currently monitoring"""
    
    notify_dict = {}
    user_database = db.return_collection('user_data')
    #TODO test what happen if there's no user data in the database
    
    for user_info in user_database:
        user_id = user_info["_id"]
        watching_list = []       
        user_watching = user_info['watched_games']
        for i in update_list:
            if i['_id'] in user_watching or i['update_id'] in user_watching:
                watching_list.append(i)
        if len(watching_list) > 0:
            notify_dict[user_id] = watching_list
                
    return notify_dict