# -*- coding: utf-8 -*-

from flask import Flask, request, render_template, redirect, url_for, jsonify
from flask.templating import Environment
import json
import csv
import re
from datetime import timedelta
from Create_KG.Connect_Server import graph
from Create_KG.Hanlp_Classfy import Classfy_Question
from Create_KG.AIML import KGQA_Answer
from pyecharts.conf import PyEchartsConfig
from pyecharts.engine import ECHAERTS_TEMPLATE_FUNCTIONS
from pyecharts import Bar, Funnel, WordCloud, Radar, Pie, Line, Timeline, Scatter


# ----- Adapter ---------
class FlaskEchartsEnvironment(Environment):
    def __init__(self, *args, **kwargs):
        super(FlaskEchartsEnvironment, self).__init__(*args, **kwargs)
        self.pyecharts_config = PyEchartsConfig(jshost='/static/js')
        self.globals.update(ECHAERTS_TEMPLATE_FUNCTIONS)


# ---User Code ----
class MyFlask(Flask):
    jinja_environment = FlaskEchartsEnvironment


app = MyFlask(__name__)
# 之下两行清除浏览器缓存使JS\CSS生效
app.config['DEBUG'] = True
app.send_file_max_age_default = timedelta(seconds=1)


@app.route('/')
def Main_Show():
    Province_China, opp_China , org_China, Province_ALL_China = ReadMap()
    Age = ReadAge()
    funnel, wordcloud, radar, pie, line = ReadOther()
    return render_template("Show.html", Province_China=json.dumps(Province_China), opp_China=json.dumps(opp_China),
                           org_China=json.dumps(org_China), Province_ALL_China=json.dumps(Province_ALL_China),
                           Age=Age, funnel=funnel, wordcloud=wordcloud, radar=radar, pie=pie, line=line)


@app.route('/Login', methods=['POST', 'GET'])
def Login():
    Province_BJ, opp_BJ, org_BJ, BJ_to_Other, Other_to_BJ, timeline, timeline_uni = ReadBJMap()
    error = None
    if request.method == 'POST':
        if request.form['username'] != '':
            return redirect(url_for('Person_Page', login_name=request.form['username']))
        else:
            error = 'Invalid username/password'
    return render_template('login.html', error=error, Province_BJ=json.dumps(Province_BJ),
                           opp_BJ=json.dumps(opp_BJ), org_BJ=json.dumps(org_BJ), BJ_to_Other=json.dumps(BJ_to_Other),
                           Other_to_BJ=json.dumps(Other_to_BJ), timeline=timeline, timeline_uni=timeline_uni)


@app.route('/Person_Page/<login_name>', methods=['POST', 'GET'])
def Person_Page(login_name):
    nodes, edges = get_graph(login_name)
    return render_template('Person_Page.html', nodes=json.dumps(nodes), edges=json.dumps(edges), login_name=login_name)


@app.route('/All_Show_Page/<login_name>', methods=['POST', 'GET'])
def All_Show_Page(login_name):
    nodes, edges = get_all_graph(login_name)
    return render_template('All_Show_Page.html', nodes=json.dumps(nodes), edges=json.dumps(edges), login_name=login_name)


@app.route('/QA_Relation/<login_name>', methods=['POST', 'GET'])
def QA_Relation(login_name):
    if request.method == 'POST':
        if request.form['question'] != '':
            return redirect(url_for('QA_Relation_Search', question=request.form['question'], login_name=login_name))
    return render_template('QA_Relation_Page.html', login_name=login_name)


@app.route('/QA_Relation_Search/<question>, <login_name>', methods=['POST', 'GET'])
def QA_Relation_Search(question, login_name):
    class_result, search_name = Classfy_Question(question)
    nodes = []
    edges = []
    if class_result == 0:
        nodes, edges = get_ques_graph_0(login_name, search_name)
    elif class_result == 1:
        nodes, edges = get_ques_graph_1(search_name)
    elif class_result == 2:
        nodes, edges = get_ques_graph_2(search_name)
    return render_template('QA_Relation_Page.html', login_name=login_name,
                           nodes=json.dumps(nodes), edges=json.dumps(edges))


