#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os
import requests
from bs4 import BeautifulSoup
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPixmap, QImage, QIcon
from PyQt5.QtWidgets import QWidget, QLineEdit, QLabel, QGridLayout, QPushButton, QCheckBox, QDesktopWidget
import DBUtil
import Images

url = "http://202.199.128.21:80"
headers = {
    'Host': '202.199.128.21',
    'Connection': 'keep-alive',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.142 Safari/537.36',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'zh-CN,zh;q=0.9',
}


class LoginForm(QWidget):

    successed = pyqtSignal(requests.cookies.RequestsCookieJar)

    def __init__(self):
        super().__init__()
        self.session = requests.Session()
        self.initUI()

    def initUI(self):
        grid = QGridLayout()  # 布局设置
        grid.setSpacing(10)  # 控件间距

        self.name = QLineEdit()
        self.name.setPlaceholderText("学号")

        self.pwd = QLineEdit()
        self.pwd.setPlaceholderText("密码")
        self.pwd.setEchoMode(QLineEdit.Password)  # 密码输入模式

        self.checkRemember = QCheckBox('记住账号密码')
        """如果数据库存在则上次已勾选记住账号密码"""
        if os.path.exists("info.db"):
            self.checkRemember.setChecked(True)
            info = DBUtil.selectInfo()
            self.name.setText(info[0])
            self.pwd.setText(info[1])

        self.captcha = QLineEdit()
        self.captcha.setAlignment(Qt.AlignCenter)
        self.captcha.setPlaceholderText("验证码")

        """爬取验证码图片并显示"""
        self.captchaView = Captcha()
        self.refresh_captcha()

        confirm = QPushButton("确定")

        self.error = QLabel("")

        """添加控件"""
        grid.addWidget(self.name, 0, 0, 1, 2)
        grid.addWidget(self.checkRemember, 0, 2, 2, 1, Qt.AlignCenter)
        grid.addWidget(self.pwd, 1, 0, 1, 2)
        grid.addWidget(self.captcha, 2, 0)
        grid.addWidget(self.captchaView, 2, 1)
        grid.addWidget(confirm, 2, 2)
        grid.addWidget(self.error, 3, 0, 1, 3)

        """信号连接"""
        self.captchaView.clicked.connect(self.refresh_captcha)
        confirm.clicked.connect(self.login)

        self.setLayout(grid)
        self.resize(300, 130)
        self.center()
        self.setWindowTitle('登录')
        self.setWindowIcon(QIcon(':/logo.ico'))

    """
                    刷新验证码
    先将验证码爬取到本地，然后显示出来后删除本地文件
    """
    def refresh_captcha(self):
        captchaImg = self.session.get(url + "/academic/getCaptcha.do", headers=headers)  # 爬取验证码
        with open("temp.jpg", "wb") as f:  # 先将图片保存本地
            f.write(captchaImg.content)
        im = QImage("temp.jpg")
        self.captchaView.setPixmap(QPixmap.fromImage(im))  # 验证码显示
        os.remove("temp.jpg")  # 删除本地缓存验证码

    """
                    登录验证功能
        提交参数，然后查看是否有错误提示，如若没有则登录成功，进行数据库操作
    """
    def login(self):
        username = self.name.text()
        password = self.pwd.text()
        captcha = self.captcha.text()

        # 传输参数
        params = {
            'j_username': username,
            'j_password': password,
            'j_captcha': captcha
        }

        # 登录信息提交
        response = self.session.post(url + '/academic/j_acegi_security_check', params=params, headers=headers)

        # 提取登录错误信息
        soup = BeautifulSoup(response.text, 'html.parser')
        message = soup.find(id="message")

        if message is not None:
            self.error.setText(str(message))
            self.refresh_captcha()
        else:
            # 是否记住账号密码
            if self.checkRemember.isChecked():
                DBUtil.insertData(username, password)
            else:
                DBUtil.deleteDB()
            self.successed.emit(self.session.cookies)

    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())


class Captcha(QLabel):
    """自定义Label点击事件"""
    clicked = pyqtSignal()

    def mouseReleaseEvent(self, QMouseEvent):
        if QMouseEvent.button() == Qt.LeftButton:
            self.clicked.emit()
