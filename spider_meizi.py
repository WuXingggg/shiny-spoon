# -*- coding: UTF-8 -*-
import requests
from requests import RequestException
from bs4 import BeautifulSoup
import re
from multiprocessing import Pool


# import pymongo

# from config import *
import os
import time

start=24656#起始图片ID，打开任何一个图集，链接最后的那一串数字，五位数。
end=25370#终止图片ID，起始初始建议间隔大一些，然后然他自动遍历搜索有效地址

# MONGO_URL = 'localhost'#建立数据库基本参数，并且连接本地MONGODB数据库。
# MONGO_DB = 'nvshens'
# MONGO_TABLE = 'piture'
# client = pymongo.MongoClient(MONGO_URL,connect=False)#声明MONGODB数据库对象，connect=False是为了消除MONGODB有关多线程的提示
# db=client[MONGO_DB]#数据库名称

base_url='https://www.nvshens.com/g/'#宅男女神美图图片专栏下的基本网址

headers1={
"Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
"Accept-Encoding":"gzip, deflate, sdch, br",
"Accept-Language":"zh-CN,zh;q=0.8",
"Cache-Control":"max-age=0",
"Connection":"keep-alive",
"Cookie":"records=%5B%7B%22id%22%3A%2225542%22%2C%22name%22%3A%22%u97E9%u96E8%u5A75%22%7D%5D; gallery_25364=1; Hm_lvt_1bb490b9b92efa278bd96f00d3d8ebb4=1517657472; Hm_lpvt_1bb490b9b92efa278bd96f00d3d8ebb4=1517658032; Hm_lvt_f378865b660846b55ba91d29e1c4c04d=1517657803; Hm_lpvt_f378865b660846b55ba91d29e1c4c04d=1517658776; gallery_24656=1",
"Host":"www.nvshens.com",
"If-Modified-Since":"Sat, 03 Feb 2018 11:19:10 GMT",
"Upgrade-Insecure-Requests":"1",
"User-Agent":"Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.104 Safari/537.36 Core/1.53.4295.400 QQBrowser/9.7.12661.400",
}
headers2={
'Accept':'image/webp,image/*,*/*;q=0.8',
'Accept-Encoding':'gzip, deflate, sdch, br',
'Accept-Language':'zh-CN,zh;q=0.8',
'Cache-Control':'max-age=0',
'Connection':'keep-alive',
'Host':'t1.onvshen.com:85',
"If-None-Match":"ce118ca4a39cd31:0",
"Referer":"https://www.nvshens.com/g/24656/",
'User-Agent':'Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.104 Safari/537.36 Core/1.53.4295.400 QQBrowser/9.7.12661.400',

         }

def tes2_url(url):
    print('正在访问',url)
    try:#确保每一个requests都有异常处理
        response = requests.get(url, headers=headers1,timeout=5)
        soup = BeautifulSoup(response.text, 'lxml')
        if soup.select('#htilte'):#是否有标题，判断该页面下是否有图片集
            url_true=url
            return url_true
        else:
            print('无效地址',url)
            pass
    except:
        pass

def url_jiexi(url_true):
    response = requests.get(url_true, headers=headers1)
    soup = BeautifulSoup(response.text, 'lxml')
    try:
        title = soup.select_one('#htilte').text
        imag_num = int(re.sub("\D", "", soup.select_one('#dinfo > span').text[:3]))#正则表达式获得具体数字
        imag_base = soup.img['src'][:-5]#获得src标签值，并且去掉src=这几个字符
        print(title)
        print(imag_num)
        print(imag_base)
        return (title,imag_num,imag_base)
    except:
        return None
def download_image(title,imag_base,i):
    imag_url=imag_base+str(i).zfill(3)+".jpg"
    print('正在下载',imag_url)#！！很重要，获得一个调制信息
    try:
        response = requests.get(imag_url, headers=headers2,timeout=10)
        print(response.status_code)
        if response.status_code == 200:
            print("请求图片成功")
            save_image(response.content, title, i)
        else:
            pass
        return None
    except RequestException:
        print('请求图片出错',imag_url)
        return None

def save_image(content,title,i):#创建对应分类的文件夹，并且保存图片。
    dir_name_or=str(title)[:100].strip()
    dir_name = re.sub("[\s+\.\!\/]+", "",dir_name_or)
    print(dir_name)
    dir_path='F:\spider\picture\zhainan2\{}'.format(dir_name)
    try:
        os.mkdir(dir_path)
        print("创建文件夹成功")
    except:
        pass

    file_path='{0}\{1}.{2}'.format(dir_path,str(i).zfill(3),'jpg')
    if not os.path.exists(file_path):
        with open(file_path,'wb') as f:
            f.write(content)
            f.close()
        print("写入图片成功")

# def save_to_mongo(result):
#     try:
#         if db[MONGO_TABLE].insert(result):
#             print('存储到MONGODB成功',result)
#             return True
#         return False
#     except:
#         print('存储错误')

def main(i):
        url=base_url+str(i)
        url_true=tes2_url(url)
        if url_true:
            title, imag_num,imag_base =url_jiexi(url_true)
            for i in range(1, int(imag_num)):
                download_image(title,imag_base,i)
                imag_url = imag_base + str(i).zfill(3) + ".jpg"
                result={
                    "title":title,
                    "indx":i,
                    "url":imag_url
                }
                print(result)

if __name__ == '__main__':
    pool=Pool()
    pool.map(main,[i for i in range(start,end)])

