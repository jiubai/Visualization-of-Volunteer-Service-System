# -*- coding: utf-8 -*-

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

# 计算评分差值矩阵
def computeDeviations(train):
    frequencies = {}
    deviations = {}
    print("Generating the Deviations....")
    for ratings in train.values():
        for (item, rating) in ratings.items():
            frequencies.setdefault(item, {})
            deviations.setdefault(item, {})
            for (item2, rating2) in ratings.items():
                if item != item2:
                    frequencies[item].setdefault(item2, 0)
                    deviations[item].setdefault(item2, 0.0)
                    frequencies[item][item2] += 1
                    deviations[item][item2] += rating - rating2

    for (item, ratings) in deviations.items():
        for item2 in ratings:
            ratings[item2] /= frequencies[item][item2]
    print("Generating the Deviations done!!")
    return deviations, frequencies

# 推荐nitem件物品
def Recommend(deviations, frequencies, userRatings, nitem=10):
    recommendations = {}
    num = {}
    for (userItem, userRating) in userRatings.items():
        for (diffItem, diffRatings) in deviations.items():
            if diffItem not in userRatings and userItem in deviations[diffItem]:
                freq = frequencies[diffItem][userItem]
                recommendations.setdefault(diffItem, 0.0)
                num.setdefault(diffItem, 0)
                recommendations[diffItem] += (diffRatings[userItem] + userRating) * freq
                num[diffItem] += freq
    recommendations = [(k, v / num[k]) for (k, v) in recommendations.items()]
    recommendations.sort(key=lambda artistTuple: artistTuple[1], reverse=True)
    return dict(recommendations[:nitem])

def Recall(train, test, deviations, frequencies, N):
    hit = 0
    all = 0
    for user in train:
        if user in test.keys():
            tu = test[user]
        else:
            continue
        userRatings = train[user]
        rank = Recommend(deviations, frequencies, userRatings, N)
        for item in rank:
            if item in tu:
                hit += 1
        all += len(tu)
    return hit / (all * 1.0)

def Precision(train, test, deviations, frequencies, N):
    hit = 0
    all = 0
    for user in train:
        if user in test.keys():
            tu = test[user]
        else:
            continue
        userRatings = train[user]
        rank = Recommend(deviations, frequencies, userRatings, N)
        for item in rank:
            if item in tu:
                hit += 1
        all += N
    return hit / (all * 1.0)

def Coverage(train, deviations, frequencies, N):
    recommend_items = set()
    all_items = set()
    for user in train:
        for item in train[user].keys():
            all_items.add(item)
        userRatings = train[user]
        rank = Recommend(deviations, frequencies, userRatings, N)
        for item in rank:
            recommend_items.add(item)
    return len(recommend_items) / (len(all_items) * 1.0)

def Popularity(train, deviations, frequencies, N):
    item_popularity = dict()
    for user, items in train.items():
        for item in items.keys():
            if item not in item_popularity:
                item_popularity[item] = 0
            item_popularity[item] += 1
    ret = 0
    n = 0
    for user in train:
        userRatings = train[user]
        rank = Recommend(deviations, frequencies, userRatings, N)
        for item in rank:
            ret += math.log(1 + item_popularity[item])
            n += 1
    ret /= n * 1.0
    return ret

def testRecommend():
    productid2name = {}
    train, test = LodaData(productid2name)
    deviations, frequencies = computeDeviations(train)
    user = "25"
    rank = Recommend(deviations, frequencies, train[user])
    print(u'给id为25的用户推荐10部电影：\n')
    for i in rank.keys():
        print(productid2name[i])


def testSlope_One():
    productid2name = {}
    train, test = LodaData(productid2name)
    deviations, frequencies = computeDeviations(train)
    N = 10
    print(u'不同K值下推荐算法的各项指标(推荐物品数、精度、召回率、覆盖率、流行度)\n')
    print("%3s%20s%20s%20s%20s" % ('K', 'precision', 'recall', 'coverage', 'popularity'))
    recall = Recall(train, test, deviations, frequencies, N)
    precision = Precision(train, test, deviations, frequencies, N)
    coverage = Coverage(train, deviations, frequencies, N)
    popularity = Popularity(train, deviations, frequencies, N)
    print("%3d%19.2f%%%19.2f%%%19.2f%%%20.6f" % (10, precision * 100, recall * 100, coverage * 100, popularity))


if __name__ == "__main__":
    testSlope_One()