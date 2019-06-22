let SOCKET

const API = {
    "getFriendList": "http://140.121.197.197:6700/get_friends"
}

function postData(url, body){
    return fetch(url, {
        body: body, // must match 'Content-Type' header
        cache: 'no-cache', // *default, no-cache, reload, force-cache, only-if-cached
        credentials: 'same-origin', // include, same-origin, *omit
        headers: {
            'user-agent': 'Mozilla/4.0 MDN Example',
            'content-type': 'application/json'
        },
        method: 'POST', // *GET, POST, PUT, DELETE, etc.
        mode: 'cors', // no-cors, cors, *same-origin
    })
    .then((response) => response.json())
}

function getData(url){
    return fetch(url, {
        cache: 'no-cache', // *default, no-cache, reload, force-cache, only-if-cached
        credentials: 'same-origin', // include, same-origin, *omit
        headers: {
            'user-agent': 'Mozilla/4.0 MDN Example',
            'content-type': 'application/json'
        },
        method: 'GET', // *GET, POST, PUT, DELETE, etc.
        mode: 'cors', // no-cors, cors, *same-origin
    })
    .then((response) => response.json())
}

function connect(){
    let name = document.getElementById("sender").innerText;
    SOCKET = io.connect('http://140.121.197.197:6700');
	SOCKET.on('get msg', function(msg) {
        console.log(msg);
        let str = ""
        if (msg["type"] == 1){
            str = `<tr><td>${msg["sender"]}</td><td>${msg["receiver"]}</td><td>${msg["message"]}<td><td>${msg["timeStamp"]}</td></tr>`
        } else {
            str = `<tr><td>${msg["sender"]}</td><td>${msg["receiver"]}</td><td><img src="http://140.121.197.197:6700/image?path=${msg["message"]}"</td><td>${msg["timeStamp"]}</td></tr>`
        }
        console.log(str)
        document.getElementById("show_msg").innerHTML += str;
        let sender = document.getElementById("sender").innerText;
        SOCKET.emit("get msg success", {
            sender: sender,
            timeStamp: msg["timeStamp"]
        });
    });
	SOCKET.on('connect', function() {
		SOCKET.emit('post name', {sender: name});
		SOCKET.emit('get history', {sender: name});
    });
}

function sendMessage(){
    let send = document.getElementById("sender").innerText;
    let rcv = document.getElementById("rcv").value;
    let msg = document.getElementById("msg").value;
    SOCKET.emit("send msg", {
        sender: send,
        receiver: rcv, 
        message: msg
    });
}
async function updateFriendList() {
    let friends = await getData(API.getFriendList);
    let tableStr = ""
    for(i in friends) {
        let tmp = `<tr><th>${friends[i]["id"]}</th><th>${friends[i]["status"]}</th></tr>`
        tableStr += tmp;
    }
    document.getElementById("friend_list_table").innerHTML = tableStr;
}
function init(){
    document.getElementById("send").addEventListener("click", sendMessage);
    updateFriendList();
    connect();
}
window.addEventListener("load", init); 
