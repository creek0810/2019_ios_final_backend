from pymongo import MongoClient
# connect to DB
DB = MongoClient("mongodb://192.168.100.249:27017")
USER_COL = DB["iosChatRoom"]["user"]
FRIEND_COL = DB["iosChatRoom"]["friendTable"]
users = ["test", "river", "test2"]
tmp = []
for user_id in users:
    FRIEND_COL.update_one({"userID": user_id}, {"$set": {"friendList": tmp}})
    result = FRIEND_COL.find_one({"userID": user_id})
    print(result)
