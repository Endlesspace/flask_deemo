#!/usr/bin/env python
# encoding: utf-8
from app import app, db, User, Role, Permission, Post, Comment, Respost, Video
from flask_script import Manager, Server
from flask_migrate import MigrateCommand


manager = Manager(app)
manager.add_command("server", Server())
manager.add_command("db", MigrateCommand)

@ manager.shell
def make_shell_context():
    return dict(app=app, db=db, User=User, Role=Role, Permission=Permission, Post=Post, Comment=Comment, Respost=Respost
                , Video=Video)


if __name__ == '__main__':
    manager.run()
