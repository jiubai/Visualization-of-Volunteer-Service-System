# -*- coding: utf-8 -*-
# LodaData()中改数据集切分比例，Recommend()改推荐物品数

import random
import codecs
import datetime
import math

# 将用户行为数据集按照均匀分布随机分成M份，划分训练集和测试集
def SplitData(data, M, k):
    test = {}
    train = {}
    nowTime = datetime.datetime.now().strftime("%Y%m%d%H%M%S")  # 生成当前时间作随机种子
    random.seed(int(nowTime))
    i = 0   # 统计测试集数量
    j = 0   # 统计训练集数量
    for user, item, rating in data:
        if random.randint(0, M) == k:
            i += 1
            if user in test:
                currentRatings = test[user]
            else:
                currentRatings = {}
            currentRatings[item] = rating
            test[user] = currentRatings
        else:
            j += 1
            if user in train:
                currentRatings = train[user]
            else:
                currentRatings = {}
            currentRatings[item] = rating
            train[user] = currentRatings
    print('test:', i, '  train:', j)
    return train, test

def LodaData(productid2name):
    data = []
    f = codecs.open("D:/Pycharm/Data/ml-100k/u.data", 'r', 'utf8')
    for line in f:
        fields = line.split('\t')
        user = fields[0]
        movie = fields[1]
        rating = int(fields[2])
        data.append([user, movie, rating])
    f.close()
    k = random.randint(0, 7)
    train, test = SplitData(data, 7, k)  # 随机划分

    f = codecs.open("D:/Pycharm/Data/ml-100k/u.item", 'r', 'iso8859-1', 'ignore')
    for line in f:
        # separate line into fields
        fields = line.split('|')
        mid = fields[0].strip()
        title = fields[1].strip()
        productid2name[mid] = title
    f.close()
    return train, test

# TopN推荐的预测准确率一般通过准确率（precision）/召回率（recall）度量
# 准确率代表推荐的物品有多少是有效的；召回率代表所需物品有多少被推荐了
def Recall(train, test, N):
    hit = 0
    all = 0
    nowTime = datetime.datetime.now().strftime("%Y%m%d%H%M%S")  # 生成当前时间作随机种子
    random.seed(int(nowTime))
    for user in train.keys():
        if user in test.keys():
            tu = test[user]
        else:
            continue
        for i in range(N):
            if str(random.randint(1, 1682)) in tu:
                hit += 1
        all += len(tu)
    return hit / (all * 1.0)

def Precision(train, test, N):
    hit = 0
    all = 0
    nowTime = datetime.datetime.now().strftime("%Y%m%d%H%M%S")  # 生成当前时间作随机种子
    random.seed(int(nowTime))
    for user in train.keys():
        if user in test.keys():
            tu = test[user]
        else:
            continue
        for i in range(N):
            if str(random.randint(1, 1682)) in tu:
                hit += 1
        all += N
    return hit / (all * 1.0)

def Coverage(train, N):
    recommend_items = set()
    all_items = set()
    nowTime = datetime.datetime.now().strftime("%Y%m%d%H%M%S")  # 生成当前时间作随机种子
    random.seed(int(nowTime))
    for user in train.keys():
        for item in train[user].keys():
            all_items.add(item)
        for i in range(N):
            item = str(random.randint(1, 1682))
            recommend_items.add(item)
    return len(recommend_items) / (len(all_items) * 1.0)

def Popularity(train, N):
    item_popularity = dict()
    nowTime = datetime.datetime.now().strftime("%Y%m%d%H%M%S")  # 生成当前时间作随机种子
    random.seed(int(nowTime))
    for user, items in train.items():
        for item in items.keys():
            if item not in item_popularity:
                item_popularity[item] = 0
            item_popularity[item] += 1
    ret = 0
    n = 0
    for user in train.keys():
        for i in range(N):
            item = str(random.randint(1, 1682))
            if item not in item_popularity:
                continue
            ret += math.log(1 + item_popularity[item])
            n += 1
    ret /= n * 1.0
    return ret

def Random():
    productid2name = {}
    train, test = LodaData(productid2name)
    N = 50
    print(u'不同K值下推荐算法的各项指标(推荐物品数、精度、召回率、覆盖率、流行度)\n')
    print("%3s%20s%20s%20s%20s" % ('N', 'precision', 'recall', 'coverage', 'popularity'))
    recall = Recall(train, test, N)
    precision = Precision(train, test, N)
    coverage = Coverage(train, N)
    popularity = Popularity(train, N)
    print("%3d%19.2f%%%19.2f%%%19.2f%%%20.6f" % (N, precision * 100, recall * 100, coverage * 100, popularity))


if __name__ == "__main__":
    Random()