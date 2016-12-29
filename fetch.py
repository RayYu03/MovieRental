# -*- coding:utf-8 -*-
from bs4 import BeautifulSoup
import requests
import time
from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import json

eng = create_engine('sqlite:///data-dev.sqlite')

Base = declarative_base()

class Movie(Base):
    __tablename__ = 'movies'
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(64), unique=True, index=True)
    original_title = Column(String(64), unique=True, index=True)
    directors = Column(String(64))
    casts = Column(String(64))
    genres = Column(String(64))
    year = Column(Integer)
    rating = Column(Float)
    images = Column(String(64))
    alt = Column(String(64))
    amount = Column(Integer, default=200)
    counts = Column(Integer, default=0)

Session = sessionmaker(bind=eng)
session = Session()

def start():
    for i in range(13):
        api = 'https://api.douban.com/v2/movie/top250?start={}'.format(20*i)
        res = requests.get(api)
        json_str = json.loads(res.text)
        for movie in json_str['subjects']:
            title = movie['title']
            original_title = movie['original_title']
            directors = ' / '.join([director['name'] for director in movie['directors']])
            casts = ' / '.join([cast['name'] for cast in movie['casts']])
            genres = ' / '.join(movie['genres'])
            year = movie['year']
            rating = movie['rating']['average']
            images = movie['images']['large']
            alt = movie['alt']
            session.add(Movie(title=title,original_title=original_title,
                        directors=directors,casts=casts,genres=genres,
                        year=year,rating=rating,images=images,alt=alt))
            session.commit()

if __name__ == '__main__':
    start()
