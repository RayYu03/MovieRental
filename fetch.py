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
    """

    ====================     =================
    列名                      说明
    ====================     =================
    id                       序号
    title                    电影名
    original_title           借阅时间
    directors                导演
    casts                    主演
    genres                   类型
    year                     上映年份
    rating                   评分
    images                   封面图片
    alt                      豆瓣链接
    amount                   库存
    counts                   借阅次数
    ====================     =================

    """
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
    """
    ..  note:: 获取数据

        使用 豆瓣电影 TOP250 API 初始化数据。

    """
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
