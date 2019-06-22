from pymongo import MongoClient
# connect to DB
DB = MongoClient("mongodb://host:port")
USER_COL = DB["iosChatRoom"]["user"]
FRIEND_COL = DB["iosChatRoom"]["friendTable"]