@app.route('/KGQA_Page/<login_name>', methods=['POST', 'GET'])
def KGQA_Page(login_name):
    quiz = request.form.get('quiz')
    if quiz == None:
        return render_template('KGQA_Page.html', login_name=login_name, login_name_=json.dumps(login_name))
    result = KGQA_Answer(quiz)
    if result:
        answer = result
    else:
        answer = quiz + '???'
    return jsonify({'answer': answer})


def get_graph(login_name):
    graph_data = graph.data("Match(n:Volunteer{name:'%s'})-[r]-(p) return n,r,p" % (login_name))
    nodesn_ = list(map(buildNodesn, graph_data))
    nodesn = []
    for node in nodesn_:
        if node not in nodesn:
            nodesn.append(node)
    nodesp = list(map(buildNodesp, graph_data))
    for node_list in nodesp:
        for node in node_list:
            if node not in nodesn:
                nodesn.append(node)  # 查询出的结果去重
    edges = []
    edger = list(map(buildEdgesn, graph_data))
    for edge_list in edger:
        for edge in edge_list:
            if edge not in edges:
                edges.append(edge)
    # nodesn_ = list(map(buildNodesn, graph.data("Match(n:Volunteer{name:'%s'})-[r]-(p) return n" % (login_name))))
    # nodesn = []
    # for node in nodesn_:
    #     if node not in nodesn:
    #         nodesn.append(node)
    # nodesp = list(map(buildNodesp, graph.data("Match(n:Volunteer{name:'%s'})-[r]-(p) return p" % (login_name))))
    # nodes = nodesn + nodesp
    # edges = list(map(buildEdgesn, graph.data("Match(n:Volunteer{name:'%s'})-[r]-(p) return r" %(login_name))))
    return nodesn, edges


