# -*- coding: utf-8 -*-

import random
import codecs
from Recommend_Algorithm.MovieLens.Distance import ItemCos
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
        if int(movie) > 1000:
            continue
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

def ItemSimilarity_Cos(train, productid2name):
    print('Generating ItemSim...')
    num = 0
    ItemSim = dict()
    for i in productid2name:
        ItemSim.setdefault(i, {})
        for j in productid2name:
            if i == j:
                ItemSim[i][j] = 0
                continue
            ItemSim[i][j] = ItemCos(i, j, train)
            num += 1
            print(num)
    print('Generating ItemSim Done!')
    return ItemSim

def Recommend(ItemSim, user, train, k=8, nitem=10):
    """
    给用户推荐nitem个物品，物品来源于与用户k个偏好物品的相似物品
    """
    rank = dict()
    interacted_items = train[user]
    for i, pi in interacted_items.items():
        for j, wj in sorted(ItemSim[i].items(), key=lambda c: c[1], reverse=True)[0:k]:
            if j in interacted_items:
                continue
            rank.setdefault(j, 0)
            rank[j] += pi * wj
    return dict(sorted(rank.items(), key=lambda c: c[1], reverse=True)[0:nitem])


def Recall(train, test, ItemSim, N):
    hit = 0
    all = 0
    for user in train.keys():
        if user in test.keys():
            tu = test[user]
        else:
            continue
        rank = Recommend(ItemSim, user, train, N)
        for item in rank:
            if item in tu:
                hit += 1
        all += len(tu)
    return hit / (all * 1.0)

def Precision(train, test, ItemSim, N):
    hit = 0
    all = 0
    for user in train.keys():
        if user in test.keys():
            tu = test[user]
        else:
            continue
        rank = Recommend(ItemSim, user, train, N)
        for item in rank:
            if item in tu:
                hit += 1
        all += 10
    return hit / (all * 1.0)

def Coverage(train, ItemSim, N):
    recommend_items = set()
    all_items = set()
    for user in train.keys():
        for item in train[user].keys():
            all_items.add(item)
        rank = Recommend(ItemSim, user, train, N)
        for item in rank:
            recommend_items.add(item)
    return len(recommend_items) / (len(all_items) * 1.0)

def Popularity(train, ItemSim, N):
    item_popularity = dict()
    for user, items in train.items():
        for item in items.keys():
            if item not in item_popularity:
                item_popularity[item] = 0
            item_popularity[item] += 1
    ret = 0
    n = 0
    for user in train.keys():
        rank = Recommend(ItemSim, user, train, N)
        for item in rank:
            ret += math.log(1 + item_popularity[item])
            n += 1
    ret /= n * 1.0
    return ret

def testRecommend():
    productid2name = {}
    train, test = LodaData(productid2name)
    ItemSim = ItemSimilarity_Cos(train, productid2name)
    user = "344"
    rank = Recommend(ItemSim, user, train, k=3)
    print(u'给id为344的用户推荐10部电影：\n')
    for i in rank.keys():
        print(productid2name[i])

def testItemBasedCF():
    productid2name = {}
    train, test = LodaData(productid2name)
    ItemSim = ItemSimilarity_Cos(train, productid2name)
    print(u'不同K值下推荐算法的各项指标(相似用户数、精度、召回率、覆盖率、流行度)\n')
    print("%3s%20s%20s%20s%20s" % ('K', 'precision', 'recall', 'coverage', 'popularity'))
    for k in [1, 3, 5, 10, 20, 40]:
        recall = Recall(train, test, ItemSim, k)
        precision = Precision(train, test, ItemSim, k)
        coverage = Coverage(train, ItemSim, k)
        popularity = Popularity(train, ItemSim, k)
        print("%3d%19.2f%%%19.2f%%%19.2f%%%20.6f" % (k, precision * 100, recall * 100, coverage * 100, popularity))


if __name__ == "__main__":
    testItemBasedCF()