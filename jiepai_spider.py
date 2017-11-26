# -*- coding: UTF-8 -*-
import requests
from urllib.parse import urlencode
from requests import RequestException
import json
from bs4 import BeautifulSoup
import re
import pymongo
# from config import *
from  hashlib import md5
import os
from multiprocessing import Pool
from json.decoder import JSONDecodeError
import time

MONGO_URL = 'localhost'#建立数据库基本参数，并且连接本地MONGODB数据库。
MONGO_DB = 'toutiao'
MONGO_TABLE = 'toutiao'
client = pymongo.MongoClient(MONGO_URL,connect=False)#声明MONGODB数据库对象，connect=False是为了消除MONGODB有关多线程的提示
db=client[MONGO_DB]#数据库名称

#首先在今日头条搜索街拍，然后点击图集，这个页面先叫做索引页。再然后，寻找，有关各个图集的入口。
#在检查索引页网页元素中，network中找到XHR板块，发现下拉网页会得到新的XHR返回
#再发现，原来是通过带有data中有不同offset值的请求的方式，来使得加载更多链接。观察，刷新出新的AJAX请求中Response值部分，发现是JSON格式，并且带有各个详情页入口
# 通过循环，拿到各个街拍组图链接的数据，返回的结果是JSON数据，用JSON包解析数据成字典
#再进入详情页，在网页中寻找有关图片及其图集中其他图片相关链接
#先找XHR，寻找AJAX请求中是否有想要的数据，未发现有效连接
#继续寻找，在network的doc板块中的网页源代码中，发现是通过变量gallery加载，后面带有大量图片链接，并且与图集后续图片链接一致。目的是解析gallery

def get_pade_index(offset,keyword):#获取索引页网站源代码
    data={
        'offset': offset,
        'format': 'json',
        'keyword': keyword,
        'autoload': 'true',
        'count': '20',
        'cur_tab': 3#!!!这里特别注意！！！视频与实际网页有改动，观察点击图集前后对比，发现cur_tab变量不同。
                    #如果发现请求结果有大量非图集，请修改这个参数
    }

    url='http://www.toutiao.com/search_content/?'+urlencode(data)#urlencode(data)将字典对象转化为URL请求参数
                                                                #构建一个带有data的请求，以取得返回的Response中的JSON
    try:headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.104 Safari/537.36 Core/1.53.3538.400 QQBrowser/9.6.12501.400'
        }
        #为了保证爬虫正常运行，设置请求头
        response = requests.get(url, headers=headers)
        # time.sleep(1)
        if response.status_code == 200:
            return response.text
        return None
    except RuntimeError:
        print('请求索引出错')
        return None

def parse_page_index(html):#解析索引页信息
    try:#解析索引页通过请求获得的各个请求返回的JSON，最终获得各个图集入口
        data=json.loads(html)#将JSON字符串，转化为JSON变量对象
        if data and 'data' in data.keys():#data存在且有存在data值
            for item in data.get('data'):
                yield item.get('article_url')
    except:
        pass

def get_page_detail(url):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.104 Safari/537.36 Core/1.53.3538.400 QQBrowser/9.6.12501.400'
        }
        response = requests.get(url, headers=headers)
        # time.sleep(2)
        if response.status_code == 200:
            return response.text
        return None
    except RuntimeError:
        print('请求详情页出错',url)
        return None

def parse_page_detail(html,url):#该函数解析详情页数据，最后返回各个图集的标题及其图片链接
    soup = BeautifulSoup(html,'lxml')
    title=soup.select('title')[0].get_text()#利用BS解析出title
    print(title)
    images_pattern=re.compile('gallery: (.*?),\n',re.S)#正则表达式，注意gallery与原网站不同，记得加入,\n！！
    result=re.search(images_pattern,html)
    if result:#如果存在result则运行
        print(result.group(1))
        data = json.loads(result.group(1))#解析JSON集，顺便提取result里的内容
        if data and 'sub_images' in data.keys():#data存在，且有sub_images这个变量。
            sub_images=data.get('sub_images')
            images=[item.get('url') for item in sub_images]#构建一个列表，存放images地址。sub_images是一个JSON中的值，不能直接引用。
            for image in images: download_image(image)
            return {
                'title':title,
                'url':url,
                'images':images
            }

def save_to_mongo(result):
    try:
        if db[MONGO_TABLE].insert(result):
            print('存储到MONGODB成功',result)
            return True
        return False
    except:
        print('存储错误')

def download_image(url):
    print('正在下载',url)#！！很重要，获得一个调制信息
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.104 Safari/537.36 Core/1.53.3538.400 QQBrowser/9.6.12501.400'
        }
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            save_image(response.content)#返回二进制内容，如图片。
        return None
    except RequestException:
        print('请求图片出错',url)
        return None


def save_image(content):#创建对应分类的文件夹，并且保存图片。个人
    dir_name=str(KEYWORD)+'_'+str(GROUP_START)+'-'+str(GROUP_END)#个人补充功能！
    dir_path='F:\spider\picture\{}'.format(dir_name)
    try:
        os.mkdir(dir_path)
    except:
        pass

    file_path='{0}/{1}.{2}'.format(dir_path,md5(content).hexdigest(),'jpg')
    if not os.path.exists(file_path):
        with open(file_path,'wb') as f:
            f.write(content)
            f.close()

def main(offset):#主程序流程
    html = get_pade_index(offset,KEYWORD) #自己输入搜索内容，还有搜索量，获取索引页源代码
    for url in parse_page_index(html):#解析索引页代码，并且用遍历，提取出url(各个详情页链接入口)
        html=get_page_detail(url)#得到详情页网页源代码
        if html:#如果得到正常得到详情页网站源代码，继续以下步骤
            result=parse_page_detail(html,url)#解析详情页源代码，得到result，包含各个图片的链接，所在图集标题，详情页地址。
            if result :save_to_mongo(result)#如果result正常获取，则保存下来。


GROUP_START = 1#自行设定
GROUP_END = 200#自行设置
KEYWORD = '羽毛球'#自行搜索

if __name__ == '__main__':
    groups=[x*20 for x in range(GROUP_START,GROUP_END+1)]
    pool=Pool()
    pool.map(main,groups)