def get_all_graph(login_name):
    graph_data = graph.data("match (n1:Volunteer{name:'%s'})-[r1]-(p1)-[r2]-(n2:Volunteer)"
                            "-[r3]-(p2:Group)-[l1]-(p3:City)-[l2]-(p4:Province) "
                            "return n1,n2,p1,p2,p3,p4,l1,l2,r1,r2,r3" % (login_name))
    nodesn_ = list(map(buildNodesn, graph_data))
    nodesn = []
    for node in nodesn_:
        if node not in nodesn:
            nodesn.append(node)  # 查询出的结果去重
    nodesp = list(map(buildNodesp, graph_data))
    for node_list in nodesp:
        for node in node_list:
            if node not in nodesn:
                nodesn.append(node)  # 查询出的结果去重
    edger = list(map(buildEdgesn, graph_data))
    edgesr = []
    for edge_list in edger:
        for edge in edge_list:
            if edge not in edgesr:
                edgesr.append(edge)
    edger = list(map(buildEdges, graph_data))
    for edge_list in edger:
        for edge in edge_list:
            if edge not in edgesr:
                edgesr.append(edge)
    # nodesn_ = list(map(buildNodesn, graph.data("match (n:Volunteer{name:'%s'})-[*1..2]-(:Volunteer)"
    #                                            "-[]-(:Group)-[]-(:City)-[]-(:Province) return n" %(login_name))))
    # nodesn = []
    # for node in nodesn_:
    #     if node not in nodesn:
    #         nodesn.append(node)     # 查询出的结果去重
    # nodesn_ = list(map(buildNodesn, graph.data("match (:Volunteer{name:'%s'})-[*1..2]-(n:Volunteer)"
    #                                            "-[]-(:Group)-[]-(:City)-[]-(:Province) return n" %(login_name))))
    # for node in nodesn_:
    #     if node not in nodesn:
    #         nodesn.append(node)     # 查询出的结果去重
    # nodesn_ = list(map(buildNodesp, graph.data("match (:Volunteer{name:'%s'})-[*1..2]-(:Volunteer)"
    #                                            "-[]-(p:Group)-[]-(:City)-[]-(:Province) return p" % (login_name))))
    # for node in nodesn_:
    #     if node not in nodesn:
    #         nodesn.append(node)  # 查询出的结果去重
    # nodesn_ = list(map(buildNodesp, graph.data("match (:Volunteer{name:'%s'})-[]-(p) return p" % (login_name))))
    # for node in nodesn_:
    #     if node not in nodesn:
    #         nodesn.append(node)  # 查询出的结果去重
    # nodesn_ = list(map(buildNodesp, graph.data("match (:Volunteer{name:'%s'})-[*1..2]-(:Volunteer)"
    #                                            "-[]-(:Group)-[]-(p:City)-[]-(:Province) return p" % (login_name))))
    # for node in nodesn_:
    #     if node not in nodesn:
    #         nodesn.append(node)  # 查询出的结果去重
    # nodesn_ = list(map(buildNodesp, graph.data("match (:Volunteer{name:'%s'})-[*1..2]-(:Volunteer)"
    #                                            "-[]-(:Group)-[]-(:City)-[]-(p:Province) return p" % (login_name))))
    # for node in nodesn_:
    #     if node not in nodesn:
    #         nodesn.append(node)  # 查询出的结果去重
    # edger = list(map(buildEdgesn, graph.data("match (n:Volunteer{name:'%s'})-[r]-() return r" %(login_name))))
    # edgesr = []
    # for edge in edger:
    #     if edge not in edgesr:
    #         edgesr.append(edge)
    # edger = list(map(buildEdgesn, graph.data("match (:Volunteer{name:'%s'})-[]-()-[r]-(:Volunteer)"
    #                                          "-[]-(:Group)-[]-(:City)-[]-(:Province) return r" % (login_name))))
    # for edge in edger:
    #     if edge not in edgesr:
    #         edgesr.append(edge)
    # edger = list(map(buildEdgesn, graph.data("match (:Volunteer{name:'%s'})-[*1..2]-(:Volunteer)"
    #                                          "-[r]-(:Group)-[]-(:City)-[]-(:Province) return r" % (login_name))))
    # for edge in edger:
    #     if edge not in edgesr:
    #         edgesr.append(edge)
    # edger = list(map(buildEdges, graph.data("match (:Volunteer{name:'%s'})-[*1..2]-(:Volunteer)"
    #                                         "-[]-(:Group)-[r]-(:City)-[]-(:Province) return r" % (login_name))))
    # for edge in edger:
    #     if edge not in edgesr:
    #         edgesr.append(edge)
    # edger = list(map(buildEdges, graph.data("match (:Volunteer{name:'%s'})-[*1..2]-(:Volunteer)"
    #                                         "-[]-(:Group)-[]-(:City)-[r]-(:Province) return r" % (login_name))))
    # for edge in edger:
    #     if edge not in edgesr:
    #         edgesr.append(edge)
    # print(edgesr)
    return nodesn, edgesr


def get_ques_graph_0(login_name, search_name):
    graph_data = graph.data("match r=shortestPath((n:Volunteer{name:'%s'})-[*]-"
                            "(p:Volunteer{name:'%s'})) return r" % (login_name, search_name))
    nodes = []
    edges = []
    for path in graph_data:
        nodes = list(map(buildNodes, path['r'].nodes()))
        edges = list(map(BuildEdges, path['r'].relationships()))
    return nodes, edges


def get_ques_graph_1(search_name):
    graph_data = graph.data("Match r=(:Volunteer{name:'%s'})-[]-(:Group) return r" % (search_name))
    nodes = []
    edges = []
    for path in graph_data:
        for node in list(map(buildNodes, path['r'].nodes())):
            if node not in nodes:
                nodes.append(node)
        for edge in list(map(BuildEdges, path['r'].relationships())):
            if edge not in edges:
                edges.append(edge)
    return nodes, edges


def get_ques_graph_2(search_name):
    graph_data = graph.data("Match r=(:Volunteer{name:'%s'})-[]-(:Project) return r" % (search_name))
    nodes = []
    edges = []
    for path in graph_data:
        for node in list(map(buildNodes, path['r'].nodes())):
            if node not in nodes:
                nodes.append(node)
        for edge in list(map(BuildEdges, path['r'].relationships())):
            if edge not in edges:
                edges.append(edge)
    return nodes, edges


