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
import re
import git
import datetime
from json import load
from os.path import isfile, isdir
from distutils import util


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

def validate_search_limit(limit: str):
    if limit in [None, ''] or limit.isdigit() is False:
        return 10
    else:
        return int(limit)

def str_to_alphanum(string: str):
    r = re.compile(r'[^\s\w_]+', re.UNICODE)
    return r.sub('', string)

def is_git_repo(path):
    if isdir(path):
        try:
            _ = git.Repo(path).git_dir
            return True
        except git.exc.InvalidGitRepositoryError:
            return False
    else:
        return False
    
def split_message(message, title, split_char='\n\n', max_char=3900):
    #split message
    message = message.split(split_char)
    messages_list = []
    message_str = ''
    for index, line in enumerate(message):
        if len(message_str) + len(title) + len(line) < max_char:
            if index == 0:
                message_str += f'{line}'
            else:
                message_str += f'{split_char}{line}'
            if index+1 == len(message):
                messages_list.append(message_str)
        else:
            messages_list.append(message_str)
            message_str = f'{split_char}{line}'
    #add message title an numbering
    return_list = []
    if len(messages_list) == 1:
        return_list.append(f'{title}{messages_list[0]}')
    else:
        for index, line in enumerate(messages_list):
            return_list.append(f'{title} [{index+1}\{len(messages_list)}]{line}')
    return return_list

def test_dict_key(dict, key):
    if key not in dict:
        if key == 'latestVersion' and key not in dict:
            return '0'
        elif key == 'name' and key not in dict:
            return 'Unknown Name'
        else:
            return 'Unknown'
    else:
        if key == 'updateId' and 'latestVersion' not in dict:
            return 'None'
        else:
            return dict[key]

#TODO remove db_folder
def UpdateTitleDB(db_folder, repo_folder, collection_name='titledb'):
    """function is used to build and interact with titledb database
    it's suposed to run every day, but the interval can be tweaked at variables.py"""
    repo_file = f'{repo_folder}/titles.US.en.json'
    
    logging.info(f'UPDATE {collection_name.upper()}: job started!')

    def UpdateDB(first_run):
        """adds a the list of dirs to the current database"""
        
        def get_titledb():
            #load json file
            with open(f'{repo_folder}/titles.US.en.json') as file:
                titledb_json = load(file)
                
            #refactor titledb to mango format
            res = []
            for game_id in titledb_json:
                game_dict = titledb_json[game_id]

                try:
                    game_dict['_id'] = game_dict.pop('id')
                except KeyError:
                    game_dict['_id'] = game_id
                
                insertion = {
                    "_id": None,
                    "name": None,
                    "version": None,
                    "region": None,
                    "releaseDate": None,
                    "rating": None,
                    "publisher": None,
                    "description": None,
                    "size": None,
                    "rank": None
                }
                
                if first_run is True:
                    insertion["insertionDate"] = datetime.datetime.utcnow()
                    
                insertion.update(game_dict)
                
                #update insert with game_dict
                res.append(insertion)
                
            return res
            
        if first_run is True:
            logging.info(f'UPDATE {collection_name.upper()} [first_run]: MangoDB is empty, populating it')
            # add everything to mongo
            db.add_multiple_to_collection(collection_name, get_titledb())
            
            return True
        else:
            #use bulk insert to insert new games into the database
            ret = db.update_multiple_documents(collection_name, get_titledb())
            
            return ret.bulk_api_result['nUpserted'] > 0 or ret.bulk_api_result['nModified'] > 0
                    
    #check if titledb repository is present, if not, clone it
    rescan_db = False
    if isfile(repo_file) is False or is_git_repo(repo_folder) is False or isdir(repo_folder) is False:
        #remove broken folder
        try:
            shutil.rmtree(repo_folder)
        except:
            pass
        
        logging.info(f'UPDATE {collection_name.upper()} [GIT]: cloning titledb to {repo_folder}')
        git.Repo.clone_from(var.TITLEDB, repo_folder)
        logging.info(f'UPDATE {collection_name.upper()} [GIT]: cloned')
        rescan_db = True
    
    #check if present repository is behind master
    repo = git.Repo(repo_folder)
    repo.remotes.origin.fetch() 
    commits_behind = len(list(repo.iter_commits('master..origin/master')))
    
    if commits_behind != 0:
        #means it's behind, pull from remote
        logging.info(f"UPDATE {collection_name.upper()} [GIT]: changes on titledb's remote detected, pulling changes!")
        repo.remotes.origin.pull() # pulls the changes from github
        rescan_db = True
    else:
        logging.info(f"UPDATE {collection_name.upper()} [GIT]: no changes on titledb's remote detected.")
    
    #determine if it's first run
    first_run = collection_name not in db.list_collections()
    
    # rescan_db = True #REMOVER APENAS DEBUG
    # first_run = False #REMOVER APENAS DEBUG
    result = False
    if first_run is True or rescan_db is True:
        #update entire database
        logging.info(f'UPDATE {collection_name.upper()}: adding titledb to MongoDB')
        result = UpdateDB(first_run)
        
    return result


