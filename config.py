#!/usr/bin/env python
# encoding: utf-8


class Config(object):
    pass


class DevConfig(Config):
    debug = True
    SQLALCHEMY_DATABASE_URI = "mysql+pymysql://102Xi102:X123456i@139.224.54.233:3306/SQW"
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    SQLALCHEMY_ECHO = False
    FLASKY_POSTS_PER_PAGE = 10
    FLASKY_COMMENTS_PER_PAGE = 6
    FLASKY_RESPOSTS_PER_PAGE = 12