def ReadOther():
    attr = ["城市社区服务", "环保项目", "帮扶活动", "文体活动", "安全医疗", "法律宣传讲座培训", "其他"]
    value = [373257, 159648, 212721, 246070, 143465, 120205, 93256]
    funnel = Funnel("项目类别统计", width='100%', height='100%', title_pos='center',
                    title_text_size=16, title_color='#3B5077')
    funnel.add("类别统计", attr, value, is_label_show=True, label_pos="inside", label_text_color="#fff",
               label_text_size=8, legend_orient="vertical", legend_pos="left", legend_text_size=10)

    name = []
    value = []
    with open('data/全国院校统计前100.csv', 'r', encoding='utf-8') as file:
        reader = csv.reader(file)
        for row in reader:
            name.append(row[2])
            value.append(row[1])
    wordcloud = WordCloud(width='120%', height='100%')
    wordcloud.add("", name, value, word_size_range=[8, 30])

    schema = [
        ("博士研究生", 1000000), ("硕士研究生", 1000000), ("大学本科", 1000000), ("大学专科", 1000000), ("中等专科", 1000000),
        ("技工学校", 1000000), ("高中", 1000000), ("初中", 1000000), ("职业高中", 1000000), ("小学", 1000000),
    ]
    v1 = [[9979, 48300, 716519, 448358, 118656, 36065, 600168, 697599, 54160, 270191]]
    v2 = [[863336, 462984, 953627, 646927, 234893, 170111, 354992, 241914, 158316, 84504]]
    radar = Radar(width='100%', height='110%')
    radar.config(schema)
    radar.add("实际人数分布", v1, is_splitline=True, is_axisline_show=True, label_text_size=8, legend_orient="vertical")
    radar.add("人数比例分布", v2, label_color=["#4e79a7"], is_area_show=False,
              legend_selectedmode='single', legend_pos="right", legend_text_size=10, legend_orient="vertical")

    attr = ["群众", "中国少年先锋队队员", "无党派民主人士", "台湾民主自治同盟盟员", "九三学社社员", "中国致公党党员", "中国农工民主党党员",
            "中国民主促进会会员", "中国民主建国会会员", "中国民主同盟盟员", "中国国民党革命委员会会员", "中国共产主义青年团团员", "中国共产党预备党员", "中国共产党党员"]
    v2 = [34688546, 2725751, 95275, 2180, 713840, 3787, 30049, 7356, 7278, 14952, 21065, 12621879, 294148, 6089445]
    pie = Pie(width='100%', height='90%', title_pos='center', title_text_size=10)
    pie.add("政治面貌统计", attr, v2, center=[50, 50], is_random=True, radius=[10, 80], rosetype="area",
            is_legend_show=True, is_label_show=False, legend_pos="left", legend_text_size=10, legend_orient="vertical")

    attr = ['2005', '2006', '2007', '2008', '2009', '2010', '2011',
            '2012', '2013', '2014', '2015', '2016', '2017', '2018']
    line = Line(width='100%', height='100%')
    line.add("志愿者数增长", attr, [1, 59580, 532707, 258196, 26194, 628465, 311171, 1970707, 1539836,
                              2807952, 6566130, 6775399, 36504414, 7408478], mark_line=["average"])
    line.add("团体增长", attr, [371, 485, 471, 924, 798, 1266, 2887, 4963, 4848, 7781, 24203, 15936, 25280, 5376],
             mark_line=["average"])
    line.add("项目增长", attr, [10, 6, 3, 94, 125, 152, 210, 802, 3209, 10937, 58426, 166609, 341083, 203931],
             mark_line=["average"], legend_text_size=10, yaxis_label_textsize=8, yaxis_margin=2)
    return funnel, wordcloud, radar, pie, line


