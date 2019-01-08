# -*- coding: utf-8 -*-
import tensorflow as tf
import argparse     # python标准库里面用来处理命令行参数的库
import os.path
import math
import operator
import random
import datetime
import pandas as pd
import numpy as np
from collections import Counter


class TransE:
    @property
    def entity2id(self):
        return self.__entity2id

    @property
    def dimension(self):
        return self.__dimension

    @property
    def num_entity(self):
        return self.__num_entity

    def __init__(self, data_dir, negative_sampling, learning_rate,
                 batch_size, max_iter, margin, dimension, norm, evaluation_size, regularizer_weight):
        # this part for the data:
        self.__data_dir = data_dir
        self.__negative_sampling = negative_sampling
        self.__regularizer_weight = regularizer_weight
        self.__norm = norm

        self.__entity2id = {}
        self.__id2entity = {}

        self.__num_entity = 0

        # load file: entity2id.txt 只需要实体_id对应用于构建实体相似度矩阵
        self.load_data()
        print('finish preparing data. ')

        # this part for the model:
        self.__learning_rate = learning_rate
        self.__batch_size = batch_size
        self.__max_iter = max_iter
        self.__margin = margin
        self.__dimension = dimension
        self.__evaluation_size = evaluation_size

    def load_data(self):
        print('loading entity2id.txt ...')
        with open(os.path.join(self.__data_dir, 'entity2id.txt'), 'r', encoding='utf-8') as f:
            self.__entity2id = {line.strip().split(',')[0]: int(line.strip().split(',')[1]) for line in f.readlines()}
            self.__id2entity = {value: key for key, value in self.__entity2id.items()}

        self.__num_entity = len(self.__entity2id)
        print('entity number: ' + str(self.__num_entity))


# 将用户行为数据集按照均匀分布随机分成M份，划分训练集和测试集
def SplitData(data, M=5):
    nowTime = datetime.datetime.now().strftime("%Y%m%d%H%M%S")  # 生成当前时间作随机种子
    random.seed(int(nowTime))

    data_df = pd.DataFrame(data, columns=['vol', 'opp', 'score', 'num'])
    data_df = data_df.sort_values(by=['num', 'vol'], ascending=False).reset_index(drop=True)
    # users去重
    data2 = data_df.values
    # 用户数目
    users_num = len(set(data2[:, 0]))

    i = 0
    test = []
    train = []
    while i < users_num:
        i += 1
        num = int(data2[0][3])
        test_num = int(round(num / float(M)))

        # 对用户随机选取test_num个元素进入test
        for ii in range(test_num):
            index = random.randint(0, num - 1 - ii)
            test.append(data2[index][:3])
            # np.delete使用一定要小心，3个参数不能少，少最后一个参数，默认合一起
            data2 = np.delete(data2, index, 0)

        # 用户剩余数据进入train
        for ii in range(num - test_num):
            train.append(data2[0][:3])
            data2 = np.delete(data2, 0, 0)
    return train, test


# 把数据读取成：[用户id，物品id，评分]
def readData(filepath):
    if filepath == None:
        print('请输入地址！')
        return None

    # 读取的数据，每个三元组有且仅出现一次
    ori_data = []
    with open(filepath, 'r', encoding='UTF-8') as f:
        while f.readline():
            ori_data.append(f.readline().strip().split(','))

    data = []   # 记录志愿者参加的项目
    items = set()   # 记录所有项目
    for line in ori_data:
        try:
            if line[1] == 'Participate_In':
                data.append([line[0], line[2], 1])
                items.add(line[2])
        except:
            i = 1

    users = []  # 记录参加过项目的所有志愿者
    for i in data:
        users.append(i[0])
    users_num = Counter(users)
    users_num = sorted(users_num.items(), key=operator.itemgetter(1), reverse=True)

    data_df = pd.DataFrame(data, columns=['vol', 'opp', 'score'])   # score均为1，代表参加过
    users_num_df = pd.DataFrame(users_num, columns=['vol', 'num'])
    data_df = pd.merge(data_df, users_num_df, how='left', on='vol')
    data_df = data_df.sort_values(by='num', ascending=False).reset_index(drop=True)
    output = data_df.values
    return output, list(items)


def transform(oriData):
    ret = dict()
    for user, item, rating in oriData:
        if user not in ret:
            ret[user] = dict()
        ret[user][item] = rating
    return ret


