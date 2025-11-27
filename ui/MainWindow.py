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
                             QListWidget, QListWidgetItem, QComboBox)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread, QSize, QUrl
from PyQt6.QtGui import QFont, QPalette, QColor, QIcon, QPixmap, QDesktopServices

import os
import logging
import shutil
from pathlib import Path
from language_manager import get_language_manager, tr


class MainWindow(QMainWindow):
    """主窗口类"""
    
    # 自定义信号
    status_updated = pyqtSignal(str)
    
    def __init__(self, config=None):
        super().__init__()
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        self.language_manager = get_language_manager()
        
        # 初始化游戏路径 - 只通过自动检测获取，不从配置读取
        self.game_path = self.find_ets2_installation_path()
        
        # 加载保存的语言设置
        saved_language = self.config.get('ui.language', 'zh_CN')
        if saved_language in ['zh_CN', 'en']:
            self.language_manager.load_language(saved_language)
            self.logger.info(f"已加载保存的语言设置: {saved_language}")
        
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
        self.setWindowTitle(tr('app_title'))
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
        icon_path = Path(__file__).parent.parent / "resources" / "icon.ico"
        if icon_path.exists():
            try:
                icon = QIcon(str(icon_path))
                if not icon.isNull():
                    self.setWindowIcon(icon)
                    # 同时设置任务栏图标
                    from PyQt6.QtWidgets import QApplication
                    QApplication.instance().setWindowIcon(icon)
                    self.logger.info(f"窗口图标设置成功: {icon_path}")
                else:
                    self.logger.warning(f"图标文件无效: {icon_path}")
            except Exception as e:
                self.logger.error(f"设置窗口图标失败: {e}")
        else:
            self.logger.warning(f"图标文件不存在: {icon_path}")
    
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
        title_label = QLabel(tr('app_title'))
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
        self.installed_btn = self.create_nav_button("✓", tr('nav.installed_dlc'), self.show_installed_dlc)
        self.uninstalled_btn = self.create_nav_button("✖", tr('nav.uninstalled_dlc'), self.show_uninstalled_dlc)
        self.settings_btn = self.create_nav_button("⚙", tr('nav.settings'), self.show_settings)
        
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
    

    
    def create_github_button(self):
        """创建GitHub图标按钮"""
        github_btn = QToolButton()
        github_btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        github_btn.setFixedSize(32, 32)
        github_btn.setToolTip("访问GitHub仓库")
        
        # GitHub图标文件路径
        github_icon_path = Path(__file__).parent.parent / "resources" / "github_icon.png"
        
        if github_icon_path.exists():
            try:
                # 创建GitHub图标
                github_icon = QIcon(str(github_icon_path))
                if not github_icon.isNull():
                    github_btn.setIcon(github_icon)
                    github_btn.setIconSize(QSize(24, 24))
                    github_btn.setStyleSheet("""
                        QToolButton {
                            border: none;
                            border-radius: 4px;
                            background-color: transparent;
                            padding: 4px;
                        }
                        QToolButton:hover {
                            background-color: rgba(0, 0, 0, 0.1);
                        }
                        QToolButton:pressed {
                            background-color: rgba(0, 0, 0, 0.2);
                        }
                    """)
                    self.logger.info(f"GitHub图标设置成功: {github_icon_path}")
                else:
                    self.logger.warning(f"GitHub图标文件无效: {github_icon_path}")
                    self.set_fallback_github_icon(github_btn)
            except Exception as e:
                self.logger.error(f"设置GitHub图标失败: {e}")
                self.set_fallback_github_icon(github_btn)
        else:
            self.logger.warning(f"GitHub图标文件不存在: {github_icon_path}")
            self.set_fallback_github_icon(github_btn)
        
        # 连接点击事件到GitHub仓库
        github_btn.clicked.connect(self.open_github_repo)
        return github_btn
    
    def set_fallback_github_icon(self, github_btn):
        """设置备用的GitHub图标（使用emoji）"""
        github_btn.setText("🐙")  # 使用章鱼emoji作为GitHub图标
        github_btn.setStyleSheet("""
            QToolButton {
                font-size: 20px;
                border: none;
                border-radius: 4px;
                background-color: transparent;
                padding: 4px;
            }
            QToolButton:hover {
                background-color: rgba(0, 0, 0, 0.1);
            }
        """)
    
    def create_github_button_for_settings(self):
        """为设置页面创建GitHub图标按钮"""
        github_btn = QPushButton()
        github_btn.setToolTip(tr('settings.github_repo'))
        github_btn.setFixedHeight(40)
        github_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
        # GitHub图标文件路径
        github_icon_path = Path(__file__).parent.parent / "resources" / "github_icon.png"
        
        if github_icon_path.exists():
            try:
                # 创建GitHub图标
                github_icon = QIcon(str(github_icon_path))
                if not github_icon.isNull():
                    github_btn.setIcon(github_icon)
                    github_btn.setIconSize(QSize(24, 24))
                    github_btn.setText(f" {tr('settings.github_repo')}")
                    self.logger.info(f"设置页面GitHub图标设置成功: {github_icon_path}")
                else:
                    self.logger.warning(f"设置页面GitHub图标文件无效: {github_icon_path}")
                    self.set_fallback_github_icon_for_settings(github_btn)
            except Exception as e:
                self.logger.error(f"设置页面GitHub图标设置失败: {e}")
                self.set_fallback_github_icon_for_settings(github_btn)
        else:
            self.logger.warning(f"设置页面GitHub图标文件不存在: {github_icon_path}")
            self.set_fallback_github_icon_for_settings(github_btn)
        
        # 设置按钮样式
        github_btn.setStyleSheet("""
            QPushButton {
                background-color: #24292e;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 14px;
                font-weight: 500;
                text-align: center;
            }
            QPushButton:hover {
                background-color: #2f363d;
            }
            QPushButton:pressed {
                background-color: #1f2328;
            }
        """)
        
        # 连接点击事件到GitHub仓库
        github_btn.clicked.connect(self.open_github_repo)
        return github_btn
    
    def set_fallback_github_icon_for_settings(self, github_btn):
        """为设置页面设置备用的GitHub图标"""
        github_btn.setText(f"🐙 {tr('settings.github_repo')}")  # 使用章鱼emoji作为GitHub图标
        github_btn.setStyleSheet("""
            QPushButton {
                background-color: #24292e;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 14px;
                font-weight: 500;
                text-align: left;
            }
            QPushButton:hover {
                background-color: #2f363d;
            }
            QPushButton:pressed {
                background-color: #1f2328;
            }
        """)
    
    def open_github_repo(self):
        """打开GitHub仓库链接"""
        # 默认的GitHub仓库地址，可以在配置文件中自定义
        github_url = self.config.get('github_repo', 'https://github.com/tengze233/ETS2_DLC_Tools')
        QDesktopServices.openUrl(QUrl(github_url))
        self.logger.info(f"打开GitHub仓库: {github_url}")
    
    def open_logs_folder(self):
        """打开日志文件夹"""
        try:
            logs_path = Path(__file__).parent.parent / "logs"
            if logs_path.exists():
                # 使用系统默认文件管理器打开文件夹
                QDesktopServices.openUrl(QUrl.fromLocalFile(str(logs_path)))
                self.logger.info(f"打开日志文件夹: {logs_path}")
            else:
                # 如果logs文件夹不存在，创建它
                logs_path.mkdir(exist_ok=True)
                QDesktopServices.openUrl(QUrl.fromLocalFile(str(logs_path)))
                self.logger.info(f"创建并打开日志文件夹: {logs_path}")
        except Exception as e:
            self.logger.error(f"打开日志文件夹失败: {e}")
            QMessageBox.warning(self, "警告", f"无法打开日志文件夹: {e}")
    
    def create_installed_page(self):
        """创建已安装DLC页面"""
        page = QWidget()
        page.setObjectName("installed_page")
        layout = QVBoxLayout(page)
        
        # 页面标题
        header = QWidget()
        header.setObjectName("page_header")
        header_layout = QHBoxLayout(header)
        
        title = QLabel(tr('installed.title'))
        title.setObjectName("page_title")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # 刷新按钮
        refresh_btn = QPushButton(tr('common.refresh'))
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
        self.uninstall_selected_btn = QPushButton(tr('installed.uninstall_selected'))
        self.uninstall_selected_btn.clicked.connect(self.uninstall_selected_dlcs)
        self.uninstall_selected_btn.setVisible(False)
        actions_layout.addWidget(self.uninstall_selected_btn)
        
        # 卸载所有DLC按钮（初始隐藏）
        self.uninstall_all_btn = QPushButton(tr('installed.uninstall_all'))
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
        
        title = QLabel(tr('uninstalled.title'))
        title.setObjectName("page_title")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # 刷新按钮
        refresh_btn = QPushButton(tr('uninstalled.refresh_list'))
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
        
        install_btn = QPushButton(tr('uninstalled.install_selected'))
        install_btn.clicked.connect(self.install_selected_dlc)
        actions_layout.addWidget(install_btn)
        
        install_all_btn = QPushButton(tr('uninstalled.install_all'))
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
        title = QLabel(tr('settings.title'))
        title.setObjectName("page_title")
        layout.addWidget(title)
        
        # 设置分组
        settings_group = QWidget()
        settings_layout = QVBoxLayout(settings_group)
        
        # 欧洲卡车模拟2游戏路径
        game_path_layout = QHBoxLayout()
        game_path_label = QLabel(tr('settings.game_path'))
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
        
        game_browse_btn = QPushButton(tr('settings.browse'))
        game_browse_btn.clicked.connect(self.browse_game_path)
        game_path_layout.addWidget(game_browse_btn)
        
        settings_layout.addLayout(game_path_layout)
        
        # 主题设置已移除
        
        # 实用工具区域
        tools_group = QWidget()
        tools_layout = QVBoxLayout(tools_group)
        
        # 语言设置
        language_layout = QHBoxLayout()
        language_label = QLabel(tr('settings.language'))
        language_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: 600;
                color: #2c3e50;
                min-width: 80px;
                padding-right: 12px;
                background-color: transparent;
            }
        """)
        language_layout.addWidget(language_label)
        
        self.language_combo = QComboBox()
        self.language_combo.addItems(["中文", "English"])
        self.language_combo.setToolTip("切换界面语言")
        
        # 设置当前语言（从配置读取，默认为中文）
        current_lang = self.config.get('ui.language', 'zh_CN')
        if current_lang == 'en':
            self.language_combo.setCurrentIndex(1)  # English
        else:
            self.language_combo.setCurrentIndex(0)  # 中文
        
        self.language_combo.currentIndexChanged.connect(self.on_language_changed)
        self.language_combo.setStyleSheet("""
            QComboBox {
                border: 2px solid #e9ecef;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 14px;
                font-weight: 500;
                min-width: 140px;
                background-color: #ffffff;
                color: #495057;
                selection-background-color: #007bff;
            }
            QComboBox:hover {
                border-color: #007bff;
                background-color: #f8f9fa;
            }
            QComboBox:focus {
                border-color: #0056b3;
                outline: none;
            }
            QComboBox::drop-down {
                border: none;
                width: 30px;
                background-color: transparent;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 6px solid transparent;
                border-right: 6px solid transparent;
                border-top: 6px solid #6c757d;
                margin-right: 8px;
            }
            QComboBox::down-arrow:hover {
                border-top-color: #007bff;
            }
            QComboBox::down-arrow:pressed {
                border-top-color: #0056b3;
            }
            QComboBox QAbstractItemView {
                border: 2px solid #e9ecef;
                border-radius: 8px;
                background-color: #ffffff;
                selection-background-color: #007bff;
                selection-color: #ffffff;
                outline: none;
                margin-top: 2px;
                padding: 4px;
            }
            QComboBox QAbstractItemView::item {
                padding: 8px 12px;
                border-radius: 4px;
                margin: 2px 0;
            }
            QComboBox QAbstractItemView::item:hover {
                background-color: #f8f9fa;
                color: #495057;
            }
            QComboBox QAbstractItemView::item:selected {
                background-color: #007bff;
                color: #ffffff;
            }
        """)
        language_layout.addWidget(self.language_combo)
        language_layout.addStretch()
        tools_layout.addLayout(language_layout)
        
        # 添加分隔线
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("color: #e9ecef;")
        tools_layout.addWidget(separator)
        
        # 打开日志文件夹按钮
        open_logs_btn = QPushButton(tr('settings.open_logs'))
        open_logs_btn.setToolTip(tr('settings.open_logs'))
        open_logs_btn.clicked.connect(self.open_logs_folder)
        open_logs_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 14px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:pressed {
                background-color: #1e7e34;
            }
        """)
        tools_layout.addWidget(open_logs_btn)
        
        # 日志说明标签
        logs_info_label = QLabel(tr('settings.logs_info'))
        logs_info_label.setStyleSheet("""
            QLabel {
                color: #6c757d;
                font-size: 12px;
                padding: 5px;
            }
        """)
        tools_layout.addWidget(logs_info_label)
        
        # GitHub仓库链接按钮
        github_btn = self.create_github_button_for_settings()
        tools_layout.addWidget(github_btn)
        
        layout.addWidget(settings_group)
        layout.addWidget(tools_group)
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
    
    def on_language_changed(self, index):
        """语言切换事件处理"""
        # 根据索引确定语言代码
        if index == 0:  # 中文
            language_code = 'zh_CN'
            language_name = '中文'
        else:  # English
            language_code = 'en'
            language_name = 'English'
        
        # 加载新语言
        if self.language_manager.load_language(language_code):
            self.logger.info(f"语言切换为: {language_name} ({language_code})")
            
            # 保存语言设置到配置（存储在ui.language中）
            if self.config:
                self.config.set('ui.language', language_code)
                self.config.save_config()
            
            # 更新界面文本
            self.update_ui_texts()
        else:
            self.logger.error(f"语言加载失败: {language_code}")
            # 恢复之前的语言选择
            current_lang = self.config.get('ui.language', 'zh_CN')
            if current_lang == 'en':
                self.language_combo.setCurrentIndex(1)
            else:
                self.language_combo.setCurrentIndex(0)
    

    def update_ui_texts(self):
        """更新界面文本 - 根据当前语言重新加载所有文本"""
        # 更新窗口标题
        self.setWindowTitle(tr('app_title'))
        
        # 更新导航按钮文本
        self.installed_btn.setText(f"✓ {tr('nav.installed_dlc')}")
        self.uninstalled_btn.setText(f"✖ {tr('nav.uninstalled_dlc')}")
        self.settings_btn.setText(f"⚙ {tr('nav.settings')}")
        
        # 更新已安装页面文本
        if hasattr(self, 'installed_page'):
            # 查找已安装页面的标题标签
            title_label = self.installed_page.findChild(QLabel, "page_title")
            if title_label:
                title_label.setText(tr('installed.title'))
            
            # 更新刷新按钮
            refresh_btn = self.installed_page.findChild(QPushButton, "refresh_btn")
            if refresh_btn:
                refresh_btn.setText(tr('common.refresh'))
            
            # 更新卸载按钮
            if self.uninstall_selected_btn:
                self.uninstall_selected_btn.setText(tr('installed.uninstall_selected'))
            if self.uninstall_all_btn:
                self.uninstall_all_btn.setText(tr('installed.uninstall_all'))
        
        # 更新未安装页面文本
        if hasattr(self, 'uninstalled_page'):
            # 查找未安装页面的标题标签
            title_label = self.uninstalled_page.findChild(QLabel, "page_title")
            if title_label:
                title_label.setText(tr('uninstalled.title'))
            
            # 更新刷新按钮
            refresh_btn = self.uninstalled_page.findChild(QPushButton, "refresh_btn")
            if refresh_btn:
                refresh_btn.setText(tr('uninstalled.refresh_list'))
            
            # 更新操作按钮
            action_buttons = self.uninstalled_page.findChildren(QPushButton)
            for btn in action_buttons:
                if btn.text() == "安装选中DLC" or btn.text() == tr('uninstalled.install_selected'):
                    btn.setText(tr('uninstalled.install_selected'))
                elif btn.text() == "安装所有DLC" or btn.text() == tr('uninstalled.install_all'):
                    btn.setText(tr('uninstalled.install_all'))
        
        # 更新设置页面文本
        if hasattr(self, 'settings_page'):
            # 查找设置页面的标题标签
            title_label = self.settings_page.findChild(QLabel, "page_title")
            if title_label:
                title_label.setText(tr('settings.title'))
            
            # 更新游戏路径标签
            game_path_labels = self.settings_page.findChildren(QLabel)
            for label in game_path_labels:
                if label.text() == "游戏路径:" or label.text() == tr('settings.game_path'):
                    label.setText(tr('settings.game_path'))
                    break
            
            # 更新浏览按钮
            browse_btns = self.settings_page.findChildren(QPushButton)
            for btn in browse_btns:
                if btn.text() == "浏览..." or btn.text() == tr('settings.browse'):
                    btn.setText(tr('settings.browse'))
                    break
            
            # 更新语言标签
            for label in game_path_labels:
                if label.text() == "界面语言:" or label.text() == tr('settings.language'):
                    label.setText(tr('settings.language'))
                    break
            
            # 更新日志按钮
            for btn in browse_btns:
                if btn.text() == "📁 打开日志文件夹" or btn.text() == tr('settings.open_logs'):
                    btn.setText(tr('settings.open_logs'))
                    btn.setToolTip(tr('settings.open_logs'))
                    break
            
            # 更新日志说明标签
            for label in game_path_labels:
                if hasattr(label, 'logs_info') or (label.text() and "日志文件位于" in label.text()):
                    label.setText(tr('settings.logs_info'))
                    break
            
            # 更新GitHub按钮
            for btn in browse_btns:
                if btn.text() and ("访问GitHub仓库" in btn.text() or "GitHub" in btn.text()):
                    if btn.text().startswith("🐙"):
                        btn.setText(f"🐙 {tr('settings.github_repo')}")
                    else:
                        btn.setText(f" {tr('settings.github_repo')}")
                    btn.setToolTip(tr('settings.github_repo'))
                    break
        
        self.logger.info("界面文本已更新为当前语言")
    
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
                self.installed_page.content_area.setPlainText(tr('settings.game_path_not_found'))
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
                item = QListWidgetItem(tr('uninstalled.no_files'))
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEnabled)  # 禁用该项
                self.installed_page.dlc_list.addItem(item)
                self.uninstall_selected_btn.setVisible(False)
                self.uninstall_all_btn.setVisible(False)
                self.logger.info(f"在 {game_path} 中未找到DLC文件")
                
        except Exception as e:
            self.installed_page.dlc_list.clear()
            error_item = QListWidgetItem(f"{tr('common.error')}: {str(e)}")
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
                QMessageBox.warning(self, tr('common.warning'), tr('settings.game_path_not_found'))
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
                QMessageBox.information(self, tr('common.info'), tr('uninstalled.no_files'))
                return
            
            # 确认对话框
            reply = QMessageBox.question(
                self, tr('common.confirm'), 
                tr('installed.confirm_uninstall_all').format(len(dlc_files), temp_dir),
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
                        self, tr('common.success'), 
                        tr('installed.uninstall_success').format(len(moved_files))
                    )
                    # 重新检查并更新显示
                    self.check_and_display_dlcs()
                else:
                    QMessageBox.warning(self, tr('common.warning'), tr('installed.no_files_moved'))
                    
        except Exception as e:
            QMessageBox.critical(self, tr('common.error'), f"{tr('installed.uninstall_error')}: {str(e)}")
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
                QMessageBox.warning(self, tr('common.warning'), tr('settings.game_path_not_found'))
                return
            
            # 获取选中的DLC文件
            selected_items = self.installed_page.dlc_list.selectedItems()
            if not selected_items:
                QMessageBox.information(self, tr('common.info'), tr('installed.select_dlc_first'))
                return
            
            # 提取选中的文件名
            selected_files = []
            for item in selected_items:
                file_name = item.data(Qt.ItemDataRole.UserRole)
                if file_name:
                    selected_files.append(file_name)
            
            if not selected_files:
                QMessageBox.information(self, tr('common.info'), tr('installed.no_valid_dlc'))
                return
            
            # 创建temp_dlcs文件夹
            temp_dir = os.path.join(game_path, "temp_dlcs")
            if not os.path.exists(temp_dir):
                os.makedirs(temp_dir)
                self.logger.info(f"创建temp_dlcs文件夹: {temp_dir}")
            
            # 确认对话框
            reply = QMessageBox.question(
                self, tr('common.confirm'), 
                tr('installed.confirm_uninstall_selected').format(len(selected_files), temp_dir),
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
                        self, tr('common.success'), 
                        tr('installed.uninstall_success').format(len(moved_files))
                    )
                    # 重新检查并更新显示
                    self.check_and_display_dlcs()
                    # 同时刷新未安装DLC列表
                    self.refresh_uninstalled_dlc()
                else:
                    QMessageBox.warning(self, tr('common.warning'), tr('installed.no_files_moved_detail'))
                    
        except Exception as e:
            QMessageBox.critical(self, tr('common.error'), f"{tr('installed.uninstall_error')}: {str(e)}")
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
                item = QListWidgetItem(tr('uninstalled.no_files'))
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
                QMessageBox.warning(self, tr('common.warning'), tr('uninstalled.game_path_not_found'))
                return
            
            # 检查temp_dlcs文件夹
            temp_dir = os.path.join(game_path, "temp_dlcs")
            if not os.path.exists(temp_dir):
                QMessageBox.information(self, tr('common.info'), tr('uninstalled.temp_dlcs_not_found'))
                return
            
            # 获取选中的DLC文件
            selected_items = self.uninstalled_page.dlc_list.selectedItems()
            if not selected_items:
                QMessageBox.information(self, tr('common.info'), tr('uninstalled.select_dlc_first'))
                return
            
            # 提取选中的文件名
            selected_files = []
            for item in selected_items:
                file_name = item.data(Qt.ItemDataRole.UserRole)
                if file_name:
                    selected_files.append(file_name)
            
            if not selected_files:
                QMessageBox.information(self, tr('common.info'), tr('uninstalled.no_valid_dlc'))
                return
            
            # 确认对话框
            reply = QMessageBox.question(
                self, tr('common.confirm'), 
                tr('uninstalled.confirm_install_selected').format(len(selected_files), temp_dir),
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
                        self, tr('common.success'), 
                        tr('uninstalled.install_success').format(len(moved_files))
                    )
                    # 重新检查并更新显示
                    self.refresh_uninstalled_dlc()
                    # 同时刷新已安装DLC列表
                    self.check_and_display_dlcs()
                else:
                    QMessageBox.warning(self, tr('common.warning'), tr('uninstalled.no_files_moved_detail'))
                    
        except Exception as e:
            QMessageBox.critical(self, tr('common.error'), f"{tr('uninstalled.install_error')}: {str(e)}")
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
                QMessageBox.warning(self, tr('common.warning'), tr('uninstalled.game_path_not_found'))
                return
            
            # 检查temp_dlcs文件夹
            temp_dir = os.path.join(game_path, "temp_dlcs")
            if not os.path.exists(temp_dir):
                QMessageBox.information(self, tr('common.info'), tr('uninstalled.temp_dlcs_not_found'))
                return
            
            # 查找temp_dlcs文件夹中的所有DLC文件
            dlc_files = []
            for file in os.listdir(temp_dir):
                if file.lower().startswith("dlc") and file.lower().endswith(".scs"):
                    dlc_files.append(file)
            
            if not dlc_files:
                QMessageBox.information(self, tr('common.info'), tr('uninstalled.no_files'))
                return
            
            # 确认对话框
            reply = QMessageBox.question(
                self, tr('common.confirm'), 
                tr('uninstalled.confirm_install_all').format(len(dlc_files), temp_dir),
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
                        self, tr('common.success'), 
                        tr('uninstalled.install_success').format(len(moved_files))
                    )
                    # 重新检查并更新显示
                    self.refresh_uninstalled_dlc()
                    # 同时刷新已安装DLC列表
                    self.check_and_display_dlcs()
                else:
                    QMessageBox.warning(self, tr('common.warning'), tr('uninstalled.no_files_moved_detail'))
                    
        except Exception as e:
            QMessageBox.critical(self, tr('common.error'), tr('uninstalled.install_error').format(str(e)))
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