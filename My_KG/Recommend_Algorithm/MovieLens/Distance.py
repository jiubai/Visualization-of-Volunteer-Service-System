# -*- coding: utf-8 -*-

from math import sqrt


# 曼哈顿距离
def manhattan(rating1, rating2):
    """Computes the Manhattan distance. Both rating1 and rating2 are dictionaries
       of the form {'The Strokes': 3.0, 'Slightly Stoopid': 2.5}"""
    distance = 0
    total = 0
    for key in rating1:
        if key in rating2:
            distance += abs(rating1[key] - rating2[key])
            total += 1
    if total > 0:
        return distance / total
    else:
        return -1 #Indicates no ratings in common


# 闵科夫斯基距离
def minkowski(rating1, rating2, r):
    distance = 0
    for key in rating1:
        if key in rating2:
            distance += pow(abs(rating1[key] - rating2[key]), r)
    return pow(distance, 1.0 / r)


# 皮尔逊系数
def pearson(rating1, rating2):
    sum_xy = 0
    sum_x = 0
    sum_y = 0
    sum_x2 = 0
    sum_y2 = 0
    n = 0
    for key in rating1:
        if key in rating2:
            n += 1
            x = rating1[key]
            y = rating2[key]
            sum_xy += x * y
            sum_x += x
            sum_y += y
            sum_x2 += pow(x, 2)
            sum_y2 += pow(y, 2)
    # now compute denominator
    denominator = sqrt(sum_x2 - pow(sum_x, 2) / n) * sqrt(sum_y2 - pow(sum_y, 2) / n)
    if denominator == 0:
        return 0
    else:
        return (sum_xy - (sum_x * sum_y) / n) / denominator


# 用户修正的余弦相似度
def Cosin(rating1, rating2):
    avg1 = (float(sum(rating1.values())) / len(rating1.values()))
    avg2 = (float(sum(rating2.values())) / len(rating2.values()))
    num = 0     # 分子
    dem1 = 0    # 分母的第一部分
    dem2 = 0
    for key in rating1:
        if key in rating2:
            num += (rating1[key] - avg1) * (rating2[key] - avg2)
            dem1 += (rating1[key] - avg1) ** 2
            dem2 += (rating2[key] - avg2) ** 2
    return num / (sqrt(dem1) * sqrt(dem2) + 1)


# 物品修正的余弦相似度
def ItemCos(item1, item2, train):
    averages = {}
    for (key, ratings) in train.items():
        averages[key] = (float(sum(ratings.values())) / len(ratings.values()))

    num = 0     # 分子
    dem1 = 0    # 分母的第一部分
    dem2 = 0
    for (user, ratings) in train.items():
        if item1 in ratings and item2 in ratings:
            avg = averages[user]
            num += (ratings[item1] - avg) * (ratings[item2] - avg)
            dem1 += (ratings[item1] - avg) ** 2
            dem2 += (ratings[item2] - avg) ** 2
    # if num == 0:
    #     return -1
    return num / (sqrt(dem1) * sqrt(dem2) + 1)
