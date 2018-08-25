from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import re
from pyquery import PyQuery as pq
import pymongo

MONGO_URL="LOCALHOST"
MONGO_DB="taobao"
MONGO_TABLE="product"
client=pymongo.MongoClient(MONGO_URL)
db=client[MONGO_DB]

#声明浏览器驱动
browser=webdriver.Chrome()

#搜索商品信息
def search():
    try:
        #驱动浏览器加载淘宝首页
        browser.get("http://www.taobao.com")
        #等待搜索框加载完成并获取该元素
        input_element=WebDriverWait(browser,10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR,"#q"))
        )
        #等待搜索按钮可点击并获取该元素
        search_button=WebDriverWait(browser,10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR,"#J_TSearchForm > div.search-button > button"))
        )
        #输入关键字美食
        input_element.send_keys("美食")
        #点击搜索按钮
        search_button.click()
        #获取总页码数
        page_total_num=WebDriverWait(browser,10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR,"#mainsrp-pager > div > div > div > div.total"))
        )
        return page_total_num.text
    except TimeoutException:
        return search()
#实现翻页功能
def next_page(page_number):
    try:
        #等待页码输入框加载成功，并获取该对象
        input_num=WebDriverWait(browser,10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR,"#mainsrp-pager > div > div > div > div.form > input"))
        )
        #等待页码跳转按钮加载成功，并获取该对象
        confirm_button=WebDriverWait(browser,10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR,"#mainsrp-pager > div > div > div > div.form > span.btn.J_Submit"))
        )
        #清空页码输入框
        input_num.clear()
        #输入需要跳转的页码
        input_num.send_keys(page_number)
        #点击页码确认跳转按钮
        confirm_button.click()
        #判断跳转后的页面是否和输入的页码数一致
        WebDriverWait(browser,10).until(
            EC.text_to_be_present_in_element((By.CSS_SELECTOR,'#mainsrp-pager > div > div > div > ul > li.item.active > span'),str(page_number))
        )
    #超时则重新加载
    except TimeoutException:
        next_page(page_number)
#解析网页代码，获取商品信息
def get_products():
    #判断商品信息是否加载完成
    WebDriverWait(browser,10).until(EC.presence_of_element_located((By.CSS_SELECTOR,"#mainsrp-itemlist .items .item")))
    #获取加载完成的网页代码
    html=browser.page_source
    #利用pyquery解析网页代码
    doc=pq(html)
    #获取所有的商品信息的列表
    items=doc("#mainsrp-itemlist .items .item").items()
    #遍历获取每个商品的信息
    for item in items:
        product={
            'image':item.find(".pic .img").attr("src"),
            'price':item.find(".price").text(),
            'deal':item.find(".deal-cnt").text()[:-3],
            'title':item.find(".title").text(),
            'shop':item.find(".shop").text(),
            'location':item.find(".location").text()
        }
        save_to_mongo(product)

#将结果存储到mongodb中
def save_to_mongo(result):
    try:
        if db[MONGO_TABLE].insert(result):
            print("存储到mongodb成功",result)
    except Exception:
        print("存储到mongodb失败",result)

if __name__ == '__main__':
    #获取总的页码，带有其他字符
    total_num=search()
    #提取页码字符串中的数字
    pattern=re.compile("(\d+)")
    total=int(re.search(pattern,total_num).group(1))
    print(total)
    #从第二页开始翻页
    for i in range(2,total+1):
        next_page(i)
        get_products()
    browser.close()