# 传入参数items为实体列表
def ItemSimilarity(items):
    parser = argparse.ArgumentParser(description="TransE")  # 创建一个解析对象，description代表-help时显示的开始文字
    # parser.add_argument()向该对象中添加你要关注的命令行参数和选项
    parser.add_argument('--data_dir', dest='data_dir', type=str, help='the directory of dataset', default='./test_data/')
    parser.add_argument('--learning_rate', dest='learning_rate', type=float, help='learning rate', default=0.01)
    parser.add_argument('--batch_size', dest='batch_size', type=int, help="batch size", default=4096)
    parser.add_argument('--max_iter', dest='max_iter', type=int, help='maximum interation', default=100)
    parser.add_argument('--optimizer', dest='optimizer', type=str, help='optimizer', default='adam')
    parser.add_argument('--dimension', dest='dimension', type=int, help='embedding dimension', default=50)
    parser.add_argument('--margin', dest='margin', type=float, help='margin', default=1.0)
    parser.add_argument('--norm', dest='norm', type=str, help='L1 or L2 norm', default='L1')
    parser.add_argument('--evaluation_size', dest='evaluation_size', type=int, help='batchsize for evaluation', default=500)
    parser.add_argument('--negative_sampling', dest='negative_sampling', type=str, help='choose unit or bern to generate negative examples', default='bern')
    parser.add_argument('--evaluate_per_iteration', dest='evaluate_per_iteration', type=int, help='evaluate the training result per x iteration', default=10)
    parser.add_argument('--evaluate_worker', dest='evaluate_worker', type=int, help='number of evaluate workers', default=4)
    parser.add_argument('--regularizer_weight', dest='regularizer_weight', type=float, help='regularization weight', default=1e-5)
    parser.add_argument('--n_test', dest='n_test', type=int, help='number of triples for test during the training', default=300)
    args = parser.parse_args()
    print(args)
    # 调取模型
    model = TransE(negative_sampling=args.negative_sampling, data_dir=args.data_dir,
                   learning_rate=args.learning_rate, batch_size=args.batch_size,
                   max_iter=args.max_iter, margin=args.margin,
                   dimension=args.dimension, norm=args.norm, evaluation_size=args.evaluation_size,
                   regularizer_weight=args.regularizer_weight)

    bound = 6 / math.sqrt(model.dimension)
    embedding_entity = tf.get_variable('embedding_entity', [model.num_entity, model.dimension], initializer=tf.random_uniform_initializer(minval=-bound, maxval=bound, seed=123))

    saver = tf.train.Saver()
    W = dict()  # 实体相似度矩阵

    with tf.Session() as session:
        init_op = tf.global_variables_initializer()
        session.run(init_op)

        saver.restore(session, './model/transe')    # 调取模型
        embedding_entity = session.run(embedding_entity)    # 读取嵌入实体向量
        entity2id = model.entity2id

        # 为所有实体由嵌入向量构建相似度矩阵（存储向量差值的倒数即越大越像）
        for i in items:
            W.setdefault(i, {})
            for j in items:
                if i == j:
                    continue
                dist = sum((abs(embedding_entity[entity2id[i]]-embedding_entity[entity2id[j]])))
                W[i][j] = 1/(dist+1)
    return W


def Recommend(W, user_id, train, nitem=3):
    rank = dict()
    ru = train[user_id]
    for i, pi in ru.items():
        for j, wij in sorted(W[i].items(), key=operator.itemgetter(1), reverse=True):
            if j in ru:
                continue
            rank.setdefault(j, 0)
            rank[j] += pi * wij
    return dict(sorted(rank.items(), key=lambda c: c[1], reverse=True)[0:nitem])


def Recall(train, test, ItemSim):
    hit = 0
    all = 0
    for user in train.keys():
        if user in test.keys():
            tu = test[user]
        else:
            continue
        rank = Recommend(ItemSim, user, train)
        for item in rank:
            if item in tu:
                hit += 1
        all += len(tu)
    return hit / (all * 1.0)

def Precision(train, test, ItemSim):
    hit = 0
    all = 0
    for user in train.keys():
        if user in test.keys():
            tu = test[user]
        else:
            continue
        rank = Recommend(ItemSim, user, train)
        for item in rank:
            if item in tu:
                hit += 1
        all += 3
    return hit / (all * 1.0)

def Coverage(train, ItemSim):
    recommend_items = set()
    all_items = set()
    for user in train.keys():
        for item in train[user].keys():
            all_items.add(item)
        rank = Recommend(ItemSim, user, train)
        for item in rank:
            recommend_items.add(item)
    return len(recommend_items) / (len(all_items) * 1.0)

def Popularity(train, ItemSim):
    item_popularity = dict()
    for user, items in train.items():
        for item in items.keys():
            if item not in item_popularity:
                item_popularity[item] = 0
            item_popularity[item] += 1
    ret = 0
    n = 0
    for user in train.keys():
        rank = Recommend(ItemSim, user, train)
        for item in rank:
            ret += math.log(1 + item_popularity[item])
            n += 1
    ret /= n * 1.0
    return ret

if __name__ == "__main__":
    data, items = readData('./test_data/data.txt')
    W = ItemSimilarity(items)
    oriTrain, oriTest = SplitData(data, 4)
    train = transform(oriTrain)
    test = transform(oriTest)

    recall = Recall(train, test, W)
    precision = Precision(train, test, W)
    coverage = Coverage(train, W)
    popularity = Popularity(train, W)
    print("%3s%20s%20s%20s%20s" % ('推荐数', 'precision', 'recall', 'coverage', 'popularity'))
    print("%3d%19.2f%%%19.2f%%%19.2f%%%20.6f" % (3, precision * 100, recall * 100, coverage * 100, popularity))




