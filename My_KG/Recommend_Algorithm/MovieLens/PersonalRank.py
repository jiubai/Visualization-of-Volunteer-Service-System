# -*- coding: utf-8 -*-
'''
没有考虑评分，后续可以考虑评分来调整游走概率，以及算法的加速的改进
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
        movie = fields[1] + 'm'
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

def BuildGraph(train):
    G = dict()
    for user, items in train.items():
        G[user] = items
        for item in items:
            if item not in G:
                G[item] = dict()
                G[item][user] = train[user][item]
            else:
                G[item][user] = train[user][item]
    return G

def PersonalRank(G, alpha, root, max_step):
    rank = {x: 0 for x in G.keys()}
    rank[root] = 1
    # 开始迭代
    for k in range(max_step):
        tmp = {x: 0 for x in G.keys()}
        # 取节点i和它的出边尾节点集合ri
        for i, ri in G.items():
            # 取节点i的出边的尾节点j以及边E(i,j)的权重wij, 边的权重都为1，归一化之后就上1/len(ri)
            for j, wij in ri.items():
                # i是j的其中一条入边的首节点，因此需要遍历图找到j的入边的首节点，
                # 这个遍历过程就是此处的2层for循环，一次遍历就是一次游走
                tmp[j] += alpha * rank[i] / (1.0 * len(ri))
        # 我们每次游走都是从root节点出发，因此root节点的权重需要加上(1 - alpha)
        tmp[root] += (1 - alpha)
        rank = tmp

    return dict(sorted(rank.items(), key=lambda x: x[1], reverse=True))

def Recommend(G, train, user, alpha, max_step, nitem=10):
    tmp = PersonalRank(G, alpha, user, max_step)
    rank = dict()
    interacted_items = train[user]
    for i in tmp:
        if i in interacted_items.keys() or i in train:
            continue
        rank.setdefault(i, 0)
        rank[i] = tmp[i]
    return dict(sorted(rank.items(), key=lambda x: x[1], reverse=True)[0:nitem])

def Recall(train, test, G, alpha, max_step, N):
    hit = 0
    all = 0
    for user in train.keys():
        if user in test.keys():
            tu = test[user]
        else:
            continue
        rank = Recommend(G, train, user, alpha, max_step, N)
        for item in rank:
            if item in tu:
                hit += 1
        all += len(tu)
    return hit / (all * 1.0)

def Precision(train, test, G, alpha, max_step, N):
    hit = 0
    all = 0
    for user in train.keys():
        if user in test.keys():
            tu = test[user]
        else:
            continue
        rank = Recommend(G, train, user, alpha, max_step, N)
        for item in rank:
            if item in tu:
                hit += 1
        all += N
    return hit / (all * 1.0)

def Coverage(train, G, alpha, max_step, N):
    recommend_items = set()
    all_items = set()
    for user in train.keys():
        for item in train[user].keys():
            all_items.add(item)
        rank = Recommend(G, train, user, alpha, max_step, N)
        for item in rank:
            recommend_items.add(item)
    return len(recommend_items) / (len(all_items) * 1.0)

def Popularity(train, G, alpha, max_step, N):
    item_popularity = dict()
    for user, items in train.items():
        for item in items.keys():
            if item not in item_popularity:
                item_popularity[item] = 0
            item_popularity[item] += 1
    ret = 0
    n = 0
    for user in train.keys():
        rank = Recommend(G, train, user, alpha, max_step, N)
        for item in rank:
            ret += math.log(1 + item_popularity[item])
            n += 1
    ret /= n * 1.0
    return ret


def testPersonal_Rank_CF():
    productid2name = {}
    train, test = LodaData(productid2name)
    G = BuildGraph(train)
    alpha = 0.8
    max_step = 10
    N = 10
    print(u'不同K值下推荐算法的各项指标(推荐物品数、精度、召回率、覆盖率、流行度)\n')
    print("%3s%20s%20s%20s%20s" % ('K', 'precision', 'recall', 'coverage', 'popularity'))
    recall = Recall(train, test, G, alpha, max_step, N)
    precision = Precision(train, test, G, alpha, max_step, N)
    coverage = Coverage(train, G, alpha, max_step, N)
    popularity = Popularity(train, G, alpha, max_step, N)
    print("%3d%19.2f%%%19.2f%%%19.2f%%%20.6f" % (N, precision * 100, recall * 100, coverage * 100, popularity))


if __name__ == '__main__':
    testPersonal_Rank_CF()