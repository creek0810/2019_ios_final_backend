from pymongo import MongoClient
from flask import Flask, render_template, request, redirect, url_for, jsonify, Response, send_file
from flask_socketio import SocketIO, emit
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_cors import CORS, cross_origin

import datetime
import os
import uuid
from config import *

# global var
SID_TABLE = {}
NAME_TABLE = {}
MESSGAE_BUFFER = {}
IMAGE_FOLDER = os.path.dirname(__file__)


app = Flask(__name__)
app.config["SECRET_KEY"] = "this is a secret"
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 1
CORS(app, supports_credentials=True)
login_manager = LoginManager(app)
socketio = SocketIO(app)

class User(UserMixin):
    pass

@login_manager.user_loader
def load_user(user_name):
    user = User()
    user.id = user_name 
    return user

@app.route('/', methods=["GET"])
def index():
    return render_template("index.html")

@app.route('/login', methods=["POST"])
def login():
    print("login")
    user_id = request.form["id"]
    password = request.form["password"]
    print(user_id, password)
    result = USER_COL.find_one({
        "userID": user_id,
        "password": password
    })

    if result:
        user = User()
        user.id = user_id 
        login_user(user)
        return render_template("chat.html", name=result["userName"])
    else:
        return "Bad Login", 401

@app.route("/profile", methods=["GET"])
@login_required 
def profile():
    name = request.args.get("id")
    tmp = USER_COL.find_one({"userID": name}, {"userName": 1, "userID": 1, "propic": 1, "status": 1, "_id": 0})
    if tmp == None:
        return "", 204
    else:
        result = {
            "name": tmp["userName"],
            "id": tmp["userID"],
            "propic": tmp["propic"],
            "status": tmp["status"]
        } 
        return jsonify(result)

@app.route("/update_name", methods=["GET"])
@login_required 
def update_name():
    user_id = request.args.get("id")
    user_name = request.args.get("name")
    print(user_id, user_name)
    USER_COL.update_one({"userID": user_id}, {"$set": {"userName": user_name}})
    print(USER_COL.find_one({"userID": user_id}))
    return "success"

@app.route("/update_status", methods=["GET"])
@login_required 
def update_status():
    user_id = request.args.get("id")
    user_status = request.args.get("status")
    USER_COL.update_one({"userID": user_id}, {"$set": {"status": user_status}})
    print(USER_COL.find_one({"userID": user_id}))
    return "success"

@app.route("/update_propic", methods=["POST"])
@login_required 
def update_propic():
    # establish data 
    file_name = str(uuid.uuid4()) + ".jpg"
    user_id = request.form.get("id")
    # save image
    file = request.files["file"]
    path = os.path.join(IMAGE_FOLDER, 'image/', file_name)
    file.save(path)
    USER_COL.update_one({"userID": user_id}, {"$set": {"propic": file_name}})
    return "Success"


