#!/usr/bin/env python
# encoding: utf-8
from random import randint
from sqlalchemy.exc import  IntegrityError
from faker import Faker
from app import db,Respost



def respost(count = 30):
    fake = Faker('zh_CN')
    i=0
    while i<count:
        r = Respost(
            title = fake.text(10),
            body = fake.text(200),
            timestamp = fake.date_this_month(before_today=True, after_today=False),
            author = fake.name(),
            category = randint(1,10)
        )
        db.session.add(r)
        try:
            db.session.commit()
            i +=1
        except IntegrityError:
            db.session.rollback()