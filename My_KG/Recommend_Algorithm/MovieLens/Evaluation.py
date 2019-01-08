# -*- coding: utf-8 -*-

import math


def Recommend(user, N):
    pass


# 个列表records存放用户评分数据，令records[i] = [u,i,rui,pui]，其
# 中rui是用户u对物品i的实际评分，pui是算法预测出来的用户u对物品i的评分
def RMSE(records):
    return math.sqrt(sum([(rui-pui)*(rui-pui) for u, i, rui, pui in records])/float(len(records)))
# 均方根误差（RMSE）和平均绝对误差（MAE）作为评分预测的预测准确度
def MAE(records):
    return sum([abs(rui-pui) for u, i, rui, pui in records])/float(len(records))


# TopN推荐的预测准确率一般通过准确率（precision）/召回率（recall）度量
# 准确率代表推荐的物品有多少是有效的；召回率代表所需物品有多少被推荐了
def Recall(train, test, N):
    hit = 0
    all = 0
    for user in train.keys():
        tu = test[user]
        rank = Recommend(user, N)
        for item, pui in rank:
            if item in tu:
                hit += 1
        all += len(tu)
    return hit / (all * 1.0)

def Precision(train, test, N):
    hit = 0
    all = 0
    for user in train.keys():
        tu = test[user]
        rank = Recommend(user, N)
        for item, pui in rank:
            if item in tu:
                hit += 1
        all += N
    return hit / (all * 1.0)


def Coverage(train, test, result, N=5000):
    recommend_items = set()
    all_items = set()
    for user in train.keys():
        for item in train[user].keys():
            all_items.add(item)

    for user in test.keys():
        rank = Recommend(result, user, N)
        for item, pui in rank:
            recommend_items.add(item)
    return len(recommend_items) / (len(all_items) * 1.0)


def Popularity(train, test, N):
    item_popularity = dict()
    for user, items in train.items():
        for item in items.keys():
            if item not in item_popularity:
                item_popularity[item] = 0
            item_popularity[item] += 1
    ret = 0
    n = 0
    for user in train.keys():
        rank = Recommend(user, N)
        for item, pui in rank:
            ret += math.log(1 + item_popularity[item])
            n += 1
    ret /= n * 1.0
    return ret
