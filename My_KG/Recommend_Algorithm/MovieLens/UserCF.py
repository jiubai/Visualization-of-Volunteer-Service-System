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

def UserSimilarity(train):
    """
    生成用户相似度矩阵
    """
    userSim = dict()
    print('Generating userSim...')
    for u in train.keys():
        for v in train.keys():
            if u == v:
                continue
            userSim.setdefault(u, {})
            userSim[u][v] = len(set(train[u].keys()) & set(train[v].keys()))
            userSim[u][v] /= math.sqrt(len(train[u]) * len(train[v]) * 1.0)
    print('Generating userSim Done!')
    return userSim

# 给用户推荐K个与之相似用户喜欢的nitem个物品
def Recommend(userSim, user, train, k=8, nitem=10):
    rank = dict()
    interacted_items = train.get(user, {})
    for v, wuv in sorted(userSim[user].items(), key=lambda x: x[1], reverse=True)[0:k]:
        for i, rvi in train[v].items():
            if i in interacted_items:
                continue
            rank.setdefault(i, 0)   # 如果键不存在于字典中，将会添加键并将值设为默认值
            rank[i] += wuv * rvi
    return dict(sorted(rank.items(), key=lambda x: x[1], reverse=True)[0:nitem])

# TopN推荐的预测准确率一般通过准确率（precision）/召回率（recall）度量
# 准确率代表推荐的物品有多少是有效的；召回率代表所需物品有多少被推荐了
def Recall(train, test, userSim, N):
    hit = 0
    all = 0
    for user in train.keys():
        if user in test.keys():
            tu = test[user]
        else:
            continue
        rank = Recommend(userSim, user, train, N)
        for item in rank:
            if item in tu:
                hit += 1
        all += len(tu)
    return hit / (all * 1.0)

def Precision(train, test, userSim, N):
    hit = 0
    all = 0
    for user in train.keys():
        if user in test.keys():
            tu = test[user]
        else:
            continue
        rank = Recommend(userSim, user, train, N)
        for item in rank:
            if item in tu:
                hit += 1
        all += 10
    return hit / (all * 1.0)

def Coverage(train, userSim, N):
    recommend_items = set()
    all_items = set()
    for user in train.keys():
        for item in train[user].keys():
            all_items.add(item)
        rank = Recommend(userSim, user, train, N)
        for item in rank:
            recommend_items.add(item)
    return len(recommend_items) / (len(all_items) * 1.0)

def Popularity(train, userSim, N):
    item_popularity = dict()
    for user, items in train.items():
        for item in items.keys():
            if item not in item_popularity:
                item_popularity[item] = 0
            item_popularity[item] += 1
    ret = 0
    n = 0
    for user in train.keys():
        rank = Recommend(userSim, user, train, N)
        for item in rank:
            ret += math.log(1 + item_popularity[item])
            n += 1
    ret /= n * 1.0
    return ret

def testRecommend():
    productid2name = {}
    train, test = LodaData(productid2name)
    userSim = UserSimilarity(train)
    user = "344"
    rank = Recommend(userSim, user, train, k=3)
    print(u'给id为344的用户推荐10部电影：\n')
    for i in rank.keys():
        print(productid2name[i])


def testUserBasedCF():
    productid2name = {}
    train, test = LodaData(productid2name)
    userSim = UserSimilarity(train)
    print(u'不同K值下推荐算法的各项指标(相似用户数、精度、召回率、覆盖率、流行度)\n')
    print("%3s%20s%20s%20s%20s" % ('K', 'precision', 'recall', 'coverage', 'popularity'))
    for k in [5, 10, 20, 40, 80, 120, 160]:
        recall = Recall(train, test, userSim, k)
        precision = Precision(train, test, userSim, k)
        coverage = Coverage(train, userSim, k)
        popularity = Popularity(train, userSim, k)
        print("%3d%19.2f%%%19.2f%%%19.2f%%%20.6f" % (k, precision * 100, recall * 100, coverage * 100, popularity))


if __name__ == "__main__":
    testUserBasedCF()