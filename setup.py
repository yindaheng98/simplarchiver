#!/usr/bin/env python
# coding: utf-8

from setuptools import setup

with open("README.md", "r", encoding='utf8') as fh:
    long_description = fh.read()

setup(
    name='simplarchiver',
    version='0.0.1',
    author='yindaheng98',
    author_email='yindaheng98@163.com',
    url='https://github.com/yindaheng98/simplarchiver',
    description=u'一个简单的可扩展聚合异步下载器框架',
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=['simplarchiver'],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache License",
        "Operating System :: OS Independent",
    ],
)