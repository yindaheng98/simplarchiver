#!/usr/bin/env python
# coding: utf-8

from setuptools import setup

with open("README.md", "r", encoding='utf8') as fh:
    long_description = fh.read()

package_dir = {
    'simplarchiver': 'simplarchiver',
    'simplarchiver.example': 'simplarchiver/example',
    'simplarchiver.example.file': 'simplarchiver/example/file',
    'simplarchiver.example.qbittorrent': 'simplarchiver/example/qbittorrent',
    'simplarchiver.example.rss': 'simplarchiver/example/rss'
}

setup(
    name='simplarchiver',
    version='1.12',
    author='yindaheng98',
    author_email='yindaheng98@163.com',
    url='https://github.com/yindaheng98/simplarchiver',
    description=u'一个简单的可扩展聚合异步下载器框架',
    long_description=long_description,
    long_description_content_type="text/markdown",
    package_dir=package_dir,
    packages=[key for key in package_dir],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
