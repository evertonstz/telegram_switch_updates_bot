This bot is available and ready to be used at: https://t.me/switch_updates_bot

# Install
Get the latest stable .zip or tar.gz from [releases](https://github.com/evertonstz/telegram_switch_updates_bot/releases) and extract it anywhere you want.
### MangoDB
*This is only needed if you don't have MongoDB already in your server*

Optional: edit the `docker-compose.yml` file with a new password and user. Default user is `root` and default password is `examples`

On linux, if you already have docker and docker-compose and assuming the .zip was extracted at `~/telegram_switch_updates_bot`, this should as simple as:
```
$ cd ~/telegram_switch_updates_bot
# docker-compose up &
```


### Env variables
Most configurations are passed to the bot via .env file. Create a .env text file in the bot's main folder (`~/telegram_switch_updates_bot/.env`), these are the possible variables you can put there (with fake personal information ofc):
```
#Token for your telegram bot, this is the token Bot Father will give you
TELEGRAM_TOKEN = 1000251511392:AHKkdhdgmfn-sdsda541-LaFfmfJqQnc

#MongoDB information
MONGO_URL = localhost
MONGO_PORT = 27017
MONGO_DBNAME = telegram_switch_bot
MONGO_USERNAME = root
MONGO_PASS = example

#This is your (dev) chat id
#you'll receive bugreports via telegram, the bot will only send them to your chat id
TELEGRAM_DEBUG = True
TELEGRAM_ADM_CHATID = 441873556

#These are pushover's user and api keys, 
#bug reports will be also sent via pushhover if PUSHOVER_DEBUG is True
PUSHOVER_DEBUG = True
PUSHHOVER_USERKEY = uQAwCg4iiyJYjfhkgloHHh75g
PUSHOVER_APIKEY = ajt2hdgHDgnfkkfoi6nv

#Pushbullet Acess token
#bug reports will be also sent via Pushbullet if PUSHBULLET_DEBUG is True
PUSHBULLET_DEBUG = True
PUSHBULLET_ACESS_TOKEN = o.6jDjfofsy82f56fjv
#on PUSHBULLET_DEVICES separate multiple devices witn commas
PUSHBULLET_DEVICES = Chrome, Xiaomi Mi A2

#Notify run don't use any kind of keys, but needs to be autenticated manually: https://notify.run/
#bug reports will be also sent via notify.run if NOTIFYRUN_DEBUG is True
NOTIFYRUN_DEBUG = True

#The user IDs here aren't limited by USER_LIMIT (ie: can subscribe in as many game IDs as they want, be cautious. You can change this limit on the variables.py file
#{TELEGRAM_ADM_CHATID} will only work if you set the TELEGRAM_ADM_CHATID above, separate multiple IDs by commas
UNLIMITED_USERS = ${TELEGRAM_ADM_CHATID}, 122354466

#The limit of how many search results will be retrieved to the user when using the /s command
SEARCH_LIMIT = 15
```

You don't need to pass every variable, optional variables are:
```
MONGO_DBNAME, default value is "telegram_switch_bot"
MONGO_USERNAME, is only optional if your mongo don't have a username and password
MONGO_PASS, same as above

TELEGRAM_DEBUG, default value is False
TELEGRAM_ADM_CHATID, is only needed if TELEGRAM_DEBUG is True

PUSHOVER_DEBUG, default value is False
PUSHHOVER_USERKEY, is only needed if PUSHOVER_DEBUG is True
PUSHOVER_APIKEY, is only needed if PUSHOVER_DEBUG is True

PUSHBULLET_DEBUG, default value is False
PUSHBULLET_ACESS_TOKEN, is only needed if PUSHBULLET_DEBUG is True
PUSHBULLET_DEVICES, not needed, if PUSHBULLET_DEBUG is True and you don't provide a device, all your devices will be notified

NOTIFYRUN_DEBUG, default is False

UNLIMITED_USERS, default limits every user, including the adm

SEARCH_LIMIT, default is 10
```

As an example, if you don't want any kind of bug report, unlimited users or custom search limit, your `~/telegram_switch_updates_bot/.env` text file will look like this:
```
#Token for your telegram bot, this is the token Bot Father will give you
TELEGRAM_TOKEN = 1000251511392:AHKkdhdgmfn-sdsda541-LaFfmfJqQnc

#MongoDB information
MONGO_URL = localhost
MONGO_PORT = 27017
MONGO_DBNAME = telegram_switch_bot
MONGO_USERNAME = root
MONGO_PASS = example
```

More settings are available in the `~/telegram_switch_updates_bot/tswitch/variables/variables.py`, those will eventually be migrated to a settings file.

### Starting bot
After you have everything ready just run the __main__.py file: `python ~/telegram_switch_updates_bot/__main__.py`

The bot will automatically clone the necessary nx-versions and titledb repositories and parse them into MangoDB (they'll be checked every now and them for updates, the interval is defined in the `variables.py` file), parsing should take some ~~5 minutes~~ seconds. After that the bot should be working.
