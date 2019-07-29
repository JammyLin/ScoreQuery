#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os
import sqlite3


def insertData(name, password):
    """如若数据库不存在则创建和插入数据，否则只更新数据"""
    conn = sqlite3.connect('info.db')
    cursor = conn.cursor()
    insertSql = "insert into session (name, password) values (?, ?)"
    try:
        createSql = 'create table session' \
                        '(name text primary key,' \
                        'password text)'
        cursor.execute(createSql)
        cursor.execute(insertSql, (str(name), str(password)))
    except sqlite3.OperationalError:
        updateData(name, password)
    cursor.close()
    conn.commit()
    conn.close()


def updateData(name, password):
    """
                更新用户数据
    对比旧数据，如若改动则更新改动数据，如若无则跳过
    """
    conn = sqlite3.connect('info.db')
    cursor = conn.cursor()
    status = 0
    oldInfo = cursor.execute('select name, password from session')
    for info in oldInfo:
        if name != info[0]:
            status += 1
        if password != info[1]:
            status += 2
    cursor = conn.cursor()
    if status == 0:
        pass
    elif status == 1:
        updateSql = 'update session set name = ?'
        cursor.execute(updateSql, (str(name),))
    elif status == 2:
        updateSql = 'update session set password = ?'
        cursor.execute(updateSql, (str(password),))
    else:
        updateSql = 'update session set name = ?,password = ?'
        cursor.execute(updateSql, (str(name), str(password)))
    cursor.close()
    conn.commit()
    conn.close()


def selectInfo():
    """查找并返回用户数据"""
    conn = sqlite3.connect('info.db')
    cursor = conn.cursor()
    userinfo = []
    cursor.execute('select name, password from session')
    for data in cursor:
        userinfo = [data[0], data[1]]
    cursor.close()
    conn.commit()
    conn.close()
    return userinfo


def deleteDB():
    """删除数据库"""
    try:
        os.remove("info.db")
    except FileNotFoundError:
        pass
