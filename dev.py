#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
开发模式启动脚本 - 使用热加载功能
当检测到代码文件变化时，自动重启应用程序
"""

import sys
import os
from pathlib import Path

# 将项目根目录添加到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from hot_reload import HotReloader


def main():
    """主函数 - 启动热加载开发模式"""
    print("=" * 70)
    print("ETS2 DLC Tools - 开发模式 (热加载已启用)")
    print("=" * 70)
    print()
    print("功能说明:")
    print("  • 自动监控 Python 文件、JSON 配置文件的变化")
    print("  • 检测到文件修改后自动重启应用")
    print("  • 提高开发效率，无需手动重启")
    print()
    print("监控范围:")
    print("  • Python 文件 (.py)")
    print("  • 配置文件 (.json)")
    print("  • UI 文件 (.ui)")
    print()
    print("忽略目录:")
    print("  • __pycache__, .git, .idea, logs, Output, venv, env")
    print()
    print("按 Ctrl+C 可以停止开发服务器")
    print("=" * 70)
    print()
    
    # 主脚本路径
    main_script = "main.py"
    
    # 检查主脚本是否存在
    if not os.path.exists(main_script):
        print(f"错误: 找不到主脚本 '{main_script}'")
        print(f"请确保在项目根目录下运行此脚本")
        sys.exit(1)
    
    # 配置热加载
    reloader = HotReloader(
        script_path=main_script,
        watch_dirs=['.'],  # 监控当前目录及子目录
        extensions=['.py', '.json', '.ui'],  # 监控的文件类型
        ignore_dirs=[
            '__pycache__', 
            '.git', 
            '.idea', 
            'logs', 
            'Output', 
            'venv', 
            'env',
            '.venv',
            'build',
            'dist'
        ]
    )
    
    # 启动热加载
    try:
        reloader.start_watching()
    except KeyboardInterrupt:
        print("\n开发服务器已停止")
    except Exception as e:
        print(f"\n错误: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()