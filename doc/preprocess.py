#!/usr/bin/env python3
import os
import subprocess
import sys
from string import Template


def main():
    doxy_gen(os.path.abspath(os.path.join('..')))

def doxy_gen(root_path):
    """
    Generate Doxygen configuration file.
    """
    confs = doxy_config(root_path)
    build_path = os.path.join(root_path, "doc", "build", "doxygen")
    gen_path = os.path.join(build_path, "Doxyfile")
    if not os.path.exists(build_path):
        os.makedirs(build_path)
    with open(gen_path, 'w') as fd:
        fd.write("#Please Don't Edit! This config file was autogenerated by ")
        fd.write(f"doxy_gen({root_path}) in doc/preprocess.py.\n")
        for c in confs:
            fd.write(c)

class DoxyTpl(Template):
    delimiter = '@'

def doxy_config(root_path):
    """
    Fetch all Doxygen sub-config files and gather it with the main config file.
    """
    confs = []
    dsrc_path = os.path.join(root_path, "doc", "source")
    sub = dict(ROOT_DIR=root_path)
    with open(os.path.join(dsrc_path, "doxyfile"), "r") as fd:
        conf = DoxyTpl(fd.read())
        confs.append(conf.substitute(CUR_DIR=dsrc_path, **sub))

    for dpath, _, files in os.walk(root_path):
        if ".doxyfile" not in files:
            continue
        conf_path = os.path.join(dpath, ".doxyfile")
        with open(conf_path, "r") as fd:
            conf = DoxyTpl(fd.read())
            confs.append(conf.substitute(CUR_DIR=dpath, **sub))
    return confs


if __name__ == "__main__":
    main()
