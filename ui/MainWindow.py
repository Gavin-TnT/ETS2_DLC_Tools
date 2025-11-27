# -*- coding: utf-8 -*-
"""
主窗口类 - MainWindow
基于QtPy5的主窗口实现
"""

from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QMenuBar, QStatusBar, QToolBar, QDockWidget,
                             QTextEdit, QPushButton, QLabel, QLineEdit,
                             QTreeWidget, QTreeWidgetItem, QSplitter,
                             QMessageBox, QFileDialog, QApplication, QToolButton,
                             QFrame, QScrollArea, QGraphicsDropShadowEffect, QSizePolicy,
                             QListWidget, QListWidgetItem)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread, QSize
from PyQt6.QtGui import QFont, QPalette, QColor, QIcon, QPixmap

import os
import logging
import shutil
from pathlib import Path


class MainWindow(QMainWindow):
    """主窗口类"""
    
    # 自定义信号
    status_updated = pyqtSignal(str)
    
    def __init__(self, config=None):
        super().__init__()
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # 初始化游戏路径 - 只通过自动检测获取，不从配置读取
        self.game_path = self.find_ets2_installation_path()
        
        # 初始化UI
        self.init_ui()
        self.setup_menu()
        self.setup_toolbar()
        self.setup_statusbar()

        
        # 添加窗口大小变化监听器
        self.resize_timer = QTimer()
        self.resize_timer.timeout.connect(self.on_resize_complete)
        self.resize_timer.setSingleShot(True)
        
        self.logger.info("主窗口初始化完成")
    
    def init_ui(self):
        """初始化用户界面 - 固定尺寸800x600，禁止用户缩放"""
        # 设置窗口属性
        self.setWindowTitle("ETS2 DLC Tools")
        self.setFixedSize(800, 600)  # 设置固定尺寸800x600，禁止用户缩放
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowMaximizeButtonHint)  # 禁用最大化按钮
        
        # 设置窗口图标
        self.set_window_icon()
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主水平布局 - 160px左侧菜单 + 剩余右侧内容
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 创建左侧菜单栏 (固定宽度160px)
        self.left_panel = self.create_left_panel()
        self.left_panel.setFixedWidth(160)  # 设置固定宽度为160px
        
        # 创建右侧主要内容区域 (剩余宽度)
        self.right_panel = self.create_right_panel()
        
        # 添加到主布局
        main_layout.addWidget(self.left_panel)
        main_layout.addWidget(self.right_panel)
        
        # 应用样式
        self.apply_styles()
    
    def set_window_icon(self):
        """设置窗口图标"""
        icon_path = Path(__file__).parent.parent / "resources" / "icon.png"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))
    
    def create_left_panel(self):
        """创建左侧菜单栏 - 高度占满100%，带阴影效果"""
        panel = QWidget()
        panel.setObjectName("left_menu_panel")  # 用于样式选择
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 启用面板阴影效果
        panel.setGraphicsEffect(self.create_shadow_effect())
        
        # 创建导航栏 - 占满整个高度
        nav_widget = self.create_navigation_bar()
        layout.addWidget(nav_widget)
        
        # 添加弹性空间，确保导航栏在顶部
        layout.addStretch()
        
        return panel
    
    def create_shadow_effect(self):
        """创建阴影效果 - 专业级视觉区分"""
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)  # 增加模糊半径，更柔和的阴影
        shadow.setColor(QColor(0, 0, 0, 80))  # 稍深的半透明黑色阴影
        shadow.setOffset(4, 0)  # 仅右侧阴影，轻微偏移
        return shadow
    
    def create_navigation_bar(self):
        """创建导航栏 - 现代化设计，支持动态内容切换"""
        nav_widget = QWidget()
        nav_widget.setObjectName("navigation_bar")  # 用于样式选择
        nav_layout = QVBoxLayout(nav_widget)
        nav_layout.setContentsMargins(0, 0, 0, 0)
        nav_layout.setSpacing(0)
        
        # 添加标题
        title_label = QLabel("ETS2 DLC Tools")
        title_label.setObjectName("nav_title")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setGraphicsEffect(self.create_shadow_effect())  # 添加阴影效果
        nav_layout.addWidget(title_label)
        
        # 添加分隔线
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setObjectName("nav_separator")
        nav_layout.addWidget(separator)
        
        # 创建图标按钮 - 现代化设计
        self.installed_btn = self.create_nav_button("✓", "已安装DLC", self.show_installed_dlc)
        self.uninstalled_btn = self.create_nav_button("✖", "未安装DLC", self.show_uninstalled_dlc)
        self.settings_btn = self.create_nav_button("⚙", "设置", self.show_settings)
        
        # 添加到布局 - 使用addWidget并设置拉伸属性
        nav_layout.addWidget(self.installed_btn, 0, Qt.AlignmentFlag.AlignTop)
        nav_layout.addWidget(self.uninstalled_btn, 0, Qt.AlignmentFlag.AlignTop)
        nav_layout.addWidget(self.settings_btn, 0, Qt.AlignmentFlag.AlignTop)
        nav_layout.addStretch()
        
        # 默认选中已安装DLC
        self.installed_btn.setChecked(True)
        
        return nav_widget
    
    def create_nav_button(self, icon_text, tooltip, callback):
        """创建导航按钮 - 现代化设计，支持动态切换"""
        btn = QToolButton()
        btn.setText(f"  {icon_text} {tooltip}")  # 添加图标和文字
        btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        btn.setFixedHeight(50)  # 固定高度
        btn.setToolTip(tooltip)
        btn.setCheckable(True)
        btn.setFont(QFont("Segoe UI", 12, QFont.Weight.Normal))
        btn.setObjectName(f"nav_btn_{tooltip.replace(' ', '_')}")  # 用于样式选择
        
        # 设置按钮大小策略为扩展，确保占满父容器宽度
        btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
        # 按钮样式将在apply_styles中统一设置
        btn.clicked.connect(callback)
        return btn
    
    def create_main_workspace(self):
        """创建主工作区"""
        workspace = QWidget()
        layout = QVBoxLayout(workspace)
        
        # 标题区域
        title_area = QWidget()
        title_layout = QHBoxLayout(title_area)
        
        self.workspace_title = QLabel("欢迎使用ETS2 DLC Tools")
        self.workspace_title.setStyleSheet("font-size: 18px; font-weight: bold; padding: 10px;")
        title_layout.addWidget(self.workspace_title)
        
        title_layout.addStretch()
        
        # 刷新按钮
        refresh_btn = QPushButton("刷新")
        refresh_btn.clicked.connect(self.refresh_content)
        title_layout.addWidget(refresh_btn)
        
        layout.addWidget(title_area)
        
        # 主内容区域
        self.content_area = QTextEdit()
        self.content_area.setPlainText("这里将显示DLC详细信息和管理功能...")
        self.content_area.setReadOnly(True)
        layout.addWidget(self.content_area)
        
        # 操作按钮区域
        button_area = QWidget()
        button_layout = QHBoxLayout(button_area)
        
        self.install_btn = QPushButton("安装DLC")
        self.install_btn.clicked.connect(self.install_dlc)
        button_layout.addWidget(self.install_btn)
        
        self.uninstall_btn = QPushButton("卸载DLC")
        self.uninstall_btn.clicked.connect(self.uninstall_dlc)
        button_layout.addWidget(self.uninstall_btn)
        
        self.backup_btn = QPushButton("备份配置")
        self.backup_btn.clicked.connect(self.backup_config)
        button_layout.addWidget(self.backup_btn)
        
        button_layout.addStretch()
        
        layout.addWidget(button_area)
        
        return workspace
    
    def create_right_panel(self):
        """创建右侧主要内容区域 - 支持动态内容切换"""
        panel = QWidget()
        panel.setObjectName("right_content_panel")  # 用于样式选择
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 创建内容堆栈部件，用于切换不同内容
        self.content_stack = QWidget()
        self.content_stack.setObjectName("content_stack")
        self.stack_layout = QVBoxLayout(self.content_stack)
        self.stack_layout.setContentsMargins(20, 20, 20, 20)
        
        # 创建不同内容的页面
        self.create_content_pages()
        
        layout.addWidget(self.content_stack)
        
        return panel
    
    def create_content_pages(self):
        """创建不同菜单对应的内容页面"""
        # 已安装DLC页面
        self.installed_page = self.create_installed_page()
        self.stack_layout.addWidget(self.installed_page)
        
        # 未安装DLC页面
        self.uninstalled_page = self.create_uninstalled_page()
        self.stack_layout.addWidget(self.uninstalled_page)
        
        # 设置页面
        self.settings_page = self.create_settings_page()
        self.stack_layout.addWidget(self.settings_page)
        
        # 默认显示已安装DLC页面
        self.show_installed_dlc()
    

    
    def create_installed_page(self):
        """创建已安装DLC页面"""
        page = QWidget()
        page.setObjectName("installed_page")
        layout = QVBoxLayout(page)
        
        # 页面标题
        header = QWidget()
        header.setObjectName("page_header")
        header_layout = QHBoxLayout(header)
        
        title = QLabel("已安装DLC列表")
        title.setObjectName("page_title")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # 刷新按钮
        refresh_btn = QPushButton("刷新列表")
        refresh_btn.setObjectName("refresh_btn")
        refresh_btn.clicked.connect(self.refresh_installed_dlc)
        header_layout.addWidget(refresh_btn)
        
        layout.addWidget(header)
        
        # DLC文件列表 - 使用QListWidget
        dlc_list = QListWidget()
        dlc_list.setObjectName("installed_dlc_list")
        dlc_list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)  # 允许多选
        layout.addWidget(dlc_list)
        
        # 保存列表引用，用于后续更新
        page.dlc_list = dlc_list
        
        # 操作按钮
        actions = QWidget()
        actions.setObjectName("page_actions")
        actions_layout = QHBoxLayout(actions)
        
        # 卸载选中DLC按钮
        self.uninstall_selected_btn = QPushButton("卸载选中DLC")
        self.uninstall_selected_btn.clicked.connect(self.uninstall_selected_dlcs)
        self.uninstall_selected_btn.setVisible(False)
        actions_layout.addWidget(self.uninstall_selected_btn)
        
        # 卸载所有DLC按钮（初始隐藏）
        self.uninstall_all_btn = QPushButton("卸载所有DLC")
        self.uninstall_all_btn.clicked.connect(self.uninstall_all_dlcs)
        self.uninstall_all_btn.setVisible(False)
        actions_layout.addWidget(self.uninstall_all_btn)
        
        actions_layout.addStretch()
        
        layout.addWidget(actions)
        
        return page
    
    def create_uninstalled_page(self):
        """创建未安装DLC页面"""
        page = QWidget()
        page.setObjectName("uninstalled_page")
        layout = QVBoxLayout(page)
        
        # 页面标题
        header = QWidget()
        header.setObjectName("page_header")
        header_layout = QHBoxLayout(header)
        
        title = QLabel("未安装DLC列表")
        title.setObjectName("page_title")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # 刷新按钮
        refresh_btn = QPushButton("刷新列表")
        refresh_btn.setObjectName("refresh_btn")
        refresh_btn.clicked.connect(self.refresh_uninstalled_dlc)
        header_layout.addWidget(refresh_btn)
        
        layout.addWidget(header)
        
        # DLC文件列表 - 使用QListWidget
        dlc_list = QListWidget()
        dlc_list.setObjectName("dlc_list")
        dlc_list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)  # 允许多选
        layout.addWidget(dlc_list)
        
        # 保存列表引用，用于后续更新
        page.dlc_list = dlc_list
        
        # 操作按钮
        actions = QWidget()
        actions.setObjectName("page_actions")
        actions_layout = QHBoxLayout(actions)
        
        install_btn = QPushButton("安装选中DLC")
        install_btn.clicked.connect(self.install_selected_dlc)
        actions_layout.addWidget(install_btn)
        
        install_all_btn = QPushButton("安装所有DLC")
        install_all_btn.clicked.connect(self.install_all_dlcs)
        actions_layout.addWidget(install_all_btn)
        
        actions_layout.addStretch()
        
        layout.addWidget(actions)
        
        return page
    
    def find_ets2_installation_path(self):
        """自动搜索欧洲卡车模拟2的安装路径"""
        # 常用的安装路径列表
        common_paths = [
            'C:\\Program Files (x86)\\Steam\\steamapps\\common\\Euro Truck Simulator 2',
            'C:\\Program Files\\Steam\\steamapps\\common\\Euro Truck Simulator 2',
            'D:\\Steam\\steamapps\\common\\Euro Truck Simulator 2',
            'D:\\SteamLibrary\\steamapps\\common\\Euro Truck Simulator 2',
            'E:\\Steam\\steamapps\\common\\Euro Truck Simulator 2',
            'E:\\SteamLibrary\\steamapps\\common\\Euro Truck Simulator 2',
            'F:\\Steam\\steamapps\\common\\Euro Truck Simulator 2',
            'F:\\SteamLibrary\\steamapps\\common\\Euro Truck Simulator 2',
            'G:\\Steam\\steamapps\\common\\Euro Truck Simulator 2',
            'G:\\SteamLibrary\\steamapps\\common\\Euro Truck Simulator 2'
        ]
        
        # 检查每个路径是否存在
        for path in common_paths:
            if os.path.exists(path) and os.path.isdir(path):
                # 进一步验证是否存在游戏主程序
                game_exe = os.path.join(path, "bin", "win_x64", "eurotrucks2.exe")
                if os.path.exists(game_exe):
                    self.logger.info(f"找到欧洲卡车模拟2安装路径: {path}")
                    return path
        
        self.logger.info("未找到欧洲卡车模拟2安装路径，使用默认路径")
        return ""

    def create_settings_page(self):
        """创建设置页面"""
        page = QWidget()
        page.setObjectName("settings_page")
        layout = QVBoxLayout(page)
        
        # 页面标题
        title = QLabel("设置选项")
        title.setObjectName("page_title")
        layout.addWidget(title)
        
        # 设置分组
        settings_group = QWidget()
        settings_layout = QVBoxLayout(settings_group)
        
        # 欧洲卡车模拟2游戏路径
        game_path_layout = QHBoxLayout()
        game_path_label = QLabel("游戏路径:")
        game_path_layout.addWidget(game_path_label)
        
        self.game_path_input = QLineEdit()
        self.game_path_input.setPlaceholderText("请选择欧洲卡车模拟2的安装路径...")
        
        # 自动搜索游戏路径
        auto_detected_path = self.find_ets2_installation_path()
        if auto_detected_path:
            self.game_path_input.setText(auto_detected_path)
        else:
            self.game_path_input.setText("C:\\Program Files (x86)\\Steam\\steamapps\\common\\Euro Truck Simulator 2")
        
        game_path_layout.addWidget(self.game_path_input)
        
        game_browse_btn = QPushButton("浏览...")
        game_browse_btn.clicked.connect(self.browse_game_path)
        game_path_layout.addWidget(game_browse_btn)
        
        settings_layout.addLayout(game_path_layout)
        
        # 主题设置已移除
        
        layout.addWidget(settings_group)
        layout.addStretch()
        
        return page
    
    def show_page(self, page_widget):
        """显示指定页面，隐藏其他页面"""
        # 隐藏所有页面
        self.installed_page.hide()
        self.uninstalled_page.hide()
        self.settings_page.hide()
        
        # 显示指定页面
        page_widget.show()
    

    
    def setup_menu(self):
        """设置菜单栏 - 简化版本"""
        pass  # 移除菜单栏
    
    def setup_toolbar(self):
        """设置工具栏 - 简化版本"""
        pass  # 移除工具栏
    
    def setup_statusbar(self):
        """设置状态栏 - 简化版本"""
        pass  # 移除状态栏
    
    def apply_styles(self):
        """应用默认样式"""
        self.setStyleSheet("""
            /* 主窗口样式 */
            QMainWindow {
                background-color: #f8f9fa;
            }
            
            /* 左侧菜单栏样式 */
            QWidget#left_menu_panel {
                background-color: #ffffff;
                border-right: 1px solid #e9ecef;
            }
            
            /* 导航栏标题 */
            QLabel#nav_title {
                font-size: 16px;
                font-weight: bold;
                color: #2c3e50;
                padding: 20px 10px;
                background-color: #f8f9fa;
                border-right: 1px solid #e9ecef;
            }
            
            /* 导航栏分隔线 */
            QFrame#nav_separator {
                background-color: #e9ecef;
                min-height: 1px;
                max-height: 1px;
            }
            
            /* 导航按钮样式 */
            QToolButton {
                border: none;
                background-color: transparent;
                color: #495057;
                font-size: 14px;
                text-align: left;
                padding: 15px 20px;
                margin: 0px;
                border-radius: 0px;
                width: 100%;
            }
            
            QToolButton:hover {
                background-color: #f1f3f4;
                color: #212529;
                border-left: 3px solid #007bff;
            }
            
            QToolButton:pressed {
                background-color: #e9ecef;
            }
            
            QToolButton:checked {
                background-color: #e3f2fd;
                color: #1976d2;
                border-left: 3px solid #1976d2;
                font-weight: 500;
            }
            
            /* 右侧内容区域样式 */
            QWidget#right_content_panel {
                background-color: #f8f9fa;
            }
            
            QWidget#content_stack {
                background-color: #ffffff;
                border-radius: 8px;
                margin: 20px;
            }
            
            /* 页面标题 */
            QLabel#page_title {
                font-size: 24px;
                font-weight: bold;
                color: #2c3e50;
                padding: 20px 0px;
            }
            
            /* 页面副标题 */
            QLabel#page_subtitle {
                font-size: 16px;
                color: #6c757d;
                padding: 10px 0px;
            }
            
            /* 页面功能介绍 */
            QLabel#page_features {
                font-size: 14px;
                color: #495057;
                line-height: 1.6;
                padding: 20px;
                background-color: #f8f9fa;
                border-radius: 8px;
                border: 1px solid #e9ecef;
            }
            
            /* 页面头部 */
            QWidget#page_header {
                border-bottom: 1px solid #e9ecef;
                padding-bottom: 15px;
                margin-bottom: 20px;
            }
            
            /* 内容区域 */
            QTextEdit#content_area {
                border: 1px solid #e9ecef;
                border-radius: 4px;
                background-color: #ffffff;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 13px;
                color: #212529;
            }
            
            /* 游戏路径信息区域 */
            QWidget#path_info {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 10px;
                margin: 10px 0;
            }
            
            QLabel#path_label {
                font-weight: bold;
                color: #495057;
                min-width: 100px;
            }
            

            
            /* 页面操作按钮区域 */
            QWidget#page_actions {
                border-top: 1px solid #e9ecef;
                padding-top: 15px;
                margin-top: 20px;
            }
            
            /* 按钮样式 */
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 14px;
                font-weight: 500;
                min-width: 100px;
            }
            
            QPushButton:hover {
                background-color: #0056b3;
            }
            
            QPushButton:pressed {
                background-color: #004085;
            }
            
            /* 输入框样式 */
            QLineEdit {
                border: 1px solid #ced4da;
                border-radius: 4px;
                padding: 8px 12px;
                font-size: 14px;
                background-color: #ffffff;
                color: #495057;
            }
            
            QLineEdit:focus {
                border-color: #80bdff;
                outline: none;
            }
            
            /* 标签样式 */
            QLabel {
                color: #212529;
                font-size: 14px;
            }
        """)
    
    # 事件处理方法

    
    def refresh_content(self):
        """刷新内容 - 简化版本"""
        self.logger.info("刷新内容")
    
    def install_dlc(self):
        """安装DLC - 简化版本"""
        self.logger.info("安装DLC功能")
    
    def uninstall_dlc(self):
        """卸载DLC - 简化版本"""
        self.logger.info("卸载DLC功能")
    
    def backup_config(self):
        """备份配置 - 简化版本"""
        self.logger.info("备份配置功能")
    
    def open_file(self):
        """打开文件 - 简化版本"""
        self.logger.info("打开文件功能")
    
    def save_file(self):
        """保存文件 - 简化版本"""
        self.logger.info("保存文件功能")
    
    def show_installed_dlc(self):
        """显示已安装DLC"""
        self.update_nav_button_state(self.installed_btn)
        self.show_page(self.installed_page)
        self.logger.info("显示已安装DLC")
        
        # 检查DLC文件
        self.check_and_display_dlcs()
    
    def show_uninstalled_dlc(self):
        """显示未安装的DLC - 动态切换内容"""
        self.update_nav_button_state(self.uninstalled_btn)
        self.show_page(self.uninstalled_page)
        self.logger.info("显示未安装DLC")
        
        # 自动刷新未安装DLC列表
        self.refresh_uninstalled_dlc()
    
    def update_nav_button_state(self, active_button):
        """更新导航按钮状态"""
        # 重置所有按钮
        self.installed_btn.setChecked(False)
        self.uninstalled_btn.setChecked(False)
        self.settings_btn.setChecked(False)
        
        # 设置活跃按钮
        active_button.setChecked(True)
    
    # 新增页面交互功能
    def refresh_installed_dlc(self):
        """刷新已安装DLC列表"""
        self.logger.info("刷新已安装DLC列表")
        # 重新检查DLC文件
        self.check_and_display_dlcs()
    
    def check_and_display_dlcs(self):
        """检查DLC文件并显示相应信息"""
        try:
            # 优先从设置界面的输入框获取路径，若为空则尝试从config读取
            game_path = self.game_path_input.text().strip() if hasattr(self, 'game_path_input') and self.game_path_input.text().strip() else (
                self.config.get('dlc', {}).get('game_path', '') if hasattr(self.config, 'get') else self.config.get("game_path", "")
            )
            if not game_path or not os.path.exists(game_path):
                self.installed_page.content_area.setPlainText("未找到游戏安装路径")
                self.uninstall_all_btn.setVisible(False)
                return
            
            # 查找以dlc开头，后缀为.scs的文件
            dlc_files = []
            for file in os.listdir(game_path):
                if file.lower().startswith("dlc") and file.lower().endswith(".scs"):
                    dlc_files.append(file)
            
            # 清空列表并重新填充
            self.installed_page.dlc_list.clear()
            
            if dlc_files:
                # 按名称排序并添加到列表
                for file in sorted(dlc_files):
                    item = QListWidgetItem(file)
                    item.setData(Qt.ItemDataRole.UserRole, file)  # 保存文件名到item数据中
                    self.installed_page.dlc_list.addItem(item)
                
                self.uninstall_selected_btn.setVisible(True)
                self.uninstall_all_btn.setVisible(True)
                self.logger.info(f"在 {game_path} 中找到 {len(dlc_files)} 个DLC文件")
            else:
                # 未找到DLC文件
                item = QListWidgetItem("未找到DLC文件")
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEnabled)  # 禁用该项
                self.installed_page.dlc_list.addItem(item)
                self.uninstall_selected_btn.setVisible(False)
                self.uninstall_all_btn.setVisible(False)
                self.logger.info(f"在 {game_path} 中未找到DLC文件")
                
        except Exception as e:
            self.installed_page.dlc_list.clear()
            error_item = QListWidgetItem(f"检查DLC文件时出错: {str(e)}")
            error_item.setFlags(error_item.flags() & ~Qt.ItemFlag.ItemIsEnabled)
            self.installed_page.dlc_list.addItem(error_item)
            self.uninstall_selected_btn.setVisible(False)
            self.uninstall_all_btn.setVisible(False)
            self.logger.error(f"检查DLC文件时出错: {e}")
    
    def uninstall_all_dlcs(self):
        """卸载所有DLC"""
        try:
            # 优先从设置界面的输入框获取路径，若为空则尝试从config读取
            game_path = self.game_path_input.text().strip() if hasattr(self, 'game_path_input') and self.game_path_input.text().strip() else (
                self.config.get('dlc', {}).get('game_path', '') if hasattr(self.config, 'get') else self.config.get("game_path", "")
            )
            if not game_path or not os.path.exists(game_path):
                QMessageBox.warning(self, "警告", "未找到游戏安装路径")
                return
            
            # 创建temp_dlcs文件夹
            temp_dir = os.path.join(game_path, "temp_dlcs")
            if not os.path.exists(temp_dir):
                os.makedirs(temp_dir)
                self.logger.info(f"创建临时DLC文件夹: {temp_dir}")
            
            # 查找所有DLC文件
            dlc_files = []
            for file in os.listdir(game_path):
                if file.lower().startswith("dlc") and file.lower().endswith(".scs"):
                    dlc_files.append(file)
            
            if not dlc_files:
                QMessageBox.information(self, "提示", "未找到DLC文件")
                return
            
            # 确认对话框
            reply = QMessageBox.question(
                self, "确认卸载", 
                f"确定要卸载 {len(dlc_files)} 个DLC文件吗？\n文件将被移动到: {temp_dir}",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                moved_files = []
                for dlc_file in dlc_files:
                    src_path = os.path.join(game_path, dlc_file)
                    dst_path = os.path.join(temp_dir, dlc_file)
                    
                    try:
                        shutil.move(src_path, dst_path)
                        moved_files.append(dlc_file)
                        self.logger.info(f"移动DLC文件: {dlc_file} -> {temp_dir}")
                    except Exception as e:
                        self.logger.error(f"移动文件 {dlc_file} 失败: {e}")
                
                if moved_files:
                    QMessageBox.information(
                        self, "成功", 
                        f"已成功卸载 {len(moved_files)} 个DLC文件"
                    )
                    # 重新检查并更新显示
                    self.check_and_display_dlcs()
                else:
                    QMessageBox.warning(self, "警告", "没有文件被移动")
                    
        except Exception as e:
            QMessageBox.critical(self, "错误", f"卸载DLC时出错: {str(e)}")
            self.logger.error(f"卸载DLC时出错: {e}")
    
    def uninstall_selected_dlcs(self):
        """卸载选中的DLC - 将游戏安装路径中选中的DLC文件移动到temp_dlcs文件夹"""
        self.logger.info("卸载选中的DLC")
        try:
            # 获取游戏路径
            game_path = self.game_path_input.text().strip() if hasattr(self, 'game_path_input') and self.game_path_input.text().strip() else (
                self.config.get('dlc', {}).get('game_path', '') if hasattr(self.config, 'get') else self.config.get("game_path", "")
            )
            if not game_path or not os.path.exists(game_path):
                QMessageBox.warning(self, "警告", "未找到游戏安装路径")
                return
            
            # 获取选中的DLC文件
            selected_items = self.installed_page.dlc_list.selectedItems()
            if not selected_items:
                QMessageBox.information(self, "提示", "请先选择要卸载的DLC文件")
                return
            
            # 提取选中的文件名
            selected_files = []
            for item in selected_items:
                file_name = item.data(Qt.ItemDataRole.UserRole)
                if file_name:
                    selected_files.append(file_name)
            
            if not selected_files:
                QMessageBox.information(self, "提示", "未找到有效的DLC文件")
                return
            
            # 创建temp_dlcs文件夹
            temp_dir = os.path.join(game_path, "temp_dlcs")
            if not os.path.exists(temp_dir):
                os.makedirs(temp_dir)
                self.logger.info(f"创建temp_dlcs文件夹: {temp_dir}")
            
            # 确认对话框
            reply = QMessageBox.question(
                self, "确认卸载", 
                f"确定要卸载 {len(selected_files)} 个选中的DLC文件吗？\n文件将被移动到 {temp_dir} 文件夹",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                moved_files = []
                for dlc_file in selected_files:
                    src_path = os.path.join(game_path, dlc_file)
                    dst_path = os.path.join(temp_dir, dlc_file)
                    
                    try:
                        # 检查源文件是否存在
                        if not os.path.exists(src_path):
                            self.logger.warning(f"源文件不存在，跳过: {dlc_file}")
                            continue
                        
                        # 检查目标文件是否已存在
                        if os.path.exists(dst_path):
                            self.logger.warning(f"目标文件已存在，跳过: {dlc_file}")
                            continue
                        
                        # 移动文件（剪切操作）
                        shutil.move(src_path, dst_path)
                        moved_files.append(dlc_file)
                        self.logger.info(f"移动DLC文件: {dlc_file} -> {temp_dir}")
                    except Exception as e:
                        self.logger.error(f"移动文件 {dlc_file} 失败: {e}")
                
                if moved_files:
                    QMessageBox.information(
                        self, "成功", 
                        f"已成功卸载 {len(moved_files)} 个DLC文件"
                    )
                    # 重新检查并更新显示
                    self.check_and_display_dlcs()
                    # 同时刷新未安装DLC列表
                    self.refresh_uninstalled_dlc()
                else:
                    QMessageBox.warning(self, "警告", "没有文件被移动，可能目标位置已存在相同文件或源文件不存在")
                    
        except Exception as e:
            QMessageBox.critical(self, "错误", f"卸载DLC时出错: {str(e)}")
            self.logger.error(f"卸载DLC时出错: {e}")
    
    def disable_selected_dlc(self):
        """禁用选中的DLC"""
        self.logger.info("禁用选中的DLC")
        # 这里添加实际的禁用逻辑
    
    def refresh_uninstalled_dlc(self):
        """刷新未安装DLC列表"""
        self.logger.info("刷新未安装DLC列表")
        try:
            # 获取游戏路径
            game_path = self.game_path_input.text().strip() if hasattr(self, 'game_path_input') and self.game_path_input.text().strip() else (
                self.config.get('dlc', {}).get('game_path', '') if hasattr(self.config, 'get') else self.config.get("game_path", "")
            )
            if not game_path or not os.path.exists(game_path):
                self.uninstalled_page.dlc_list.clear()
                return
            
            # 检查temp_dlcs文件夹
            temp_dir = os.path.join(game_path, "temp_dlcs")
            if not os.path.exists(temp_dir):
                self.uninstalled_page.dlc_list.clear()
                return
            
            # 查找temp_dlcs文件夹中的DLC文件
            dlc_files = []
            for file in os.listdir(temp_dir):
                if file.lower().startswith("dlc") and file.lower().endswith(".scs"):
                    dlc_files.append(file)
            
            # 清空列表并重新填充
            self.uninstalled_page.dlc_list.clear()
            
            if dlc_files:
                # 按名称排序并添加到列表
                for file in sorted(dlc_files):
                    item = QListWidgetItem(file)
                    item.setData(Qt.ItemDataRole.UserRole, file)  # 保存文件名到item数据中
                    self.uninstalled_page.dlc_list.addItem(item)
                
                self.logger.info(f"在 {temp_dir} 中找到 {len(dlc_files)} 个已卸载的DLC文件")
            else:
                # 未找到DLC文件
                item = QListWidgetItem("temp_dlcs文件夹中没有找到DLC文件")
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEnabled)  # 禁用该项
                self.uninstalled_page.dlc_list.addItem(item)
                self.logger.info(f"在 {temp_dir} 中未找到DLC文件")
                
        except Exception as e:
            self.uninstalled_page.dlc_list.clear()
            error_item = QListWidgetItem(f"检查已卸载DLC文件时出错: {str(e)}")
            error_item.setFlags(error_item.flags() & ~Qt.ItemFlag.ItemIsEnabled)
            self.uninstalled_page.dlc_list.addItem(error_item)
            self.logger.error(f"检查已卸载DLC文件时出错: {e}")
    
    def install_selected_dlc(self):
        """安装选中的DLC - 将temp_dlcs文件夹中选中的DLC文件移回游戏安装路径"""
        self.logger.info("安装选中的DLC")
        try:
            # 获取游戏路径
            game_path = self.game_path_input.text().strip() if hasattr(self, 'game_path_input') and self.game_path_input.text().strip() else (
                self.config.get('dlc', {}).get('game_path', '') if hasattr(self.config, 'get') else self.config.get("game_path", "")
            )
            if not game_path or not os.path.exists(game_path):
                QMessageBox.warning(self, "警告", "未找到游戏安装路径")
                return
            
            # 检查temp_dlcs文件夹
            temp_dir = os.path.join(game_path, "temp_dlcs")
            if not os.path.exists(temp_dir):
                QMessageBox.information(self, "提示", "未找到temp_dlcs文件夹，没有可安装的DLC")
                return
            
            # 获取选中的DLC文件
            selected_items = self.uninstalled_page.dlc_list.selectedItems()
            if not selected_items:
                QMessageBox.information(self, "提示", "请先选择要安装的DLC文件")
                return
            
            # 提取选中的文件名
            selected_files = []
            for item in selected_items:
                file_name = item.data(Qt.ItemDataRole.UserRole)
                if file_name:
                    selected_files.append(file_name)
            
            if not selected_files:
                QMessageBox.information(self, "提示", "未找到有效的DLC文件")
                return
            
            # 确认对话框
            reply = QMessageBox.question(
                self, "确认安装", 
                f"确定要安装 {len(selected_files)} 个选中的DLC文件吗？\n文件将从 {temp_dir} 移回游戏安装路径",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                moved_files = []
                for dlc_file in selected_files:
                    src_path = os.path.join(temp_dir, dlc_file)
                    dst_path = os.path.join(game_path, dlc_file)
                    
                    try:
                        # 检查源文件是否存在
                        if not os.path.exists(src_path):
                            self.logger.warning(f"源文件不存在，跳过: {dlc_file}")
                            continue
                        
                        # 检查目标文件是否已存在
                        if os.path.exists(dst_path):
                            self.logger.warning(f"目标文件已存在，跳过: {dlc_file}")
                            continue
                        
                        # 移动文件（剪切操作）
                        shutil.move(src_path, dst_path)
                        moved_files.append(dlc_file)
                        self.logger.info(f"移动DLC文件: {dlc_file} -> {game_path}")
                    except Exception as e:
                        self.logger.error(f"移动文件 {dlc_file} 失败: {e}")
                
                if moved_files:
                    QMessageBox.information(
                        self, "成功", 
                        f"已成功安装 {len(moved_files)} 个DLC文件"
                    )
                    # 重新检查并更新显示
                    self.refresh_uninstalled_dlc()
                    # 同时刷新已安装DLC列表
                    self.check_and_display_dlcs()
                else:
                    QMessageBox.warning(self, "警告", "没有文件被移动，可能目标位置已存在相同文件或源文件不存在")
                    
        except Exception as e:
            QMessageBox.critical(self, "错误", f"安装DLC时出错: {str(e)}")
            self.logger.error(f"安装DLC时出错: {e}")
    
    def install_all_dlcs(self):
        """安装所有DLC - 将temp_dlcs文件夹中的所有DLC文件移回游戏安装路径"""
        self.logger.info("安装所有DLC")
        try:
            # 获取游戏路径
            game_path = self.game_path_input.text().strip() if hasattr(self, 'game_path_input') and self.game_path_input.text().strip() else (
                self.config.get('dlc', {}).get('game_path', '') if hasattr(self.config, 'get') else self.config.get("game_path", "")
            )
            if not game_path or not os.path.exists(game_path):
                QMessageBox.warning(self, "警告", "未找到游戏安装路径")
                return
            
            # 检查temp_dlcs文件夹
            temp_dir = os.path.join(game_path, "temp_dlcs")
            if not os.path.exists(temp_dir):
                QMessageBox.information(self, "提示", "未找到temp_dlcs文件夹，没有可安装的DLC")
                return
            
            # 查找temp_dlcs文件夹中的所有DLC文件
            dlc_files = []
            for file in os.listdir(temp_dir):
                if file.lower().startswith("dlc") and file.lower().endswith(".scs"):
                    dlc_files.append(file)
            
            if not dlc_files:
                QMessageBox.information(self, "提示", "temp_dlcs文件夹中没有找到DLC文件")
                return
            
            # 确认对话框
            reply = QMessageBox.question(
                self, "确认安装", 
                f"确定要安装所有 {len(dlc_files)} 个DLC文件吗？\n文件将从 {temp_dir} 移回游戏安装路径",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                moved_files = []
                for dlc_file in dlc_files:
                    src_path = os.path.join(temp_dir, dlc_file)
                    dst_path = os.path.join(game_path, dlc_file)
                    
                    try:
                        # 检查源文件是否存在
                        if not os.path.exists(src_path):
                            self.logger.warning(f"源文件不存在，跳过: {dlc_file}")
                            continue
                        
                        # 检查目标文件是否已存在
                        if os.path.exists(dst_path):
                            self.logger.warning(f"目标文件已存在，跳过: {dlc_file}")
                            continue
                        
                        # 移动文件（剪切操作）
                        shutil.move(src_path, dst_path)
                        moved_files.append(dlc_file)
                        self.logger.info(f"移动DLC文件: {dlc_file} -> {game_path}")
                    except Exception as e:
                        self.logger.error(f"移动文件 {dlc_file} 失败: {e}")
                
                if moved_files:
                    QMessageBox.information(
                        self, "成功", 
                        f"已成功安装 {len(moved_files)} 个DLC文件"
                    )
                    # 重新检查并更新显示
                    self.refresh_uninstalled_dlc()
                    # 同时刷新已安装DLC列表
                    self.check_and_display_dlcs()
                else:
                    QMessageBox.warning(self, "警告", "没有文件被移动，可能目标位置已存在相同文件或源文件不存在")
                    
        except Exception as e:
            QMessageBox.critical(self, "错误", f"安装DLC时出错: {str(e)}")
            self.logger.error(f"安装DLC时出错: {e}")
    
    def browse_game_path(self):
        """浏览欧洲卡车模拟2游戏路径"""
        self.logger.info("浏览欧洲卡车模拟2游戏路径")
        
        # 获取当前路径作为初始目录
        current_path = self.game_path_input.text()
        initial_dir = current_path if current_path and os.path.exists(current_path) else "C:\\"
        
        # 打开文件夹选择对话框
        directory = QFileDialog.getExistingDirectory(
            self,
            "选择欧洲卡车模拟2安装目录",
            initial_dir,
            QFileDialog.Option.ShowDirsOnly | QFileDialog.Option.DontResolveSymlinks
        )
        
        # 如果用户选择了目录，更新输入框
        if directory:
            self.game_path_input.setText(directory)
            self.logger.info(f"用户选择了游戏路径: {directory}")
    
    def save_settings(self):
        """保存设置"""
        self.logger.info("保存设置")
        # 获取设置值
        game_path = self.game_path_input.text()
        
        self.logger.info(f"游戏路径: {game_path}")
        # 这里添加实际的保存逻辑
    
    def filter_dlc_list(self, status_filter):
        """根据状态过滤DLC列表"""
        self.workspace_title.setText(f"{status_filter}的DLC")
        self.content_area.setPlainText(f"显示{status_filter}的DLC列表...")
        self.status_updated.emit(f"显示{status_filter}的DLC")
    
    def show_settings(self):
        """显示设置页面 - 动态切换内容"""
        self.update_nav_button_state(self.settings_btn)
        self.show_page(self.settings_page)
        self.logger.info("显示设置")
    
    def show_about(self):
        """显示关于对话框 - 简化版本"""
        self.logger.info("显示关于对话框")
    
    def resizeEvent(self, event):
        """窗口大小变化事件 - 响应式布局调整"""
        # 延迟调整布局，避免频繁重绘
        self.resize_timer.start(100)
        super().resizeEvent(event)
    
    def on_resize_complete(self):
        """窗口大小调整完成后的处理"""
        # 窗口为固定尺寸800x600，无需调整布局
        # 左侧菜单宽度固定为160px
        self.logger.info(f"窗口大小: 800x600(固定), 左侧菜单宽度: 160px(固定)")
    
    def closeEvent(self, event):
        """关闭事件处理 - 简化版本"""
        self.logger.info("应用程序正在关闭...")
        event.accept()