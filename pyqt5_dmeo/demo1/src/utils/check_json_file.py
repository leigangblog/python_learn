#!/usr/bin/python
# -*- coding: UTF-8 -*-
"""
@author:lei
@file:check_json_file.py
@time:2023/04/29
@邮箱：leigang431@163.com
"""
import json


def check_josn_format_run(json_file):
    with open(json_file,"r") as f:
        try:
            json_object = json.load(f)
            return True
        except ValueError as e:
            print("except info:{}".format(e))
            return False



def main():
    json_file = "keyword.json"
    ret = check_josn_format_run(json_file)
    if (ret):
        print("[INFO]json file format ok")
    else:
        print("[ERROR]json file format error")

if __name__ == '__main__':
    main()
