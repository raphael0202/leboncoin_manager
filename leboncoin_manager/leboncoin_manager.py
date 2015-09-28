#!/usr/bin/python3
# coding: utf-8

import argparse
import configparser
import os
import sys
import ast

from leboncoin_manager.core import LeboncoinManager

launch_directory = os.environ["PWD"]

parser = argparse.ArgumentParser()
parser.add_argument("-c", "--config-file", help="path of the configuration file")
args = parser.parse_args()

config_file_path = args.config_file

if config_file_path is None:
    sys.exit("A configuration file is needed.")

if not os.path.isfile(config_file_path):
    sys.exit("The configuration path file is incorrect")

config = configparser.ConfigParser()
config.read(config_file_path)

for section in config.sections():
    action = config[section].pop("action")
    username = config[section].pop("username")
    password = config[section].pop("password")
    parameters = dict(config[section].items())

    if "image_path_list" in config[section]:
        parameters["image_path_list"] = ast.literal_eval(config[section]["image_path_list"])

        for n, image_path in enumerate(parameters["image_path_list"]):
            if not image_path.startswith("/"):
                parameters["image_path_list"][n] = os.path.join(launch_directory, image_path)
                print(parameters["image_path_list"][n])

    manager = LeboncoinManager(username, password)

    if action == "update":
        manager.update(**parameters)

    if action == "publish":
        manager.publish(**parameters)

    manager.quit()
