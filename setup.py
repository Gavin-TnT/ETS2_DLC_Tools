#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ETS2 DLC Tools - cx_Freeze 打包配置
用于创建Windows可执行文件的打包脚本
"""

import sys
from cx_Freeze import setup, Executable
from pathlib import Path

# 基本配置
base = None
if sys.platform == "win32":
    base = "gui"  # Windows GUI应用程序（兼容新版本cx_Freeze）

# 项目根目录
project_root = Path(__file__).parent

# 需要包含的文件和目录
include_files = [
    "config.json",
    "dlcs_info.json",
    "config.py",
    "utils.py",
    "ui/",
    "logs/",
    "README.md",
    "requirements.txt"
]

# 需要包含的Python包
packages = [
    "PyQt6",
    "PIL",
    "requests",
    "colorlog",
    "yaml",
    "pathlib",
    "json",
    "logging",
    "traceback",
    "sys",
    "os"
]

# 排除不需要的包
excludes = [
    "tkinter",
    "matplotlib",
    "numpy",
    "pandas",
    "scipy",
    "test",
    "unittest",
    "pytest",
    "pydoc",
    "doctest"
]

# 构建选项
build_exe_options = {
    "packages": packages,
    "excludes": excludes,
    "include_files": include_files,
    "include_msvcr": True,  # 包含Microsoft Visual C++运行库
    "optimize": 2  # 优化级别
}

# 可执行文件配置
executables = [
    Executable(
        script="main.py",
        base=base,
        target_name="ETS2_DLC_Tools.exe",
        icon=None,  # 可以添加图标文件路径
        copyright="Copyright (C) 2024 ETS2 DLC Tools",
        trademarks="ETS2 DLC Tools",
        shortcut_name="ETS2 DLC Tools",
        shortcut_dir="DesktopFolder"
    )
]

# 设置信息
setup_options = {
    "build_exe": build_exe_options
}

# 执行设置
setup(
    name="ETS2 DLC Tools",
    version="1.0.0",
    description="欧洲卡车模拟2 DLC 管理工具",
    long_description="一个用于管理欧洲卡车模拟2 DLC文件的图形界面工具",
    author="ETS2 DLC Tools Team",
    author_email="",
    url="",
    license="MIT",
    options=setup_options,
    executables=executables
)