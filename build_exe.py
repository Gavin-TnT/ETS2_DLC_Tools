#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ETS2 DLC Tools - 自动化打包脚本
用于自动化构建Windows可执行文件
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

def clean_build_dirs():
    """清理构建目录"""
    print("正在清理构建目录...")
    
    # 需要清理的目录
    dirs_to_clean = ["build", "dist", "__pycache__"]
    
    for dir_name in dirs_to_clean:
        dir_path = Path(dir_name)
        if dir_path.exists():
            try:
                shutil.rmtree(dir_path)
                print(f"已删除目录: {dir_name}")
            except Exception as e:
                print(f"删除目录 {dir_name} 失败: {e}")
    
    # 清理Python缓存文件
    for pycache in Path(".").rglob("__pycache__"):
        try:
            shutil.rmtree(pycache)
            print(f"已删除缓存: {pycache}")
        except Exception as e:
            print(f"删除缓存 {pycache} 失败: {e}")
    
    for pyc in Path(".").rglob("*.pyc"):
        try:
            pyc.unlink()
            print(f"已删除: {pyc}")
        except Exception as e:
            print(f"删除 {pyc} 失败: {e}")

def install_cx_freeze():
    """安装cx_Freeze（如果未安装）"""
    try:
        import cx_Freeze
        print(f"cx_Freeze 已安装")
        return True
    except ImportError:
        print("cx_Freeze 未安装，正在安装...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "cx_Freeze"])
            print("cx_Freeze 安装成功")
            return True
        except subprocess.CalledProcessError as e:
            print(f"cx_Freeze 安装失败: {e}")
            return False

def build_exe():
    """构建可执行文件"""
    print("开始构建可执行文件...")
    
    try:
        # 运行cx_Freeze构建
        result = subprocess.run([
            sys.executable, "setup.py", "build"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("构建成功!")
            print("构建输出:")
            print(result.stdout)
            return True
        else:
            print("构建失败!")
            print("错误输出:")
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"构建过程中发生错误: {e}")
        return False

def create_distribution():
    """创建分发版本"""
    print("创建分发版本...")
    
    # 查找构建目录
    build_dirs = list(Path("build").glob("exe.*"))
    if not build_dirs:
        print("未找到构建目录")
        return False
    
    build_dir = build_dirs[0]  # 获取最新的构建目录
    dist_dir = Path("dist") / "ETS2_DLC_Tools"
    
    try:
        # 复制构建文件到分发目录
        if dist_dir.exists():
            shutil.rmtree(dist_dir)
        
        shutil.copytree(build_dir, dist_dir)
        
        # 注意：根据用户需求，移除了启动脚本和说明文件的生成
        # 如果需要这些文件，可以取消下面的注释
        
        # 创建启动脚本（已注释掉）
        # start_script = dist_dir / "启动程序.bat"
        # start_script.write_text("@echo off\nstart ETS2_DLC_Tools.exe\n", encoding="utf-8")
        
        # 创建说明文件（已注释掉）
        # readme = dist_dir / "使用说明.txt"
        # readme.write_text("""ETS2 DLC Tools - 使用说明

# 1. 双击 ETS2_DLC_Tools.exe 启动程序
# 2. 或者双击 启动程序.bat 启动程序

# 功能说明：
# - 已安装DLC：查看和管理已安装的DLC文件
# - 未安装DLC：查看和管理未安装的DLC文件
# - 设置：配置游戏安装路径

# 注意事项：
# - 程序会自动检测ETS2游戏安装路径
# - DLC文件会被移动到temp_dlcs文件夹而不是删除
# - 支持批量选择和操作

# 技术支持：
# 如有问题，请查看README.md文件
# """, encoding="utf-8")
        
        print(f"分发版本已创建: {dist_dir}")
        return True
        
    except Exception as e:
        print(f"创建分发版本失败: {e}")
        return False

def main():
    """主函数"""
    print("=" * 50)
    print("ETS2 DLC Tools - 打包程序")
    print("=" * 50)
    
    # 检查Python版本
    if sys.version_info < (3, 7):
        print("错误: 需要Python 3.7或更高版本")
        return False
    
    print(f"Python版本: {sys.version}")
    
    # 安装cx_Freeze
    if not install_cx_freeze():
        return False
    
    # 清理构建目录
    clean_build_dirs()
    
    # 构建可执行文件
    if not build_exe():
        return False
    
    # 创建分发版本
    if not create_distribution():
        return False
    
    print("\n" + "=" * 50)
    print("打包完成!")
    print("可执行文件位置: dist/ETS2_DLC_Tools/")
    print("=" * 50)
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)