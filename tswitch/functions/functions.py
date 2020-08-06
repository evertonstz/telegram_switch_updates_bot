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
from json import load
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

def LoadTitleDB(db_folder, table_name='titledb'):
    """load titledb from SqliteDict"""
    db_location = f"{db_folder}/titledb_database.db"
    db = {}
    if isfile(db_location):
        with SqliteDict(db_location, autocommit=False) as database:
            db = database[table_name]
    
    return(db)
        

def UpdateTitleDB(db_folder, repo_folder):
    """function is used to build and interact with titledb database
    it's suposed to run every day, but the interval can be tweaked at variables.py"""
    db_location = f"{db_folder}/titledb_database.db"
    repo_file = f'{repo_folder}/titles.US.en.json'
    logging.info(f'UPDATE TITLEDB: job started!')

    def ReplaceDB(table_name='titledb'):
        #TODO add option to change language
        """adds a the list of dirs to the current database
        """
        #load json file
        with open(f'{repo_folder}/titles.US.en.json') as file:
            titledb_json = load(file)
        
        with SqliteDict(db_location, autocommit=False) as database:
            #just replace old db with the new one
            database[table_name] = titledb_json
            database.commit()
            return True

    #create database foleder
    create_folder(db_folder)

    #TODO use git to check for titledb updates, keep in mind this function will run every day
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
    if isfile(db_location) is False or rescan_db is True:
        #update entire database
        logging.info(f'UPDATE TITLEDB: adding titledb to SqliteDict')
        ReplaceDB()
        result = True
        
    return result


def UpdateNxversiosDB(db_folder, repo_folder): #TODO break away from bot file?
    """function is used to build and interact with nx-versions database
    it's suposed to run every hour, but the interval can be tweaked at variables.py"""

    db_location = f"{db_folder}/versions_database.db"
    
    logging.info(f'UPDATE VERSIONS: job started!')
    
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
    #if there's no db file yet, parse entire versions.txt file
    #TODO don't notify users if it's first clone?
    result=[]
    if isfile(db_location) is False or rescan_db is True:
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

    #TODO if there are new updates, copy versions.txt to old_versions.txt, clone the new versions.txt

    #TODO after new file is cloned, parse it to the database (maibe use diff so there's no need to read the entire file)

    #result isused by the bot to know if runing the check cicle for user is necessary or not
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