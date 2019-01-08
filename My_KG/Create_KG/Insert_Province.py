# -*- coding: utf-8 -*-

from Create_KG.Connect_Server import graph
import csv

# graph.delete_all()    # 清空数据库
# 读取csv文件
# with open('./data/province_tmp.csv', encoding='utf-8') as csv_file:
# with open('./data/district_tmp.csv', encoding='utf-8') as csv_file:
with open('./data_tmp/Beijing_org_manager_unit.csv', encoding='utf-8') as csv_file:     # 开始太慢
    readCSV = csv.reader(csv_file, delimiter=',')
    for row in readCSV:
        # if row[2] == '北京市':
        print(row)
        # graph.run("MERGE(p: District{Code:'%s',Name: '%s'})" % (row[1], row[0]))
        graph.run("MERGE(p: Org_Manager_Unit{Name: '%s'})" % (row[0]))
        #     graph.run(
        #         "MATCH(from: District), (to: Province) \
        #         WHERE from.Name='%s' AND to.Name='%s' \
        #         CREATE(from)-[r: Is_Located_In{relation: 'Is_Located_In'}]->(to) \
        #         RETURN r" % (row[0], row[2])
        #     )
        graph.run(
            "MATCH(from: Org_Manager_Unit), (to: District) \
            WHERE from.Name='%s' AND to.Name='%s' \
            CREATE(from)-[r: OrgM_Belong_to{relation: 'OrgM_Belong_to'}]->(to) \
            RETURN r" % (row[0], row[1])
        )

node = graph.find_one(label='Org_Manager_Unit')
print(node)
