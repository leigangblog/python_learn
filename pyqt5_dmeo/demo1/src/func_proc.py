#!/usr/bin/python
# -*- coding: UTF-8 -*-
"""
@author:lei
@utils:func_proc.py.py
@time:2023/04/29
@邮箱：leigang431@163.com
"""
import os
import time
from loguru import logger
import argparse

trace = logger.add('{}_run_log.txt'.format(os.path.basename(__file__).split(".")[0]),  format='{time:YYYYMMDD HH:mm:ss} - '  # 时间
                               "{process.name} | "  # 进程名
                               "{thread.name} | "  # 进程名
                               '{module}.{function}:{line} - {level} -{message}',  # 模块名.方法名:行号
                                level="DEBUG")

# 入参解析
def parse_args(args):
    logger.debug("parse_args start")
    if args.src_path is None:
        logger.debug("src_path args is None")
        exit()
    if args.dest_path is None:
        logger.debug("dest_path args is None")
        exit()
    if args.keyword is None:
        logger.debug("keyword args is None")
        exit()
    src_path = args.src_path
    dest_path = args.dest_path
    keyword =args.keyword
    return src_path, dest_path,keyword

def parse_json(json_file):
    logger.debug("parse_json:{}".format(json_file))


def func_proc_run(src_path, dest_path,keyword):
    logger.debug("run start")
    logger.debug("src_path:{},dest_path:{},keyword:{}".format(src_path, dest_path,keyword))


def main(args):
    logger.debug("main start")
    src_path, dest_path,keyword = parse_args(args)
    func_proc_run(src_path, dest_path, keyword)



if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="[demo-20230430]Demo of argparse")
    parser.add_argument('-s','--src_path', default="log",type=str, help='path of file of src log')
    parser.add_argument('-d','--dest_path',default="decode_log",type=str, help='path of dest log')
    parser.add_argument('-k', '--keyword', default="keyword.json", type=str, help='path of keyword.json')
    args = parser.parse_args()
    main(args)
