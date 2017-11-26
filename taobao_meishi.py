from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import re
from pyquery import PyQuery as pq
import pymongo
from config import *

MONGO_URL='localhost'#设置MONGODB配置
MONGO_DB='taobao'
MONGO_TABLE='product'

client = pymongo.MongoClient(MONGO_URL)#连接MONGODB
db = client[MONGO_DB]

# browser=webdriver.Chrome()#现在是弹出游览器后再进行保存，尝试到后台进行
SERVICE_ARGS=['--load-images=false','--disk-cache=true']#做后台运行的设置
browser=webdriver.PhantomJS(service_args=SERVICE_ARGS)#后台运行
wait = WebDriverWait(browser,10)#因为后面需要很多等待，所以都替换成一个变量\

# browser.set_window_size(1400,900)#设置网页大小
def search():
    print('正在搜索')
    try:
        browser.get('https://www.taobao.com')
        input = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#q"))#输入框
        )
        submit=wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#J_TSearchForm > div.search-button > button')))#搜索键的按钮
        input.send_keys(KEYWORD)
        submit.click()
        total = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,'#mainsrp-pager > div > div > div > div.total')))#找到搜索结果下，页面下方的所有页的页数

        get_products()#在整个页面加载完以后再调用
        return total.text
    except TimeoutError:
        return search()#出现错误，重新请求一次

def next_page(page_number):
    print('正在翻页',page_number)
    try:
        input = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#mainsrp-pager > div > div > div > div.form > input"))#翻页的输入框
        )
        submit = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '#mainsrp-pager > div > div > div > div.form > span.btn.J_Submit')))#翻页键
        input.clear()#清空后再输入
        input.send_keys(page_number)
        submit.click()
        wait.until(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'#mainsrp-pager > div > div > div > ul > li.item.active > span'),str(page_number)))#判断2翻页是否成功，判断当前页数和输入页数是否一样即可
        get_products()
    except TimeoutError:
        next_page(page_number)

def get_products():#获得商品的信息
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,'#mainsrp-itemlist .items .item')))#对class=mainsrp-itemlist下的标签进行定位
    html=browser.page_source
    doc=pq(html)#pq解析库
    items=doc('#mainsrp-itemlist .items .item').items()
    for item in items:
        product = {
            'images':item.find('.pic .img').attr('src'),
            'price':item.find('.price').text(),
            'deal':item.find('.deal-cnt').text()[:-3],
            'title':item.find('.title').text(),
            'shop':item.find('.shop').text(),
            'location':item.find('.location').text()

        }
        print(product)
        save_to_mongo(product)

def save_to_mongo(result):
    try:
        if db[MONGO_TABLE].insert(result):
            print('保存MONGODB成功',result)
    except Exception:
        print('存储到MONGODB失败',result)

KEYWORD='美食'

def main():#可以加入异常处理，保证服务器会关闭
    try:
        total = search()#search本身带有return，所以要用递归的方法
        total = int(re.compile('(\d+)').search(total).group(1))#因为有可能是个字符串，强制转换为int
        for i in range(2,31):
            next_page(i)
    except Exception:
        main()
    finally:
        browser.close()

if __name__ == '__main__':
    main()

