# -*- coding: utf-8 -*-
'''
没有考虑流行度，感兴趣为1不感兴趣为0，后期将兴趣换成评分
'''

import random
import codecs
import datetime
import math


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

# 训练集中所有物品，未考虑流行度
def InitAllItemSet(train):
    allItemSet = set()
    for user, items in train.items():
        for i, r in items.items():
            allItemSet.add(i)
    return allItemSet

# 初始化候选物品池
def InitItems_Pool(items, allItemSet):
    interacted_items = set(items.keys())
    items_pool = list(allItemSet - interacted_items)
    return items_pool

# 随机负采样
def RandSelectNegativeSample(items, allItemSet):
    ret = dict()
    for i in items.keys():
        ret[i] = 1
    n = 0
    items_pool = InitItems_Pool(items, allItemSet)
    for i in range(0, len(items) * 3):
        item = items_pool[random.randint(0, len(items_pool) - 1)]
        if item in ret:
            continue
        ret[item] = 0
        n += 1
        if n > len(items):
            break
    return ret

# 推断某一用户对某一物品的感兴趣程度（评分）
def Predict(user, item, P, Q):
    rate = 0
    for f, puf in P[user].items():
        qif = Q[item][f]
        rate += puf * qif
    return rate


def InitModel(train, F):
    '''
    初始化P，Q矩阵，P为用户对隐分类的评分，Q为物品和隐分类的关系度，F为隐分类数
    '''
    P = dict()
    Q = dict()
    for user, items in train.items():
        P[user] = dict()
        for f in range(0, F):
            P[user][f] = random.random()
        for i, r in items.items():
            if i not in Q:
                Q[i] = dict()
                for f in range(0, F):
                    Q[i][f] = random.random()
    return P, Q


def LatentFactorModel(train, F, T, alpha, lamb):
    '''
    :param F: 隐分类数
    :param T: 迭代次数
    :param alpha: 学习速率
    :param lamb: 防止过拟合的正则参数
    '''
    print("Generating Model....")
    allItemSet = InitAllItemSet(train)
    [P, Q] = InitModel(train, F)
    for step in range(0, T):
        for user, items in train.items():
            samples = RandSelectNegativeSample(items, allItemSet)
            for item, rui in samples.items():
                eui = rui - Predict(user, item, P, Q)   # 计算损失
                for f in range(0, F):
                    P[user][f] += alpha * (eui * Q[item][f] - lamb * P[user][f])
                    Q[item][f] += alpha * (eui * P[user][f] - lamb * Q[item][f])
        alpha *= 0.9    # 学习速率逐步下降
    print("Generating Model Done!")
    return P, Q


def Recommend(user, train, P, Q, nitem=10):
    rank = dict()
    interacted_items = train[user]
    for i in Q:
        if i in interacted_items.keys():
            continue
        rank.setdefault(i, 0)
        for f, qif in Q[i].items():
            puf = P[user][f]
            rank[i] += puf * qif
    return dict(sorted(rank.items(), key=lambda x: x[1], reverse=True)[0:nitem])

def Recall(train, test, P, Q, N):
    hit = 0
    all = 0
    for user in train.keys():
        if user in test.keys():
            tu = test[user]
        else:
            continue
        rank = Recommend(user, train, P, Q, N)
        for item in rank:
            if item in tu:
                hit += 1
        all += len(tu)
    return hit / (all * 1.0)

def Precision(train, test, P, Q, N):
    hit = 0
    all = 0
    for user in train.keys():
        if user in test.keys():
            tu = test[user]
        else:
            continue
        rank = Recommend(user, train, P, Q, N)
        for item in rank:
            if item in tu:
                hit += 1
        all += N
    return hit / (all * 1.0)

def Coverage(train, P, Q, N):
    recommend_items = set()
    all_items = set()
    for user in train.keys():
        for item in train[user].keys():
            all_items.add(item)
        rank = Recommend(user, train, P, Q, N)
        for item in rank:
            recommend_items.add(item)
    return len(recommend_items) / (len(all_items) * 1.0)

def Popularity(train, P, Q, N):
    item_popularity = dict()
    for user, items in train.items():
        for item in items.keys():
            if item not in item_popularity:
                item_popularity[item] = 0
            item_popularity[item] += 1
    ret = 0
    n = 0
    for user in train.keys():
        rank = Recommend(user, train, P, Q, N)
        for item in rank:
            ret += math.log(1 + item_popularity[item])
            n += 1
    ret /= n * 1.0
    return ret


def testLFM_CF():
    productid2name = {}
    train, test = LodaData(productid2name)
    F = 5
    T = 30
    alpha = 0.02
    lamb = 0.01
    N = 10
    P, Q = LatentFactorModel(train, F, T, alpha, lamb)
    print(u'不同K值下推荐算法的各项指标(推荐物品数、精度、召回率、覆盖率、流行度)\n')
    print("%3s%20s%20s%20s%20s" % ('K', 'precision', 'recall', 'coverage', 'popularity'))
    recall = Recall(train, test, P, Q, N)
    precision = Precision(train, test, P, Q, N)
    coverage = Coverage(train, P, Q, N)
    popularity = Popularity(train, P, Q, N)
    print("%3d%19.2f%%%19.2f%%%19.2f%%%20.6f" % (N, precision * 100, recall * 100, coverage * 100, popularity))


if __name__ == "__main__":
    testLFM_CF()