def ReadAge():
    attr = ["{}岁".format(i) for i in range(49)]
    ManAge = []
    WomanAge = []
    with open('data/女性年龄分布.csv', 'r', encoding='utf-8') as file:
        reader = csv.reader(file)
        for row in reader:
            WomanAge.append(row[1])
    with open('data/男性年龄分布.csv', 'r', encoding='utf-8') as file:
        reader = csv.reader(file)
        for row in reader:
            ManAge.append(row[1])
    bar = Bar("志愿者年龄分布", width='100%', height=230, title_text_size=14, title_color='#3B5077')
    bar.add("男", attr, ManAge, is_stack=True)
    bar.add("女", attr, WomanAge, is_stack=True,
            is_datazoom_show=True, datazoom_type="both", datazoom_range=[26, 60],
            yaxis_label_textsize=8, yaxis_margin=2)
    return bar


def ReadMap():
    Province_China = []
    Province_ALL_China = []
    opp_China = []
    org_China = []
    with open('data/全国志愿者分布.csv', 'r', encoding='utf-8') as file:
        reader = csv.reader(file)
        for row in reader:
            Province_China.append(dict(name=row[1], value=int(row[2])))
    with open('data/2018各省人口统计.txt', 'r', encoding='utf-8-sig') as file:    # utf-8-sig可以消除非法字符
        reader = file.readlines()
        for row in reader:
            row = row.split(',')
            Province_ALL_China.append(dict(name=row[0], value=float(row[1][:-2])*10000))
    with open('data/全国志愿项目分布.csv', 'r', encoding='utf-8') as file:
        reader = csv.reader(file)
        for row in reader:
            opp_China.append(dict(name=row[1], value=int(row[2])))
    with open('data/全国志愿团体分布.csv', 'r', encoding='utf-8') as file:
        reader = csv.reader(file)
        for row in reader:
            org_China.append(dict(name=row[1], value=int(row[2])))
    return Province_China, opp_China, org_China, Province_ALL_China


