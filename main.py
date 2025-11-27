#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ETS2 DLC Tools - 主应用程序入口
基于QtPy5的ETS2 DLC管理工具主程序
"""

import sys
import os
from pathlib import Path

# 将项目根目录添加到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtCore import Qt
    from PyQt6.QtGui import QIcon
except ImportError as e:
    print(f"错误: 无法导入PyQt6。请先安装依赖: pip install -r requirements.txt")
    print(f"具体错误: {e}")
    sys.exit(1)

from ui.MainWindow import MainWindow
from config import Config
from utils import setup_logging


def main():
    """主函数"""
    # 设置高DPI支持
    if hasattr(Qt, 'AA_EnableHighDpiScaling'):
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    # 创建QApplication实例
    app = QApplication(sys.argv)
    app.setApplicationName("ETS2 DLC Tools")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("ETS2DLCTools")
    
    # 设置应用程序图标（如果存在）
    icon_path = project_root / "resources" / "icon.ico"
    if icon_path.exists():
        try:
            app_icon = QIcon(str(icon_path))
            if not app_icon.isNull():
                app.setWindowIcon(app_icon)
                print(f"应用程序图标设置成功: {icon_path}")
            else:
                print(f"警告: 图标文件无效: {icon_path}")
        except Exception as e:
            print(f"设置应用程序图标失败: {e}")
    else:
        print(f"警告: 图标文件不存在: {icon_path}")
    
    # 初始化配置
    config = Config()
    
    # 设置日志 - 使用配置文件中的日志设置
    log_config = config.get('logging', {})
    setup_logging(
        level=log_config.get('level', 'INFO'),
        log_file=log_config.get('file', 'logs/app.log'),
        max_size=log_config.get('max_size', 10485760),
        backup_count=log_config.get('backup_count', 5)
    )
    
    try:
        # 创建并显示主窗口
        main_window = MainWindow(config)
        main_window.show()
        
    # 进入事件循环
        sys.exit(app.exec())
        
    except Exception as e:
        print(f"应用程序启动失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()