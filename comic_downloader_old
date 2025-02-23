import requests
import parsel
import time
import os
from threading import Thread

# 2021.12.13 修改为多线程 大幅度提升了运行下载速度


# url = 'https://www.3004zz.com/100654954.html'
url = input('\n---------------------------------\033[1;32m请输入要下载的漫画主页链接\033[0m---------------------------------\n')
headers = {
    'Referer': 'https://www.san421.com/',
    'user-agent': 'Mozilla/5.0 (iPad; U; CPU OS 3_2_2 like Mac OS X; en-us) AppleWebKit/531.21.10 (KHTML, like Gecko) Version/4.0.4 Mobile/7B500 Safari/531.21.10'}
downloadname = r'O:\收集'


# 下载并保存

def get_download(src, dirnames, filename):
    time.sleep(1)
    img = requests.get(src, headers=headers)
    os.chdir(dirnames)
    with open('{}'.format(filename) + '.jpg', 'wb') as fd:
        fd.write(img.content)
    return src


# 获取章节下图片链接
def get_page_url(herf, dirnames,fir_num):
    resp = requests.get(herf, headers=headers)
    print(resp)
    resp.encoding = resp.apparent_encoding
    res_page = requests.get(herf)
    res_page_img = parsel.Selector(res_page.text)
    end = res_page_img.xpath('//*[@class="post-page-numbers current"]/span/text()').get()
    print('当前下载第', end, '页')
    imgs = res_page_img.xpath('//*[@class="article-content"]/p/img/@src').getall()
    print(imgs)
    che_num = herf.split('.')[-2].split('-')[-1]
    if che_num == fir_num:
        che_num = '1'
    for src in imgs:
        # print(src)
        fname = src.split('/')[-1]
        filename = che_num+'-'+fname.split('.')[0]
        print(filename)
        os.chdir(dirnames)
        with open('0000000.html', 'a') as fdd:
            fdd.write("<div align='center' ><img src='{}.jpg' width='720'></div>".format(filename))
            fdd.close()
        t = Thread(target=get_download, args=(src, dirnames, filename), daemon=False)
        # time.sleep(0.5)
        t.start()
        # get_download(src,dirnames,filename)


# 获取所有章节列表
def get_list_url(url):
    resp = requests.get(url)
    # 自动转码
    resp.encoding = resp.apparent_encoding
    html = parsel.Selector(resp.text)
    # //*[contains(@id,'post-')] 该部分表达式为通用格式，数字变化不影响定位
    list_href = html.xpath('//*[@class="article-paging"][1]/a/@href').getall()
    # 因为最后一个是下一页，所以去掉列表中最后一个
    del (list_href[-1])
    # 因为只能从列表中开始，所以将首页添加进列表中0代表在列表第一位添加
    list_href.insert(0, url)
    # print(list_href)
    tempNum = len(list_href)
    fir_num = url.split('.')[-2].split('-')[-1]
    title = html.xpath('//*[@class="article-title"]/a/text()').get().replace('\n', ' ').lstrip().split('/')[0]
    print(title, '共计', tempNum, '页')
    dirnames = os.path.join(downloadname, title)
    if not os.path.exists(dirnames):
        os.makedirs(dirnames)
    #通过重新定义列表达到指定页数下载
    #以下代码含义为从原有列表中选择最后5个，如果需要累进制下载可将#号去掉，并选择最后要增量下载的页数
    #list_href = list_href[-20:]
    # 从1到最终页顺序取值
    for i in list_href:
        # 拼接页面链接
        herf = i
        # print(herf)
        get_page_url(herf, dirnames,fir_num)


if __name__ == "__main__":
    t = Thread(target=get_list_url, args=(url,))
    t.start()
