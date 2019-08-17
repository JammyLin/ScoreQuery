#!/usr/bin/python3
# -*- coding: utf-8 -*-

import datetime
import pandas as pd
import requests
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QMainWindow, QGridLayout, QWidget, QComboBox, QCheckBox, QPushButton,\
    QLabel, QTextEdit, QMessageBox, QDesktopWidget
from bs4 import BeautifulSoup
import LoginForm
import Images


url = "http://202.199.128.21:80"
headers = {
    'Host': '202.199.128.21',
    'Connection': 'keep-alive',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.142 Safari/537.36',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'zh-CN,zh;q=0.9',
}

"""字典集"""
dicts = {
    '全部': '', '春': '1', '秋': '2', '必修': '0', '选修': '1', '任选': '2',  # 下拉框中选项转换
    '优': 95, '良': 85, '中': 75, '不及格': 35, '及格': 65, '合格': 85,  # 等级成绩转换为分数
    '第一学年': 0, '第二学年': 1, '第三学年': 2, '第四学年': 3, '第五学年': 4  # 学年转换
}


class QueryWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        # 主控件
        self.mainWidget = QWidget()
        self.mainLayout = QGridLayout()
        self.mainWidget.setLayout(self.mainLayout)

        # 查询模块
        self.queryWidget = QWidget()
        self.queryLayout = QGridLayout()
        self.queryWidget.setLayout(self.queryLayout)

        self.yearCombo = QComboBox()  # 年份选择
        self.yearCombo.addItem("全部")
        for i in range(2012, 2027):
            self.yearCombo.addItem(str(i))
        """获取当前年份后并设置为默认值"""
        todayYear = datetime.datetime.today().year
        yearIndex = self.yearCombo.findText(str(todayYear))
        self.yearCombo.setCurrentIndex(yearIndex)

        self.termCombo = QComboBox()  # 学期选择
        self.termCombo.addItem('全部')
        self.termCombo.addItem('春')
        self.termCombo.addItem('秋')
        self.termCombo.setCurrentIndex(1 if datetime.datetime.today().month < 9 else 2)  # 小于9月默认选择春，否则为秋

        """条件选择框"""
        self.checkFailed = QCheckBox('未通过课程')
        self.checkPassed = QCheckBox('及格课程')
        self.checkMax = QCheckBox("最高分")

        # 课程属性选择
        self.propCombo = QComboBox()
        self.propCombo.addItem('全部')
        self.propCombo.addItem('必修')
        self.propCombo.addItem('选修')
        self.propCombo.addItem('任选')

        self.queryBtn = QPushButton('查询')

        self.info = QLabel('未登录')  # 记录登录状况

        self.dispArea = QTextEdit()  # 显示区域
        self.dispArea.setReadOnly(True)

        self.selectGrade = QComboBox()  # 要计算的学年选择
        self.selectGrade.addItem('全部')
        self.selectGrade.addItem('第一学年')
        self.selectGrade.addItem('第二学年')
        self.selectGrade.addItem('第三学年')
        self.selectGrade.addItem('第四学年')
        self.selectGrade.addItem('第五学年')

        self.selectPattern = QComboBox()  # 选择计算模式
        self.selectPattern.addItem('GPA')
        self.selectPattern.addItem('奖学金GPA')

        self.countScore = QPushButton('计算GPA')

        self.createExcel = QPushButton('生成Excel文件')

        self.login = QPushButton('登录')

        self.about = QPushButton('使用须知')

        # 查询模块
        self.queryLayout.addWidget(QLabel("学年学期"), 0, 0, Qt.AlignRight)
        self.queryLayout.addWidget(self.yearCombo, 0, 1)
        self.queryLayout.addWidget(self.termCombo, 0, 2)
        self.queryLayout.addWidget(self.checkFailed, 0, 3)
        self.queryLayout.addWidget(self.checkPassed, 0, 4)
        self.queryLayout.addWidget(self.checkMax, 0, 5)
        self.queryLayout.addWidget(QLabel("选课属性"), 0, 6, Qt.AlignRight)
        self.queryLayout.addWidget(self.propCombo, 0, 7)
        self.queryLayout.addWidget(self.queryBtn, 0, 8)

        # 主控件
        self.mainLayout.addWidget(self.queryWidget, 0, 0, 1, 9)
        self.mainLayout.addWidget(self.info, 0, 9)
        self.mainLayout.addWidget(self.dispArea, 1, 0, 7, 10)
        self.mainLayout.addWidget(self.selectGrade, 8, 0)
        self.mainLayout.addWidget(self.selectPattern, 8, 1)
        self.mainLayout.addWidget(self.countScore, 8, 2)
        self.mainLayout.addWidget(self.createExcel, 8, 4)
        self.mainLayout.addWidget(self.login, 8, 8)
        self.mainLayout.addWidget(self.about, 8, 9)

        """信号连接"""
        self.login.clicked.connect(self.judgeLogin)
        self.about.clicked.connect(self.introduce)
        self.queryBtn.clicked.connect(self.dispScore)
        self.countScore.clicked.connect(lambda: self.calculate(1))
        self.createExcel.clicked.connect(lambda: self.calculate(2))

        self.setCentralWidget(self.mainWidget)  # 设置窗口主部件
        self.setWindowTitle('个人成绩查询')
        self.setWindowIcon(QIcon(':/logo.ico'))
        self.setFixedSize(725, 500)
        self.center()

    def judgeLogin(self):
        if self.info.text() == "未登录":
            # 登录控件
            self.loginWidget = LoginForm.LoginForm()
            self.loginWidget.setWindowModality(Qt.ApplicationModal)
            self.loginWidget.successed.connect(self.refreshInfo)
            self.loginWidget.show()
        if self.login.text() == "退出登录":
            self.info.setText("未登录")
            self.login.setText('登录')

    def refreshInfo(self, cookies):
        """成功登录后接收数据并刷新界面信息"""
        self.cookies = cookies

        try:
            response = requests.get(url + '/academic/showHeader.do', headers=headers, cookies=self.cookies)  # 获取用户姓名
        except ConnectionError:
            self.dispArea.setText("未联网")
            return
        soup = BeautifulSoup(response.text, 'html.parser')
        info = soup.find(id="greeting").find('span').string
        for i, value in enumerate(info):  # 只保留字符串中的姓名
            if value == '(':
                self.entranceGrade = info[i + 1:i + 3]  # 获得入学年份
                info = info[:i]
                break
        self.info.setText("您好！" + str(info))
        self.login.setText('退出登录')
        self.loginWidget.close()

    def introduce(self):
        QMessageBox.about(self, '关于', '本软件需联网登录教务，仅限大连交通大学学生使用。<br><br>'
                                      '<b>生成Excel文件功能说明</b>：依据所选学年生成文档<br>'
                                        'eg.所选为第一学年，则生成文档中只包含第一学年成绩<br><br>'
                                        '<b>Note</b>：<br>'
                                        '1.生成新文档请先关闭先前文档再生成<br>'
                                        '2.全部学年只能计算GPA，无法计算奖学金GPA<br>'
                                        '3.计算查询不要过于频繁')

    def dispScore(self):
        if self.info.text() == "未登录":
            self.dispArea.setText("请先登录")
            return

        # post的form数据
        params = {
            'para': '0'
        }

        # 所选选项
        year = self.yearCombo.currentText()
        term = self.termCombo.currentText()
        prop = self.propCombo.currentText()

        # 添加表单数据
        params['year'] = (str(int(year[0]) + int(year[2])) + year[3]) if year != '全部' else dicts[year]
        params['term'] = dicts[term]
        params['prop'] = dicts[prop]
        if self.checkFailed.isChecked():
            params['failedStatus'] = '1'
        if self.checkPassed.isChecked():
            params['passedStatus'] = '1'
        if self.checkMax.isChecked():
            params['maxStatus'] = '1'

        try:
            response = requests.post(url + '/academic/manager/score/studentOwnScore.do', headers=headers,
                                     params=params, cookies=self.cookies)
        except ConnectionError:
            self.dispArea.setText("电脑未联网")
            return

        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find(class_="datalist")
        if table is None:
            self.dispArea.setText('暂无成绩')
            return
        df = pd.read_html(str(table))[0]
        df = df.drop(df.columns[[2, 3, 6, 11, 12, 13, 14, 15]], axis=1)  # 删除无用列
        df = df.fillna(value='')  # 缺省值处理
        self.dispArea.setHtml(str(df.to_html()))

    def calculate(self, pattern):
        """1为只计算GPA，2为计算并生成Excel"""
        if self.info.text() == "未登录":
            self.dispArea.setText("请先登录")
            return

        params = {
            'para': '0',
            'maxStatus': '1'
        }

        grade = self.selectGrade.currentText()
        calculatePattern = 1 if self.selectPattern.currentText() == 'GPA' else 2

        try:
            if grade == "全部":  # 计算总GPA
                if calculatePattern == 2:
                    self.dispArea.setText("奖学金GPA只能计算某一学年")
                    return
                params['year'] = ''
                params['term'] = ''
                response = requests.post(url + '/academic/manager/score/studentOwnScore.do', headers=headers,
                                             params=params, cookies=self.cookies)
                datas = calculateGPA(response, 1)
                if datas is None:  # 没有成绩直接退出计算
                    self.dispArea.setText('暂无成绩')
                    return
                GPA = datas[0] / datas[1]
                df = appendDF(GPA, datas[2], 1)

            else:  # 计算某学年GPA或奖学金成绩
                """上半学年"""
                year = str(int(self.entranceGrade) + dicts[grade])
                year = str(int(year[0]) + 2) + year[1]
                term = '2'
                params['year'] = year
                params['term'] = term
                response = requests.post(url + '/academic/manager/score/studentOwnScore.do', headers=headers,
                                             params=params, cookies=self.cookies)
                datas = calculateGPA(response, calculatePattern)
                if datas is None:
                    self.dispArea.setText('暂无成绩')
                    return
                theFirstSemesterScore = datas[0]
                theFirstSemesterGredit = datas[1]
                df = datas[2]


                """下半学年"""
                year = str(int(year) + 1)
                term = '1'
                params['year'] = year
                params['term'] = term
                response = requests.post(url + '/academic/manager/score/studentOwnScore.do', headers=headers,
                                         params=params, cookies=self.cookies)
                datas = calculateGPA(response, calculatePattern)
                theSecondSemesterScore = datas[0]
                theSecondSemesterGredit = datas[1]
                df = df.append(datas[2], ignore_index=True)
                if calculatePattern == 1:
                    GPA = (theFirstSemesterScore + theSecondSemesterScore) / \
                          (theFirstSemesterGredit + theSecondSemesterGredit)
                else:
                    GPA = (theFirstSemesterScore / theFirstSemesterGredit) * 0.4 + \
                          (theSecondSemesterScore / theSecondSemesterGredit) * 0.6
                df = appendDF(GPA, df, calculatePattern)
        except ConnectionError:
            self.dispArea.setText("电脑未联网")
            return

        if pattern == 1:  # 计算模式
            self.dispArea.setHtml(str(df.to_html()))
        else:  # 生成模式
            try:
                df.to_excel('Score.xlsx', sheet_name='Sheet1')
                self.dispArea.setHtml("生成文档成功")
            except PermissionError:
                self.dispArea.setHtml("请先关闭文档或修改文档名称再生成新文档")

    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())


