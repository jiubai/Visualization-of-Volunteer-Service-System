# -*- coding: utf-8 -*-

from pyhanlp import *
import csv
from numpy import zeros, log, ones


# 读取训练文本，准备训练数据
def loadDataSet():
    rootdir = 'D:/Pycharm/My_KG/Create_KG/QA_Data'   # 问答训练文本目录
    filelist = os.listdir(rootdir)  # 列出文件夹下所有文件
    TrainData = []
    classVec = []
    vocabSet = set()
    for i in range(0, len(filelist)):
        path = os.path.join(rootdir, filelist[i])
        classnow = filelist[i].split('_')[0]
        if os.path.isfile(path):
            with open(path, 'r', encoding='utf-8') as file:     # 顺序读取所有文件
                reader = csv.reader(file)
                for row in reader:
                    NowData = []
                    for term in HanLP.segment(row[0]):
                        if str(term.nature) != 'nx':
                            NowData.append(term.word)
                            vocabSet.add(term.word)
                    TrainData.append(NowData)
                    classVec.append(classnow)
    return TrainData, classVec, list(vocabSet)


# 词集模型
def setOfWords2Vec(vocabList, inputSet):
    returnVec = zeros(len(vocabList))   # 生成零向量的array
    for word in inputSet:
        if word in vocabList:
            returnVec[vocabList.index(word)] = 1  # 有单词，则该位置填充0
        else:
            print('the word:%s is not in my Vocabulary!' % word)
    return returnVec    # 返回全为0和1的向量


# 词袋模型
def bagOfWords2VecMN(vocabList, inputSet):
    returnVec = zeros(len(vocabList))
    for word in inputSet:
        if word in vocabList:
            returnVec[vocabList.index(word)] += 1
    return returnVec    # 返回非负整数的词向量


# 训练朴素贝叶斯模型，即准备各种概率数据
def trainNB(trainMatrix, trainCategory):
    numTrainData = len(trainMatrix)     # 数据条数
    numWord = len(trainMatrix[0])   # 向量长度
    numCategory = len(set(trainCategory))   # 统计种类
    categories = {}     # 存储各类概率
    for each in trainCategory:
        categories[each] = categories.get(each, 0) + 1
    for key in categories:
        categories[key] /= len(trainCategory)
    pNum = []   # ωk在ci中出现的次数
    pDemon = []     # ci中词总数
    for i in range(numCategory):
        pNum.append(ones(numWord))  # 初始化为1
        pDemon.append(2)    # 初始化为2
    for i in range(numTrainData):
        pNum[int(trainCategory[i])] += trainMatrix[i]
        pDemon[int(trainCategory[i])] += sum(trainMatrix[i])
    pVec = []   # p(ωk|ci)
    for i in range(numCategory):
        pVec.append(log(pNum[i]/pDemon[i]))  # 对结果求对数
    return pVec, categories


# 利用朴素贝叶斯模型进行分类
def classifyNB(inputVec, pVec, categories):
    p = []
    for i in range(len(categories)):
        p.append(sum(inputVec*pVec[i])+log(categories[str(i)]))
    return p.index(max(p))


def Classfy_Question(question):
    TrainData, classVec, vocabSet = loadDataSet()
    TrainData_Matrix = []
    for Data in TrainData:
        TrainData_Matrix.append(setOfWords2Vec(vocabSet, Data))

    pVec, categories = trainNB(TrainData_Matrix, classVec)

    # 测试部分，全对
    # for i in range(len(TrainData_Matrix)):
    #     ans = classifyNB(TrainData_Matrix[i], pVec, categories)
    #     if ans == int(classVec[i]):
    #         print("true")
    #     else:
    #         print("false")

    testEntry = []
    search_name = ''
    # inputstr = input('请输入字符串:')
    for term in HanLP.segment(question):
        testEntry.append(term.word)
        # print('{}\t{}'.format(term.word, term.nature))  # 获取单词与词性
        if str(term.nature) == 'nr':
            search_name = term.word
    thisDoc = setOfWords2Vec(vocabSet, testEntry)
    class_result = classifyNB(thisDoc, pVec, categories)
    return class_result, search_name