@app.route("/add_friend", methods=["GET"])
@login_required
def add_friend():
    sender = request.args.get("sender")
    name = request.args.get("id")
    print(sender, name)
    if sender != name:
        FRIEND_COL.update_one({"userID": sender}, {"$addToSet": {"friendList": name}})
        data = {
            "sender": sender,
            "message": name,
            "receiver": name,
            "type": 2,
            "timeStamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        if sender not in FRIEND_COL.find_one({"userID": name})["friendList"]:
            socketio.emit("get msg", data, room=SID_TABLE[name])
        return "success"
    print(result)
    return "same account"

@app.route("/get_friends", methods=["GET"])
@login_required
def get_friendlist():
    print("Get friends")
    friends = FRIEND_COL.find_one({"userID": current_user.id}, {"_id": 0, "friendList": 1})["friendList"]
    result = []
    for friend in friends:
        profile = USER_COL.find_one({"userID": friend}, {"_id": 0, "userName": 1, "propic": 1, "userID": 1, "status": 1})
        final = {
            "propic": profile["propic"],
            "name": profile["userName"],
            "id": profile["userID"],
            "status": profile["status"]
        }
        result.append(final)
    return jsonify(result)

@app.route("/send_text", methods=["POST"])
@login_required 
def send_text():
    # establish data
    tmp_data = request.get_json()
    data = {
        "sender": tmp_data["sender"],
        "receiver": tmp_data["receiver"],
        "type": 1,
        "message": tmp_data["message"],
        "timeStamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    print("send text")
    # send to receiver
    if data["receiver"] not in MESSGAE_BUFFER:
        MESSGAE_BUFFER[data["receiver"]] = {}
    MESSGAE_BUFFER[data["receiver"]][data["timeStamp"]] = data
    if data["receiver"] in SID_TABLE:
        socketio.emit("get msg", data, room=SID_TABLE[data["receiver"]])
    # recend to sender
    if data["sender"] not in MESSGAE_BUFFER:
        MESSGAE_BUFFER[data["sender"]] = {}
    MESSGAE_BUFFER[data["sender"]][data["timeStamp"]] = data
    if data["sender"] in SID_TABLE:
        socketio.emit("get msg", data, room=SID_TABLE[data["sender"]])
    print(MESSGAE_BUFFER)
    print(MESSGAE_BUFFER)
    return "Success"

@app.route("/send_image", methods=["POST"])
@login_required 
def upload_image():
    # establish data 
    file_name = str(uuid.uuid4()) + ".jpg"
    data = {
        "sender": request.form.get("sender"),
        "receiver": request.form.get("receiver"),
        "type": 0,
        "message": file_name,
        "timeStamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    # save image
    file = request.files["file"]
    path = os.path.join(IMAGE_FOLDER, 'image/', file_name)
    file.save(path)
    # send to receiver
    if data["receiver"] not in MESSGAE_BUFFER:
        MESSGAE_BUFFER[data["receiver"]] = {}
    MESSGAE_BUFFER[data["receiver"]][data["timeStamp"]] = data
    if data["receiver"] in SID_TABLE:
        socketio.emit("get msg", data, room=SID_TABLE[data["receiver"]])
    # resend to sender
    if data["sender"] not in MESSGAE_BUFFER:
        MESSGAE_BUFFER[data["sender"]] = {}
    MESSGAE_BUFFER[data["sender"]][data["timeStamp"]] = data
    if data["sender"] in SID_TABLE:
        socketio.emit("get msg", data, room=SID_TABLE[data["sender"]])
    print("get image success")
    print(data)
    return "Success"

@app.route("/image", methods=["GET", "POST"])
@login_required 
def query_image():
    image_name = request.args.get("path")
    if image_name == None or image_name == "":
        return "no image"
    path = os.path.join(IMAGE_FOLDER, 'image/', image_name)
    print(path)
    return send_file(path, mimetype="image/jpg")

@socketio.on("post name") 
@login_required
def get_name(data):
    print(SID_TABLE)
    global SID_TABLE, NAME_TABLE
    SID_TABLE[data["sender"]] = request.sid
    NAME_TABLE[request.sid] = data["sender"]
    print(SID_TABLE)

@socketio.on("get history")
@login_required
def get_name(data):
    print("get history")
    print(MESSGAE_BUFFER)
    if data["sender"] in MESSGAE_BUFFER:
        for msg in MESSGAE_BUFFER[data["sender"]]:
            emit("get msg", MESSGAE_BUFFER[data["sender"]][msg], room=SID_TABLE[data["sender"]])

@socketio.on("send msg")
@login_required
def handle_message(tmp_data):
    print("start send")
    # establish data
    data = {
        "sender": tmp_data["sender"],
        "receiver": tmp_data["receiver"],
        "type": 1,
        "message": tmp_data["message"],
        "timeStamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    # send to receiver
    if data["receiver"] not in MESSGAE_BUFFER:
        MESSGAE_BUFFER[data["receiver"]] = {}
    MESSGAE_BUFFER[data["receiver"]][data["timeStamp"]] = data
    if data["receiver"] in SID_TABLE:
        print("send to receiver")
        emit("get msg", data, room=SID_TABLE[data["receiver"]])
    # recend to sender
    if data["sender"] not in MESSGAE_BUFFER:
        MESSGAE_BUFFER[data["sender"]] = {}
    MESSGAE_BUFFER[data["sender"]][data["timeStamp"]] = data
    if data["sender"] in SID_TABLE:
        emit("get msg", data, room=SID_TABLE[data["sender"]])
    print(MESSGAE_BUFFER)

@socketio.on("get msg success")
@login_required
def get_success(data):
    del MESSGAE_BUFFER[data["sender"]][data["timeStamp"]]
    print(MESSGAE_BUFFER)

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port="6700", debug=True)