def UpdateNxversiosDB(repo_folder, collection_name='titledb'): 
    """function is used to build and interact with nx-versions database
    it's suposed to run every hour, but the interval can be tweaked at variables.py"""
    
    logging.info(f'UPDATE {collection_name.upper()}: job started!')
    
    # functions
    def AddtoDB(list_versions, first_run):
        """adds a the list of dirs to the current database"""
        
        if first_run is True:
            logging.info(f'UPDATE {collection_name.upper()} [first_run]: MangoDB is empty, populating it')
            db.add_multiple_to_collection(collection_name, list_versions)
            #return the entire database
            return db.return_collection(collection_name)
        else:
            return_list = []
            
            for game_dict in list_versions:
                game_id = game_dict['_id']
                new_game_version = game_dict["latestVersion"]
                #pop date
                if 'insertionDate' in game_dict:
                    game_dict.pop('insertionDate')
                    
                res = db.update_document(collection_name, {'_id':game_id}, game_dict)
                
                if res.raw_result['nModified'] > 0 or 'upserted' in res.raw_result: #updated on Mongo
                    if res.raw_result['nModified'] > 0:
                        logging.info(f'UPDATE {collection_name.upper()} [{game_id}]: updated to version v{new_game_version}')
                    else:
                        logging.info(f'UPDATE {collection_name.upper()} [{game_id}]: got first update to v{new_game_version}')
                    
                    return_list.append(game_dict)
            
            return return_list
                
    def VersionsToList(versions_text_string):
        return_list = []
        for i in versions_text_string.split("\n"):         
            if i.startswith("id|") or "|" not in i:
                pass
            else:
                update_id, update_version_latest = i.split("|")
                base_id = update_id[:-3]+"000"
                if next((item for item in return_list if item['_id'] == base_id), None) is None:
                    if update_id.endswith("800"):
                        return_list.append({"_id": base_id,
                                            "updateId":update_id,
                                            "latestVersion": update_version_latest,
                                            "insertionDate": datetime.datetime.utcnow()
                                            })
        return return_list
    
    # check if nx-versions repository is present, if not, clone it
    rescan_db = False
    if isfile(repo_folder+"/versions.txt") is False or is_git_repo(repo_folder) is False or isdir(repo_folder) is False:
        #remove broken folder
        try:
            shutil.rmtree(repo_folder)
        except:
            pass
        
        logging.info(f'UPDATE {collection_name.upper()} [GIT]: cloning nx-versions to {repo_folder}')
        
        git.Repo.clone_from(var.NXVERSION, repo_folder)
        logging.info(f'UPDATE {collection_name.upper()} [GIT]: cloned')
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
    print('rescan_db: ', rescan_db)
    
    # rescan_db = True #REMOVER APENAS DEBUG
    # first_run = True #REMOVER APENAS DEBUG
    
    #if there's no db file yet, parse entire versions.txt file
    #TODO don't notify users if it's first clone?
    result=[]
    if first_run is True or rescan_db is True:
        print(11111111111111)
        #update entire database
        nx_versions_file = False
        if isfile(repo_folder+"/versions.txt") is True:
            with open(repo_folder+"/versions.txt", 'r') as file:
                nx_versions_file = file.read()
                
            if nx_versions_file is not False:
                result = AddtoDB(VersionsToList(nx_versions_file), first_run)
                # logging.info(f'UPDATE {collection_name.upper()}: {len(result)} updates found in this run')
            else:
                logging.info(f'UPDATE {collection_name.upper()} [ERROR]: no version file located at: {repo_folder+"/versions.txt"}')
        else:
            logging.info(f'UPDATE {collection_name.upper()} [ERROR]: no version file located at: {repo_folder+"/versions.txt"}')

    return result
