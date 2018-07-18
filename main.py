#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @Time    : 2018/7/17  14:03
# @Auther  : Bill Xu
# @File    : main.py

import os
from multiprocessing.pool import Pool

import requests
from lxml import html
from requests.exceptions import ConnectionError
import redis
from config import *


# Request a website and return text
def webRequests(url):
    try:
        res = requests.get(url=url,headers=HEADERS,proxies={"HTTP":getProxy()})
        if res.status_code == 200:
            return res
        else:
            return None
    except ConnectionError as e:
        print(e)


# Get title and set urls
def getSeturls():
    '''
    :return: 返回字典titles_n_urls，包含套图标题和url
    '''
    titles_n_urls = dict()
    res = webRequests(INDEX_URL)
    tree = html.fromstring(res.text)
    for each in tree.xpath('//p[@class="url"]'):
        titles = each.xpath('./a/text()')   # 返回每日的title列表
        set_urls = each.xpath('./a/@href')  # 返回每日的seturl列表
        for title,set_url in zip(titles,set_urls):
            titles_n_urls.update({set_url:title})
    return titles_n_urls

# Save the title_n_urls to redis
def saveTitleUrls(name,dic):
    '''
    :param name: redis的hash名字
    :param dic: 套图的标题和url字典
    :return:
    '''
    try:
        r = dbConnect()
        r.hmset(name,dic)
    except redis.ConnectionError as e:
        print(e)

# Get pic pages
def getPicPages(seturl):
    res = webRequests(seturl)
    tree = html.fromstring(res.text)
    maxPnum = tree.xpath('//*[@class="pagenavi"]/a[last()-1]/span/text()')[0]  # 获取最大页数
    picPages = [seturl + '/{}'.format(i) for i in range(1,int(maxPnum)+1)]
    return picPages   #  返回图片页列表

# Create set directory
def createSetDir(seturl):
    r = dbConnect()
    title = r.hget('mzitu',seturl)
    if title:
        if not os.path.exists(title):
            os.mkdir(title)
            return title
        else:
            print(title + "已存在！")
            return None
    else:
        print(title + '不在数据库中，请重试！')
        return None

# Create Project dir
def createProjectDir(dir):
    if not os.path.exists(dir):
        os.mkdir(dir)
    else:
        print("项目目录" + dir + "已创建！")


# Get pic url
def getPicUrl(picPages):
    picUrls = list()
    for picPage in picPages:
        res = webRequests(picPage)
        tree = html.fromstring(res.text)
        picurl = tree.xpath('//*[@class="main-image"]/p/a/img/@src')[0]
        picUrls.append(picurl)
    return picUrls  # 返回图片下载链接列表

# save imgs
def saveImgs(imgurls):   # 传进来一个图片下载链接的列表
    for imgurl in imgurls:
        res = webRequests(imgurl)
        content = res.content
        name = imgurl.split('/')[-1]
        with open(name,'wb') as f:
            f.write(content)
            print("图片{}已下载！".format(imgurl))


def main(seturl):
    title = createSetDir(seturl)
    if title:
        os.chdir(title)
        picPages = getPicPages(seturl)
        picUrls = getPicUrl(picPages)
        print(picUrls)
        saveImgs(picUrls)
        print("套图{}下载完成！".format(seturl))
        os.chdir('..')
    else:
        print("Already finished!")


if __name__ == '__main__':
    # dic = getSeturls()
    # saveTitleUrls(name='mzitu',dic=dic)
    r = dbConnect()
    createProjectDir(PROJECT_DIR)
    os.chdir(PROJECT_DIR)
    pool = Pool(processes=2)
    set_url_list = [url for url in r.hkeys('mzitu')]
    pool.map(main,set_url_list)  # 增加多进程
    # for seturl in r.hkeys('mzitu'):
    #     title = createSetDir(seturl)
    #     if title:
    #         os.chdir(title)
    #         picPages = getPicPages(seturl)
    #         picUrls = getPicUrl(picPages)
    #         print(picUrls)
    #         saveImgs(picUrls)
    #         print("套图{}下载完成！".format(seturl))
    #         os.chdir('..')
    #     else:
    #         print("Already finished!")
    #         continue