def ReadBJMap():
    Province_BJ = []
    opp_BJ = []
    org_BJ = []
    BJ_to_Other = []
    Other_to_BJ = []
    with open('data/北京志愿者分布.csv', 'r', encoding='utf-8') as file:
        reader = csv.reader(file)
        for row in reader:
            Province_BJ.append(dict(name=row[2], value=int(row[1])))
    with open('data/北京志愿项目分布.csv', 'r', encoding='utf-8') as file:
        reader = csv.reader(file)
        for row in reader:
            opp_BJ.append(dict(name=row[2], value=int(row[1])))
    with open('data/北京志愿团体分布.csv', 'r', encoding='utf-8') as file:
        reader = csv.reader(file)
        for row in reader:
            org_BJ.append(dict(name=row[2], value=int(row[1])))
    with open('data/BJ_向外人口.csv', 'r', encoding='utf-8') as file:
        reader = csv.reader(file)
        for row in reader:
            BJ_to_Other.append(dict(name=row[1], value=int(row[2])))
    with open('data/BJ_外来人口.csv', 'r', encoding='utf-8') as file:
        reader = csv.reader(file)
        for row in reader:
            Other_to_BJ.append(dict(name=row[1], value=int(row[2])))

    attr_vol = []
    attr_org = []
    attr_uni = []
    hour_vol = []
    hour_org = []
    hour_uni = []
    opp_vol = []
    opp_org = []
    opp_uni = []
    with open('data/BJ_时长最长的志愿者.csv', 'r', encoding='utf-8') as file:
        reader = csv.reader(file)
        for row in reader:
            attr_vol.append(row[1])
            hour_vol.append(row[2])
            opp_vol.append(row[3])
    bar_vol = Bar("时长最长的30位志愿者", width='100%', height='100%', title_text_size=14, title_color='#3B5077')
    bar_vol.add("时长", attr_vol, hour_vol, is_stack=True, is_label_show=True, label_formatter='{b}',
                label_pos='right', label_text_size=10, label_text_color='#f95d3c')
    bar_vol.add("项目数", attr_vol, opp_vol, is_stack=True, is_label_show=True, label_formatter='{b}', label_pos='right',
                label_text_size=10, is_yaxis_show=False, legend_pos='right', label_text_color='#f95d3c',
                is_datazoom_show=True, datazoom_type="both", datazoom_range=[0, 30], datazoom_orient='vertical',
                yaxis_label_textsize=8, yaxis_margin=2, xaxis_label_textsize=8, is_convert=True)
    with open('data/BJ_时长最长的志愿团体.csv', 'r', encoding='utf-8') as file:
        reader = csv.reader(file)
        for row in reader:
            attr_org.append(row[1])
            hour_org.append(row[2])
            opp_org.append(row[3])
    bar_org = Bar("时长最长的30个志愿团体", width='100%', height='100%', title_text_size=14, title_color='#3B5077')
    bar_org.add("时长", attr_org, hour_org, is_stack=True, is_label_show=True, label_formatter='{b}',
                label_pos='right', label_text_size=10)
    bar_org.add("项目数", attr_org, opp_org, is_stack=True, is_label_show=True, label_formatter='{b}',
                label_pos='right', label_text_size=10, is_yaxis_show=False, legend_pos='right',
                is_datazoom_show=True, datazoom_type="both", datazoom_range=[0, 20], datazoom_orient='vertical',
                yaxis_label_textsize=8, yaxis_margin=2, is_convert=True)
    with open('data/BJ_时长最长的高校.csv', 'r', encoding='utf-8') as file:
        reader = csv.reader(file)
        for row in reader:
            attr_uni.append(row[1])
            hour_uni.append(row[2])
            opp_uni.append(row[3])
    bar_uni = Bar("时长最长的30所高校", width='100%', height='100%', title_text_size=14, title_color='#3B5077')
    bar_uni.add("时长", attr_uni, hour_uni, is_stack=True, is_label_show=True, label_formatter='{b}',
                label_pos='right', label_text_size=10)
    bar_uni.add("项目数", attr_uni, opp_uni, is_stack=True, is_label_show=True, label_formatter='{b}',
                label_pos='right', label_text_size=10, is_yaxis_show=False, legend_pos='right',
                is_datazoom_show=True, datazoom_type="both", datazoom_range=[0, 20], datazoom_orient='vertical',
                yaxis_label_textsize=6, yaxis_margin=2, xaxis_label_textsize=8, is_convert=True)
    timeline = Timeline(is_auto_play=True, timeline_bottom=0, width='100%', height='100%')
    timeline.add(bar_vol, '志愿者')
    timeline.add(bar_org, '志愿团体')
    timeline.add(bar_uni, '高校志愿')

    timeline_uni = Timeline(is_auto_play=True, timeline_bottom=0, width='100%', height='100%')
    for i in range(2011, 2019):
        vol_num = []
        opp_hour = []
        opp_num = []
        university = []
        hour_min = 7000000
        hour_max = 0
        with open('data/BJ_高校每年项目及时长统计.csv', 'r', encoding='utf-8') as file:
            reader = csv.reader(file)
            for row in reader:
                if int(row[0]) == i:
                    opp_num.append(int(row[4]))
                    opp_hour.append(int(row[3]))
                    university.append(row[2])
                    if int(row[3]) < hour_min:
                        hour_min = int(row[3])
                    if int(row[3]) > hour_max:
                        hour_max = int(row[3])
        with open('data/BJ_高校每年新增志愿者数.csv', 'r', encoding='utf-8') as file:
            reader = csv.reader(file)
            for row in reader:  # 必须这个在前，一个open只能这么循环一次
                for uni in university:
                    if int(row[0]) == i and row[2] == uni:
                        vol_num.append(int(row[3]))
        scatter = Scatter("%s年高校统计" % i)
        for uni in university:
            lab = university.index(uni)
            scatter.add(uni, [opp_num[lab]], [vol_num[lab]], extra_data=[opp_hour[lab]],
                        symbol_size=opp_hour[lab]/hour_max*70, is_legend_show=False, tooltip_formatter="{a}:{c}")
        timeline_uni.add(scatter, '%s' % i)
    return Province_BJ, opp_BJ, org_BJ, BJ_to_Other, Other_to_BJ, timeline, timeline_uni


