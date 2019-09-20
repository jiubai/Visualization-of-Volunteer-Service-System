# -*- coding: utf-8 -*-

import os
import aiml
import xml.etree.ElementTree as ET


def get_alice():
    os.chdir('D:/Pycharm/My_KG/Create_KG/Bot_Data')  # 首先配置的语料库地址
    alice = aiml.Kernel()
    alice.learn("start_up.xml")  # 此处加载XML文件，即语料
    alice.respond('LOAD AIML PATTERN')
    return alice


def sentence_add_space(sentence):
    # 对输入的每句话进行隔字加空格处理
    list01 = list(sentence)
    list02 = []
    for i in range(len(list01)):
        if i == 0:
            list02.append(list01[i])
        else:
            list02.append(" ")
            list02.append(list01[i])
    str_sentence = str()
    for i in list02:
        str_sentence += i
    return str_sentence


def KGQA_Answer(quiz):
    alice = get_alice()
    result = alice.respond(quiz)
    if result:
        return result
    else:
        return quiz + '???'


# alice = get_alice()
# while True:
#     question = input("Enter your message >> ")
#     result = alice.respond(question)
#     if result:
#         print(result)
#     else:
#         print('我不知道这个问题诶，请你下一句告诉我答案啊！！')
#         updateTree = ET.parse("learning_chat.aiml")
#         root = updateTree.getroot()
#
#         category = ET.Element("category")
#         root.append(category)
#
#         pattern = ET.Element("pattern")
#         pattern.text = question
#         category.append(pattern)
#
#         answer = input("Enter your answer >> ")
#         print('我学会了，你可以再说一遍了！')
#
#         template = ET.Element("template")
#         template.text = answer
#         category.append(template)
#
#         updateTree.write("learning_chat.aiml", encoding='utf-8')
#
#         alice.learn("start_up.xml")  # 此处重新加载语料
#         alice.respond('LOAD AIML PATTERN')

