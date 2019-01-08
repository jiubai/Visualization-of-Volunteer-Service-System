# -*- coding: utf-8 -*-
import requests
import re
import json


if __name__ == '__main__':
    url = 'http://www.chamiji.com/chinaprovincepopulation'
    response = requests.get(url)
    if response.status_code == 200:
        html = response.text
    pattern = re.compile('<tr>.*?href=.*?>(.*?)<.*?万.*?<td>(.*?)<.*?', re.S)
    items = re.findall(pattern, html)
    with open('../data/2018各省人口统计.txt', 'a') as f:
        for item in items:
            content = (item[0], item[1].strip())
            f.write(json.dumps(content, ensure_ascii=False) + '\n')

