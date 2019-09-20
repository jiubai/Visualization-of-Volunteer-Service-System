# -*- coding: utf-8 -*-

import codecs
import xml.etree.ElementTree as ET


# 读取待修改文件
updateTree = ET.parse("volun_qa.aiml")
root = updateTree.getroot()
f = codecs.open("志愿者常见问题问答.txt", 'r', 'utf8')
for line in f:
    # 创建新节点并添加为root的子节点
    category = ET.Element("category")
    root.append(category)

    fields = line.strip().split('|')
    if len(fields) < 2:
        break

    pattern = ET.Element("pattern")
    pattern.text = fields[0]
    category.append(pattern)

    template = ET.Element("template")
    template.text = fields[1]
    category.append(template)

f.close()

updateTree.write("volun_qa.aiml", encoding='utf-8')
