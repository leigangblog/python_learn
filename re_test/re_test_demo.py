#!/usr/bin/python
# -*- coding: UTF-8 -*-
"""
@author:lei
@file:re_test_demo.py
@time:2023/05/15
@邮箱：leigang431@163.com
"""
import os
import re
from loguru import logger  # 参考学习：https://blog.csdn.net/Franciz777/article/details/124297656

trace = logger.add('{}_run_log.txt'.format(os.path.basename(__file__).split(".")[0]),
                   format='{time:YYYYMMDD HH:mm:ss} - '  # 时间
                          "{process.name} | "  # 进程名
                          "{thread.name} | "  # 进程名
                          "{module}.{function}:{line} - {level} -{message}",  # 模块名.方法名:行号
                   level="DEBUG")


def run():
    logger.debug("run start")
    strings = "xxxxx12"
    res = re.findall("x", strings)
    print("res:{}".format(res))


def main():
    logger.debug("-----------------------{}-------------------------".format("start"))
    run()
    logger.debug("-----------------------{}-------------------------".format("end"))


if __name__ == '__main__':
    main()
