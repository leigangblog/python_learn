#!/usr/bin/python
# -*- coding: UTF-8 -*-
"""
@author:lei
@utils:mock_file.py.py
@time:2023/04/29
@邮箱：leigang431@163.com
"""
import os
import random

# 环境变量
LOG_LEVEL=["DEBUG","INFO","WARN","ERROR","EMEGR"]
LINE_NUM = 100

# 检测文件夹是否存在
def check_path(path):
    # 运行日志记录
    # print("check_path run")
    if not os.path.exists(path):
        os.makedirs(path)

# 生成文件
def mock_file_run(dest_file):
    # 运行日志记录
    # print("mock_file_run run")
    # 生成文件
    with open(dest_file,"w") as file:
        for i in range(LINE_NUM):
            random_num = random.randint(0, 4)
            # print("random_num:{}".format(random_num))
            log_str="[{}]line:{}\n".format(LOG_LEVEL[random_num],str(i))
            file.write(log_str)
        file.write("\n")

def main():
    dest_path = "./mock"
    check_path(dest_path)
    for i in range(10):
        dest_path = os.path.join(os.path.abspath("./"),dest_path)
        dest_file = "{}/{}.txt".format(dest_path,i)
        print("dest_file：{}".format(dest_file))
        mock_file_run(dest_file)

if __name__ == '__main__':
    main()