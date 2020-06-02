#!/usr/bin/env python
# encoding: utf-8

from flask import Flask, json, request, flash
from flask_socketio import SocketIO
from geventwebsocket.websocket import WebSocketError

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)
socketio.init_app(app)
user_socket_dict = {}


@app.route('/ws/<username>')
def ws(username):
    user_socket = request.environ.get("wsgi.websocket")
    if not user_socket:
        return "请以WEBSOCKET方式连接"

    user_socket_dict[username] = user_socket

    def fresh_list():
        userlist = ""
        for key in user_socket_dict.keys():
            userlist = userlist + "-" + key
        send_msg = {
            "userlist": userlist[1:],
            "is_connect": True
        }
        sdict = user_socket_dict.values()
        for item in sdict:
            try:
                item.send(json.dumps(send_msg))
            except WebSocketError:
                continue
        print(user_socket_dict)

    while True:
        try:
            user_msg = user_socket.receive()
            if user_msg:
                user_msg = json.loads(user_msg)
                print("服务器收到消息 type:{}".format(user_msg.get("type")))
                if user_msg.get("type") == 'chat':
                    to_user_socket = user_socket_dict.get(user_msg.get("to_user"))
                    send_msg = {
                        "send_msg": user_msg.get("send_msg"),
                        "send_user": username
                    }
                    try:
                        to_user_socket.send(json.dumps(send_msg))
                        print("消息发送成功")
                    except AttributeError:
                        continue
                elif user_msg.get("type") == 'connect':
                    fresh_list()
                elif user_msg.get("type") == 'close':
                    del user_socket_dict["{}".format(username)]
                    fresh_list()
                    break

        except WebSocketError:
            break

    return "disconnet"


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=8024)
