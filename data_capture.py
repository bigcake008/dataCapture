import gzip
import io
import re
import time
import os
import random
from urllib import request
from multiprocessing import Process, Queue


class Good(object):
    def __init__(self, d, u, off_line=False, title='', name='', inventory=None):
        if inventory is None:
            inventory = {}
        self.date = d
        self.url = u
        self.off_line = off_line
        self.title = title
        self.name = name
        self.inventory = inventory
        self.low_inventory = []

    def data_process(self, url_data):
        if re.search(r'offline-title', url_data):
            self.title = re.search(r'(<title>)(.*?)(</title>)', url_data)[2]
            self.off_line = True
        else:
            try:
                self.name = re.search(r'(<h1.*?>)(.*?)(</h1>)', url_data)[2]
                self.inventory = eval(re.search(r'(skuMap:)(.*})', url_data)[2])
            except BaseException as e:
                print('Error: %s' % e)
                print(self.url)

    def inventory_scan(self):
        for key, value in self.inventory.items():
            if int(value['canBookCount']) < 5:
                self.low_inventory.append('Style&Size: %s, Price: %s, Count: %s'
                                          % (key, value['price'], value['canBookCount']))


def run_proc(r, u, d, q):
    print('Process %s running' % os.getpid())
    with request.urlopen(r) as html:
        print('Processing url:\n%s' % u)
        item = Good(d, u)
        data = html.read()
        string = gzip.decompress(data).decode('gbk')
        item.data_process(string)
        print(item.name)
        q.put(item)


if __name__ == '__main__':
    date = ''
    url = ''
    goods = []
    offline_goods = []
    result = ''
    scan = ''
    count = 0
    with io.open('scan_file', 'r') as file:
        for line in file.readlines():
            if re.match(r'\d{4}', line):
                date = line
            else:
                url = line.strip()
                req = request.Request(url)
                req.add_header('Host', 'detail.1688.com')
                req.add_header('User-Agent',
                               'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:72.0) Gecko/20100101 Firefox/72.0')
                req.add_header('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8')
                req.add_header('Accept-Language', 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2')
                req.add_header('Accept-Encoding', 'gzip, deflate, br')
                req.add_header('Connection', 'keep-alive')
                req.add_header('Cookie', 'cna=MSKjFmPxP1sCATsqeM0CTa2I; '
                                         'isg=BNfX-yMoRQgG98G-LQahU8yYZUshHKt-Bt6X8SkE_aYNWPeaMe6oz2X6vnjGq4P2; '
                                         'l=cBNr_FngQPr8sf'
                                         '-oBOCNZuI8LZ_OsIOYYuPRwCXMi_5IE6LsV__Oo0y7QFp6csWd9ULB4eJvIYp9'
                                         '-etuixsZ2ikZKTdP.; lid=k15915737928; '
                                         'ali_apache_track=c_mid=b2b-1627778056|c_lid=k15915737928|c_ms=1; '
                                         'UM_distinctid=16f9e2c66e036d-05803ea9ddc50f8-4c302978-1fa400-16f9e2c66e14fe'
                                         '; CNZZDATA1253659577=401740006-1578903399-%7C1579573094; '
                                         'taklid=9ef34dbc3ee6427c9a4c4bd53c573966; '
                                         'alicnweb=touch_tb_at%3D1579578327289%7Clastlogonid%3Dk15915737928; '
                                         'JSESSIONID=2CBFE62F077A384ADD9C952D45076535; _csrf_token=1579578325202; '
                                         'cookie2=136f5d2df93417b18cc2255a80d738ea; '
                                         't=849b33898cd263e012da9b2a667ed7c7; _tb_token_=e3beb5781673e; '
                                         'uc4=nk4=0%40CuMT11%2FdK%2FSTCItfRc3P4RgzaKLlF%2FU%3D&id4=0%40UO%2Bwk'
                                         '%2FJouphCHo6m7Ekd6JDTJbjr; __cn_logon__=false')
                req.add_header('Upgrade-Insecure-Requests', '1')
                req.add_header('Cache-Control', 'max-age=0')
                req.add_header('TE', 'Trailers')
                queue = Queue()
                p = Process(target=run_proc, args=(req, url, date, queue))
                count += 1
                print('count: %d' % count)
                p.start()
                p.join()
                item_from_queue = queue.get()
                goods.append(item_from_queue)
                time.sleep(random.uniform(1.5, 3.5))

    result += 'LOW-INVENTORY:\n'
    tem_date = ''
    for good in goods:
        if good.off_line:
            offline_goods.append(good)
            continue
        good.inventory_scan()
        if len(good.low_inventory) > 0:
            if tem_date != good.date:
                result += good.date
                tem_date = good.date
            result += '%s\n' % good.name
            for info in good.low_inventory:
                result += '%s\n' % info
    result += '\nOFF-LINE:\n'
    tem_date = ''
    for good in offline_goods:
        if tem_date != good.date:
            result += good.date
            tem_date = good.date
        result += '%s\n' % good.title
        result += '%s\n' % good.url
    with io.open('result_file', 'w') as file:
        file.write(result)
    tem_date = ''
    for good in goods:
        if good.off_line:
            continue
        if tem_date != good.date:
            scan += '%s' % good.date
            tem_date = good.date
        scan += '%s\n' % good.url
    with io.open('scan_file', 'w') as file:
        file.write(scan)
