# -*- coding: utf-8 -*-


def loadDataSet():
    return [[1,2,5],[2,4],[2,3],[1,2,4],[1,3],[2,3],[1,3],[1,2,3,5],[1,2,3]]


# 构建候选1项集C1
def createC1(dataSet):
    C1 = []
    for transaction in dataSet:
        for item in transaction:
            if not [item] in C1:
                C1.append([item])
    C1.sort()
    return list(map(frozenset, C1))


# 将候选集Ck转换为频繁项集Lk
# D：原始数据集
# Cn: 候选集项Ck
# minSupport:支持度的最小值
def scanD(D, Ck, minSupport):
    # 候选集计数
    ssCnt = {}
    # 数据集过滤
    D2 = [item for item in D if len(item) >= len(Ck[0])]
    for tid in D2:
        for can in Ck:
            if can.issubset(tid):
                if can not in ssCnt.keys():
                    ssCnt[can] = 1
                else:
                    ssCnt[can] += 1
    numItems = float(len(D))
    Lk= []     # 候选集项Cn生成的频繁项集Lk
    supportData = {}    # 候选集项Cn的支持度字典
    # 计算候选项集的支持度, supportData key:候选项， value:支持度
    for key in ssCnt:
        support = ssCnt[key] / numItems
        if support >= minSupport:
            Lk.append(key)
        supportData[key] = support
    return Lk, supportData


# 将频繁k-1项集转换为候选k项集
def aprioriGen(Lk_1, k):
    Ck = []
    lenLk = len(Lk_1)
    for i in range(lenLk):
        L1 = Lk_1[i]
        for j in range(i + 1, lenLk):
            L2 = Lk_1[j]
            if len(L1 & L2) == k - 2:
                L1_2 = L1 | L2
                if L1_2 not in Ck:
                    Ck.append(L1_2)
    return Ck


def apriori(dataSet, minSupport = 0.5):
    C1 = createC1(dataSet)
    L1, supportData = scanD(dataSet, C1, minSupport)    # 得到频繁项集和支持度
    L = [L1]
    k = 2   # 候选k项集的值
    while(len(L[k-2])>0):
        Lk_1 = L[k-2]
        Ck = aprioriGen(Lk_1, k)
        # print("ck:", Ck)
        Lk, supK = scanD(dataSet, Ck, minSupport)
        supportData.update(supK)
        # print("lk:", Lk)
        L.append(Lk)
        k += 1
    return L, supportData


# 生成关联规则
# L: 频繁项集列表
# supportData: 包含频繁项集支持数据的字典
# minConf 最小置信度
def generateRules(L, supportData, minConf=0.7):
    # 包含置信度的规则列表
    bigRuleList = []
    # 从频繁2项集开始遍历
    for i in range(1, len(L)):
        for freqSet in L[i]:
            H1 = [frozenset([item]) for item in freqSet]
            if i > 1:
                rulesFromConseq(freqSet, H1, supportData, bigRuleList, minConf)
            else:   # 2项频繁集直接计算最小可信度
                calcConf(freqSet, H1, supportData, bigRuleList, minConf)
    return bigRuleList


# 计算是否满足最小可信度
def calcConf(freqSet, H, supportData, brl, minConf=0.7):
    prunedH = []
    # 用每个conseq作为后件
    for conseq in H:
        # 计算置信度
        conf = supportData[freqSet] / supportData[freqSet - conseq]
        if conf >= minConf:
            print(freqSet - conseq, '-->', conseq, 'conf:', conf)
            # 元组中的三个元素：前件、后件、置信度
            brl.append((freqSet - conseq, conseq, conf))
            prunedH.append(conseq)
    # 返回后件列表
    return prunedH


# 对规则进行评估
def rulesFromConseq(freqSet, H, supportData, brl, minConf=0.7):
    m = len(H[0])
    if len(freqSet) > m:
        Hmp1 = calcConf(freqSet, H, supportData, brl, minConf)  # m后件
        Hmp1 = aprioriGen(Hmp1, m + 1)  # 可用后件合并
        if len(Hmp1) > 0:
            rulesFromConseq(freqSet, Hmp1, supportData, brl, minConf)


dataset = loadDataSet()
L, supportData = apriori(dataset, minSupport=0.2)
result = generateRules(L, supportData)
print(result)
