# -*- coding: utf-8 -*-

from flask import Flask, request, render_template, redirect, url_for
from flask.templating import Environment
import json
import csv
from datetime import timedelta
from Create_KG.Connect_Server import graph
from pyecharts.conf import PyEchartsConfig
from pyecharts.engine import ECHAERTS_TEMPLATE_FUNCTIONS
from pyecharts import Bar, Funnel, WordCloud, Radar, Pie, Line, Timeline


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
    Province_BJ, opp_BJ, org_BJ, BJ_to_Other, Other_to_BJ, timeline = ReadBJMap()
    error = None
    if request.method == 'POST':
        if request.form['username'] != '':
            return redirect(url_for('Person_Page', login_name=request.form['username']))
        else:
            error = 'Invalid username/password'
    return render_template('login.html', error=error, Province_BJ=json.dumps(Province_BJ),
                           opp_BJ=json.dumps(opp_BJ), org_BJ=json.dumps(org_BJ), BJ_to_Other=json.dumps(BJ_to_Other),
                           Other_to_BJ=json.dumps(Other_to_BJ), timeline=timeline)


@app.route('/Person_Page/<login_name>', methods=['POST', 'GET'])
def Person_Page(login_name):
    nodes, edges = get_graph(login_name)
    return render_template('Person_Page.html', nodes=json.dumps(nodes), edges=json.dumps(edges))


def get_graph(login_name):
    nodes = list(map(buildNodes, graph.data("Match(n:Org_Group{Name:'%s'})-[r]-(p) return n" %(login_name))))
    edges = list(map(buildEdges, graph.data("Match(n:Org_Group{Name:'%s'})-[r]-(p) return r" %(login_name))))
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
    return Province_BJ, opp_BJ, org_BJ, BJ_to_Other, Other_to_BJ, timeline


def buildNodes(nodeRecord):
    # print(str(nodeRecord['n'].labels()) == "SetView({'Org_Group'})")    # 用来之后固定查询语句
    label = str(nodeRecord['n'].labels())   # 取出标签，若存在“‘***’”这样的嵌套则传数据会崩
    data = {"label": label[10:-3]}
    data.update(nodeRecord['n'].properties)
    # data = {"label": str(nodeRecord['p'].labels())}
    # data.update(nodeRecord['p'].properties)
    return {'data': data}


def buildEdges(relationRecord):
    source = relationRecord['r'].start_node()['Name']
    target = relationRecord['r'].end_node()
    print(source)
    print(target)
    data = {"source": str(relationRecord['r'].start_node()),
            "target": str(relationRecord['r'].end_node()),
            "relationship": relationRecord['r'].relationships()}
    return {'data': data}


if __name__ == '__main__':
    app.run(debug=True)