def calculateGPA(response, calculatePattern):
    """计算相关GPA并返回相关数据和DataFrame"""
    soup = BeautifulSoup(response.text, 'html.parser')
    table = soup.find(class_="datalist")
    if table is not None:
        df = pd.read_html(str(table))[0]
        if calculatePattern == 2:  # 奖学金GPA只要必修与专业方向选修且不包含优良中差合格成绩
            df = df.query('课组 == ["必修", "专业方向选修"]')
            df = df.query('总评 != ["优", "良", "中", "差", "合格"]')
        df = df.drop(df.columns[[2, 3, 6, 11, 12, 13, 14, 15]], axis=1)
        credit = df.loc[:, '学分']
        results = df.loc[:, '总评']
        totalCredit = 0.0
        totalScore = 0.0
        for i, j in zip(credit, results):
            if j.isdigit():
                totalScore += i * float(j)
                totalCredit += i
            else:
                totalScore += i * dicts[j]
                totalCredit += i
        return totalScore, totalCredit, df


def appendDF(GPA, df, calculatePattern):
    """拼接DataFrame"""
    if calculatePattern == 1:
        DF = pd.DataFrame({'学年': '',
                              '学期': '',
                              '课程名': 'GPA',
                              '选课属性': '',
                              '学分': '',
                              '平时': '',
                              '期末': '',
                              '总评': str(GPA)}, index=[0])
    else:
        DF = pd.DataFrame({'学年': '',
                              '学期': '',
                              '课程名': '奖学金GPA',
                              '选课属性': '',
                              '学分': '',
                              '平时': '',
                              '期末': '',
                              '总评': str(GPA)}, index=[0])
    df = df.append(DF, ignore_index=True)
    df = df.fillna(value='')  # 缺省值处理
    return df
