#!/usr/bin/python
# -*- coding: UTF-8 -*-
"""
@author:lei
@file:my_ssh_demo.py.py
@time:2023/05/03
@邮箱：leigang431@163.com
"""
# Python自带库
import os
import time
import argparse
# 安装第三方库
from loguru import logger
# 自己实现的库
from my_ssh import SSH
from my_ssh import cmd_list
from my_ssh import ssh_host_list

trace = logger.add("run_{time}.log", level="DEBUG")

def demo1():
    ssh = SSH(hostname='xxx', port=22,
              username='root', password='...')
    send_msg,warn_type,sshStatus = ssh.check_ssh_status()
    if(sshStatus == False):
        logger.error("\nsend_msg:{}, warn_type:{}, sshStatus:{}".format(send_msg,warn_type,sshStatus))
        return
    else:
        logger.debug("\nsend_msg:{}, warn_type:{}, sshStatus:{}".format(send_msg, warn_type, sshStatus))
        # 测试命令
        for cmd in cmd_list:
            command = cmd.get("cmd")
            executeStatus, result = ssh.execute(command)
            logger.debug("\ncmd:{},executeStatus:{},result:\n{}".format(command,executeStatus,result))

def demo2():
    for ssh_host in ssh_host_list:
        ssh = SSH(hostname=ssh_host.get("hostname"), port=ssh_host.get("port"),
                  username=ssh_host.get("username"), password=ssh_host.get("password"))
        send_msg, warn_type, sshStatus = ssh.check_ssh_status()
        if (sshStatus == False):
            logger.error("\nsend_msg:{},warn_type:{},sshStatus:{}".format(send_msg, warn_type, sshStatus))
            return
        else:
            logger.debug("\nsend_msg:{},warn_type:{},sshStatus:{}".format(send_msg, warn_type, sshStatus))
            # 测试命令
            for cmd in cmd_list:
                command = cmd.get("cmd")
                executeStatus, result = ssh.execute(command)
                logger.debug("\ncmd:{},executeStatus:{},result:\n{}".format(command,executeStatus,result))

def main():
    demo1()
    # demo2()

if __name__ == '__main__':
    main()
