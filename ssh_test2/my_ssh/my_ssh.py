#!/usr/bin/python
# -*- coding: UTF-8 -*-
"""
@author:lei
@file:my_ssh.py
@time:2023/05/03
@邮箱：leigang431@163.com
"""
import datetime
import paramiko

class SSH:
    def __init__(self, hostname: str, port: int = 22, username: str = 'root', password: str = 'huawei'):

        # 建立一个sshclient对象
        self.ssh = paramiko.SSHClient()
        self.ssh_trans = paramiko.SSHClient()

        # 允许将信任的主机自动加入到host_allow 列表，此方法必须放在connect方法的前面
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.timenow = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') + ' '

        self.hostname = hostname
        self.port = port
        self.username = username
        self.password = password

        # ssh状态设置
        self.sshInvalid = False
        self.errorMsg = "null"

        # 调用connect方法连接服务器
        self.connect()

        # trans字典
        self.trans = {
            hostname: {  # 键是该服务器的ip地址
                "hostname": hostname,  # 主机地址
                "port": port,  # 端口号
                "username": username,  # 用户名
                "password": password  # 密码
            }
        }

    def check_ssh_status(self):
        if self.sshInvalid:
            send_msg = ('告警时间：:{},告警主机:{},告警内容:{}').format(self.timenow,str(self.hostname),str(self.errorMsg))
            warn_type = '主机SSH无法连接'
            sshStatus = False
        else:
            send_msg = ('告警时间：:{},告警主机:{},告警内容:{}').format(self.timenow, str(self.hostname), str(self.errorMsg))
            warn_type = '主机SSH连接正常'
            sshStatus = True
        return send_msg, warn_type, sshStatus

    def add_trans(self, hostname: str, port: int, username: str, password: str):
        """
        添加trans服务，用于在多个ssh之间切换
        """
        self.trans[hostname] = {  # 键是该服务器的ip地址
            "hostname": hostname,  # 主机地址
            "port": port,  # 端口号
            "username": username,  # 用户名
            "password": password  # 密码
        }

    def __set_trans(self, hostname: str):
        """
        设置要连接的trans，用以切换不同的ssh
        """
        trans_dict = self.trans.get(hostname)
        if trans_dict is None:
            raise Exception("不存在该主机的trans配置")

        # 使用trans连接
        self.trans_server = paramiko.Transport((trans_dict.get("hostname"), trans_dict.get("port")))
        self.trans_server.connect(username=trans_dict.get("username"), password=trans_dict.get("password"))
        self.ssh_trans._transport = self.trans_server

    def execute_trans(self, hostname: str, command: str):
        """
        使用trans的方式执行ssh命令
        """
        self.__set_trans(hostname)

        # 执行命令，和传统方法一样
        stdin, stdout, stderr = self.ssh_trans.exec_command(command)
        print(stdout.read().decode())

        # 关闭连接
        self.ssh_trans.close()

    def __ftp_execute(self, hostname: str, local_path: str, remote_path: str, execute: str):
        """
        使用FTP执行文件操作

        local_path：本地路径
        remote_path：远程路径
        execute: 执行字符串，upload上传，download下载
        """
        # 获取配置信息
        trans_dict = self.trans.get(hostname)
        if trans_dict is None:
            raise Exception("不存在该主机的trans配置")

        # 实例化一个trans对象
        trans = paramiko.Transport(
            (trans_dict.get("hostname"),
             trans_dict.get("port")))

        # 建立连接
        trans.connect(
            username=trans_dict.get("username"),
            password=trans_dict.get("password"))

        # 实例化一个 sftp对象,指定连接的通道
        sftp = paramiko.SFTPClient.from_transport(trans)

        if execute == "upload":
            # 上传文件
            sftp.put(localpath=local_path, remotepath=remote_path)
        elif execute == "download":
            # 下载文件
            sftp.get(localpath=local_path, remotepath=remote_path)
        else:
            raise Exception("不支持的操作，execute暂时只支持upload和download")

        # 下载文件
        trans.close()

    def ftp_download(self, hostname: str, local_path: str, remote_path: str):
        """
        FTP下载文件

        hostname: 主机地址
        local_path：本地路径
        remote_path：远程路径
        """
        self.__ftp_execute(hostname, local_path, remote_path, "download")

    def ftp_upload(self, hostname: str, local_path: str, remote_path: str):
        """
        FTP上传文件

        hostname: 主机地址
        local_path：本地路径
        remote_path：远程路径
        """
        self.__ftp_execute(hostname, local_path, remote_path, "upload")

    def connect(self):
        """
        建立连接
        """
        try:
            # 调用connect方法连接服务器
            self.ssh.connect(self.hostname, self.port, self.username, self.password, timeout=5)

        except Exception as errmsg:
            self.sshInvalid = True
            self.errorMsg = errmsg

    def execute(self, command: str):
        """
        执行命令
        """
        executeStatus = True
        if self.sshInvalid:
            executeStatus = False
            result = "SSH无法连接，请检查主机"
        else:
            # 执行命令
            # 结果放到stdout中，如果有错误将放到stderr中
            stdin, stdout, stderr = self.ssh.exec_command(command)
            # print("stdin:{}, stdout:{}, stderr:{} ".format(stdin, stdout, stderr))
            # print("dir(stdin_buf):{}".format(dir(stdin_buf)))
            # print("vars(stdin_buf):{}".format(vars(stdin_buf)))
            # print("help(stdin_buf):{}".format(help(stdin_buf)))
            channel = stdout.channel
            status = channel.recv_exit_status()
            result = stdout.read().decode()
            error = stderr.read().decode()
            if status != 0:
                executeStatus = False
                result = ("cmd %s run error, result is %s".format(command, error))
        return executeStatus, result

    def close(self):
        """
        关闭连接
        """
        self.ssh.close()
        self.ssh_trans.close()