def buildNodes(nodeRecord):
    pattern = re.compile('.*?Id', re.S)  # 正则匹配关系
    id = ''
    for k in nodeRecord.keys():
        if len(re.findall(pattern, k)) > 0:
            id = k
    label = str(nodeRecord.labels())   # 取出标签，若存在“‘***’”这样的嵌套则传数据会崩
    name = str(nodeRecord['name']) + '_' + str(nodeRecord[id])
    data = {"category": label[10:-3], "symbolSize": 30, "name": name}   # Echarts
    return data


def buildNodesn(nodeRecord):    # nodeRecord 是一个字典
    # print(str(nodeRecord['n'].labels()) == "SetView({'Org_Group'})")    # 用来之后固定查询语句
    pattern = re.compile('n.*?', re.S)  # 正则匹配关系
    data = {}
    for k in nodeRecord.keys():
        l = re.findall(pattern, k)
        if len(l) > 0:
            label = str(nodeRecord[k].labels())   # 取出标签，若存在“‘***’”这样的嵌套则传数据会崩
            name = str(nodeRecord[k]['name']) + '_' + str(nodeRecord[k]['volunteerId'])
            data = {"category": label[10:-3], "symbolSize": 30, "name": name}   # Echarts
    # data = {"label": label[10:-3]}    # Cytoscape
    # data = {"category": label[10:-3], "symbolSize": 20}  # Echarts
    # data.update(nodeRecord['n'].properties)
    # return {'data': data} #Cytoscape
    return data


def buildNodesp(nodeRecord):
    pattern = re.compile('p.*?', re.S)  # 正则匹配关系
    data = []
    node = {}
    for k in nodeRecord.keys():
        l = re.findall(pattern, k)
        if len(l) > 0:
            label = str(nodeRecord[k].labels())   # 取出标签，若存在“‘***’”这样的嵌套则传数据会崩
            node = {"category": label[10:-3], "symbolSize": 20}   # Echarts
            node.update(nodeRecord[k].properties)
            data.append(node)
    return data


def BuildEdges(relationRecord):
    relationships = str(relationRecord)
    pattern = re.compile('.*?-\[:(.*?) \{.*?', re.S)    # 正则匹配关系
    relationship = re.findall(pattern, relationships)
    patterns = re.compile('.*?Id', re.S)  # 正则匹配关系
    sid = ''
    eid = ''
    for k in relationRecord.start_node().keys():
        if len(re.findall(patterns, k)) > 0:
            sid = k
    source = relationRecord.start_node()['name'] + '_' + relationRecord.start_node()[sid]
    for k in relationRecord.end_node().keys():
        if len(re.findall(patterns, k)) > 0:
            eid = k
    target = relationRecord.end_node()['name'] + '_' + relationRecord.end_node()[eid]
    edge = {"source": source,
            "target": target,
            "value": relationship[0]}
    return edge


def buildEdgesn(relationRecord):
    patternr = re.compile('r.*?', re.S)  # 正则匹配关系
    edge = {}
    data = []
    for k in relationRecord.keys():
        l = re.findall(patternr, k)
        if len(l) > 0:
            relationships = str(relationRecord[k])
            pattern = re.compile('.*?-\[:(.*?) \{.*?', re.S)    # 正则匹配关系
            relationship = re.findall(pattern, relationships)
            source = relationRecord[k].start_node()['name'] + '_' + relationRecord[k].start_node()['volunteerId']
            target = relationRecord[k].end_node()['name']
            edge = {"source": source,
                    "target": target,
                    "value": relationship[0]}
            data.append(edge)
    # return {'data': data} #Cytoscape
    return data


def buildEdges(relationRecord):
    patternr = re.compile('l.*?', re.S)  # 正则匹配关系
    data = []
    edge = {}
    for k in relationRecord.keys():
        l = re.findall(patternr, k)
        if len(l) > 0:
            relationships = str(relationRecord[k])
            pattern = re.compile('.*?-\[:(.*?) \{.*?', re.S)    # 正则匹配关系
            relationship = re.findall(pattern, relationships)
            source = relationRecord[k].start_node()['name']
            target = relationRecord[k].end_node()['name']
            edge = {"source": source,
                    "target": target,
                    "value": relationship[0]}
            data.append(edge)
    # return {'data': data} #Cytoscape
    return data


if __name__ == '__main__':
    app.run(debug=True)

