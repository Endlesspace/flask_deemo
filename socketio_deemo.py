#!/usr/bin/env python
# encoding: utf-8

from flask import Flask, json, request
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
    print(user_socket_dict)

    def fresh_list():
        userlist = []
        for key in user_socket_dict.keys():
            userlist.append(key)
        send_msg = {
            "userlist": userlist,
            "is_connect": True
        }
        for item in user_socket_dict.values():
            item.send(json.dumps(send_msg))

    while True:
        try:
            user_msg = user_socket.receive()
            if user_msg:
                user_msg = json.loads(user_msg)
                if user_msg.get("type") == 'chat':
                    to_user_socket = user_socket_dict.get(user_msg.get("to_user"))
                    userlist = []
                    for key in user_socket_dict.keys():
                        userlist.append(key)
                    send_msg={
                        "send_msg": user_msg.get("send_msg"),
                        "send_user": username,
                        "userlist": userlist
                    }
                    to_user_socket.send(json.dumps(send_msg))
                elif user_msg.get("type") == 'connect':
                    fresh_list()

        except WebSocketError as e:
            user_socket_dict.pop(username)
            fresh_list()
            print(user_socket_dict)
            print(e)


if __name__ == '__main__':
    socketio.run()


