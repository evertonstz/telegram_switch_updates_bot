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
from os.path import isfile, isdir

from sqlitedict import SqliteDict
import git

import tswitch.variables as var

##FUNCTIONS##

def create_folder(location):
    """function used to create folders in the file system"""
    try:
        os.makedirs(location)
        return True
    except:
        return False

def is_git_repo(path):
    if isdir(path):
        try:
            _ = git.Repo(path).git_dir
            return True
        except git.exc.InvalidGitRepositoryError:
            return False
    else:
        return False
        
# def AddToUserDB(root_folder, chat_id, ids_to_watch, operation):
#     """function is used to intect with users' database"""
#     db_folder = root_folder+"/database_users"
#     user_db_folder = db_folder+"/"+chat_id
#     user_db_file = user_db_folder+"/user_database.db"
#     ids_to_watch = [x[:-3]+"000" for x in ids_to_watch]
#     #creating folders
#     create_folder(db_folder)
#     create_folder(user_db_folder)
#     print(1/0)
#     logging.info(f'USER REQUEST {chat_id}: user databse interaction {operation}.')

#     def AddtoDB(list_ids, table_name="Watched IDs"):
#         """adds watched ids to user database based on his chat id"""
#         with SqliteDict(user_db_file, autocommit=False) as database:
#             if table_name not in database:
#                 database[table_name] = []

#             database_editable = database[table_name]

#             #iterate of id list
#             if operation == "add":
#                 #add matches
#                 for game_id in list_ids:
#                     if game_id not in database_editable:
#                         database_editable.append(game_id)
#                         logging.info(f'USER REQUEST {chat_id}: watched {game_id}')
#                     else:
#                         logging.info(f'USER REQUEST {chat_id}: already watching {game_id}, skipping.')
#             elif operation == "rm":
#                 #remove matches
#                 for game_id in list_ids:
#                     if game_id in database_editable:
#                         database_editable.remove(game_id)
#                         logging.info(f'USER REQUEST {chat_id}: removed {game_id}')
#                     else:       
#                         logging.info(f'USER REQUEST {chat_id}: user not watching {game_id}, skipping.')
#             elif operation == "list":
#                 return(database_editable)
#             #commit changes
#             database[table_name] = database_editable
#             database.commit()
#             return True
    
#     res = AddtoDB(ids_to_watch)
#     return res

def UpdateNxversiosDB(db_folder, nx_versions_folder): #TODO break away from bot file?
    """function is used to intect with database"""

    db_location = f"{db_folder}/versions_database.db"
    
    logging.info(f'UPDATE VERSIONS: job started!')
    # TODO get metadata fro titledb https://github.com/blawar/titledb
    
    # functions
    def AddtoDB(list_versions, table_name='versions'):
        """adds a the list of dirs to the current database
        this is a example: list = [{"Base ID":"0100B5B00EF38800", "Update Name":"v131072", "Update ID":"0100B5B00EF38800"}]
        """
        with SqliteDict(db_location, autocommit=False) as database:
            # check and create "table" in case it don't exist
            if table_name not in database:
                database[table_name] = []

            database_editable = database[table_name]
            added_to_database =[]
            
            # iterate over list
            for game_dict in list_versions:
                #TODO check if dict is valid

                #new information 
                base_id = game_dict["Base ID"]
                update_id = game_dict['Update ID']
                update_version_new = game_dict['Update Name']

                # check if keys part of the dict are already in the database 'GameID'
                checker = next((item for item in database_editable if item['Base ID'] == base_id), None)

                if checker is not None:
                    # this means there's already a entry, only update the last entry
                    if checker != game_dict: 
                        #this means there's a change
                        checker_index = database_editable.index(checker)
                        old_ver = database_editable[checker_index]["Update Name"]
                        database_editable[checker_index].update(game_dict)
                        added_to_database.append({"Base ID":base_id, "Update Name":update_id, "Update ID":update_version_new})
                        logging.info(f'UPDATE VERSIONS [{base_id}]: {old_ver} -> {update_version_new}')
                else:
                    # this means it's a new entry, append new dict
                    database_editable.append({"Base ID":base_id, "Update Name":update_version_new, "Update ID":update_id})
                    added_to_database.append({"Base ID":base_id, "Update Name":update_id, "Update ID":update_version_new})
                    logging.info(f'UPDATE VERSIONS [{base_id}]: new entry {update_version_new}')
                
            #commit changes
            database[table_name] = database_editable
            database.commit()
            logging.info('UPDATE VERSIONS: changes commited!')
            logging.info('UPDATE VERSIONS: done!')
            
            return added_to_database
                

    def VersionsToList(versions_text_string):
        return_list = []

        for i in versions_text_string.split("\n"):
            try:
                if i.startswith("id|") or "|" not in i:
                    raise()
                update_id, update_version_latest = i.split("|")
                base_id = update_id[:-3]+"000"
                if next((item for item in return_list if item['Base ID'] == base_id), None) is None:
                    if update_id.endswith("800"):
                        return_list.append({"Base ID":base_id,"Update Name":update_version_latest, "Update ID":update_id})
            except:
                pass
        return return_list


    #create database foleder
    create_folder(db_folder)

    #TODO use git to check nx-updates for updates, keep in mind this function will run every hour or so
    #check if nx-versions repository is present, if not, clone it
    rescan_db = False
    if isfile(nx_versions_folder+"/versions.txt") is False or is_git_repo(nx_versions_folder) is False or isdir(nx_versions_folder) is False:
        #remove broken folder
        try:
            shutil.rmtree(nx_versions_folder)
        except:
            pass
        
        logging.info(f"Cloning nx-versions to: {nx_versions_folder}")
        logging.info(f'UPDATE VERSIONS [GIT]: cloning nx-versions to {nx_versions_folder}')
        
        git.Repo.clone_from(var.NXVERSION, nx_versions_folder)
        rescan_db = True
    
    #check if present repository is behind master
    repo = git.Repo(nx_versions_folder)
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
    #if there's no db file yet, parse entire versions.txt file
    result=[]
    if isfile(db_location) is False or rescan_db is True:
        #update entire database
        nx_versions_file = False
        if isfile(nx_versions_folder+"/versions.txt") is True:
            with open(nx_versions_folder+"/versions.txt", 'r') as file:
                nx_versions_file = file.read()

            if nx_versions_file is not False:
                result = AddtoDB(VersionsToList(nx_versions_file))
                logging.info(f'UPDATE VERSIONS: {len(result)} updates found in this run')
            else:
                logging.info(f'UPDATE VERSIONS [ERROR]: no version file located at: {nx_versions_folder+"/versions.txt"}')
        else:
            logging.info(f'UPDATE VERSIONS [ERROR]: no version file located at: {nx_versions_folder+"/versions.txt"}')

    #TODO if there are new updates, copy versions.txt to old_versions.txt, clone the new versions.txt

    #TODO after new file is cloned, parse it to the database (maibe use diff so there's no need to read the entire file)

    #used by the bot to know if runing the check cicle for user is necessary or not
    return result


def NotifyUsersUpdate(update_list, user_database):
    """used to match new updates with ids users are currently monitoring"""
    
    notify_dict = {}
    for user_id in user_database:
        watching_list = []       
        user_watching = user_database[user_id]
        for i in update_list:
            if i['Base ID'] in user_watching or i['Update ID'] in user_watching:
                watching_list.append(i)
        if len(watching_list) > 0:
            notify_dict[user_id] = watching_list
                
    return notify_dict