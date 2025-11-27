# -*- coding: utf-8 -*-
"""
配置文件模块
管理应用程序的配置信息
"""

import json
import os
from pathlib import Path
import logging


class Config:
    """配置管理类"""
    
    def __init__(self, config_file=None):
        """初始化配置"""
        self.logger = logging.getLogger(__name__)
        
        # 默认配置
        self.default_config = {
            "app": {
                "name": "ETS2 DLC Tools",
                "version": "1.0.0",
                "debug": False
            },
            "window": {
                "width": 1200,
                "height": 800,
                "x": 100,
                "y": 100,
                "maximized": False
            },
            "logging": {
                "level": "INFO",
                "file": "logs/app.log",
                "max_size": 1048576,   # 1MB
                "backup_count": 5
            },
            "dlc": {
                "game_path": "",
                "mods_path": "",
                "backup_path": "backups",
                "auto_backup": True
            },
            "ui": {
                "theme": "light",
                "language": "zh_CN",
                "font_size": 12,
                "show_toolbar": True,
                "show_statusbar": True
            }
        }
        
        # 配置文件路径
        if config_file:
            self.config_file = Path(config_file)
        else:
            self.config_file = Path(__file__).parent / "config.json"
        
        # 加载配置
        self.config = self.load_config()
        
        self.logger.info(f"配置初始化完成，配置文件: {self.config_file}")
    
    def load_config(self):
        """加载配置文件"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    # 合并默认配置和加载的配置
                    config = self.merge_config(self.default_config.copy(), loaded_config)
                    self.logger.info("配置文件加载成功")
                    return config
            else:
                self.logger.info("配置文件不存在，使用默认配置")
                return self.default_config.copy()
        except Exception as e:
            self.logger.error(f"加载配置文件失败: {e}")
            return self.default_config.copy()
    
    def save_config(self):
        """保存配置到文件"""
        try:
            # 确保配置目录存在
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
            
            self.logger.info("配置文件保存成功")
            return True
        except Exception as e:
            self.logger.error(f"保存配置文件失败: {e}")
            return False
    
    def get(self, key_path, default=None):
        """获取配置值"""
        keys = key_path.split('.')
        value = self.config
        
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key_path, value):
        """设置配置值"""
        keys = key_path.split('.')
        config = self.config
        
        try:
            # 遍历到倒数第二个键
            for key in keys[:-1]:
                if key not in config:
                    config[key] = {}
                config = config[key]
            
            # 设置最后一个键的值
            config[keys[-1]] = value
            
            # 自动保存配置
            self.save_config()
            
            self.logger.info(f"配置已更新: {key_path} = {value}")
            return True
        except Exception as e:
            self.logger.error(f"设置配置失败: {e}")
            return False
    
    def merge_config(self, default, custom):
        """合并配置"""
        if not isinstance(default, dict) or not isinstance(custom, dict):
            return custom
        
        for key, value in custom.items():
            if key in default and isinstance(default[key], dict) and isinstance(value, dict):
                default[key] = self.merge_config(default[key], value)
            else:
                default[key] = value
        
        return default
    
    def reset_to_default(self):
        """重置为默认配置"""
        self.config = self.default_config.copy()
        self.save_config()
        self.logger.info("配置已重置为默认值")
    
    def get_game_path(self):
        """获取游戏路径"""
        return self.get('dlc.game_path', '')
    
    def set_game_path(self, path):
        """设置游戏路径"""
        return self.set('dlc.game_path', path)
    
    def get_mods_path(self):
        """获取MODS路径"""
        return self.get('dlc.mods_path', '')
    
    def set_mods_path(self, path):
        """设置MODS路径"""
        return self.set('dlc.mods_path', path)
    
    def get_backup_path(self):
        """获取备份路径"""
        return self.get('dlc.backup_path', 'backups')
    
    def set_backup_path(self, path):
        """设置备份路径"""
        return self.set('dlc.backup_path', path)
    
    def is_auto_backup_enabled(self):
        """检查是否启用自动备份"""
        return self.get('dlc.auto_backup', True)
    
    def set_auto_backup(self, enabled):
        """设置自动备份"""
        return self.set('dlc.auto_backup', enabled)
    
    def get_window_geometry(self):
        """获取窗口几何信息"""
        return {
            'x': self.get('window.x', 100),
            'y': self.get('window.y', 100),
            'width': self.get('window.width', 1200),
            'height': self.get('window.height', 800),
            'maximized': self.get('window.maximized', False)
        }
    
    def set_window_geometry(self, geometry):
        """设置窗口几何信息"""
        self.set('window.x', geometry.get('x', 100))
        self.set('window.y', geometry.get('y', 100))
        self.set('window.width', geometry.get('width', 1200))
        self.set('window.height', geometry.get('height', 800))
    
    def get_theme(self):
        """获取主题设置"""
        return self.get('ui.theme', 'light')
    
    def set_theme(self, theme):
        """设置主题"""
        return self.set('ui.theme', theme)
        self.set('window.maximized', geometry.get('maximized', False))
    
    def get_ui_theme(self):
        """获取UI主题"""
        return self.get('ui.theme', 'default')
    
    def set_ui_theme(self, theme):
        """设置UI主题"""
        return self.set('ui.theme', theme)
    
    def get_language(self):
        """获取语言设置"""
        return self.get('ui.language', 'zh_CN')
    
    def set_language(self, language):
        """设置语言"""
        return self.set('ui.language', language)
    
    def get_font_size(self):
        """获取字体大小"""
        return self.get('ui.font_size', 12)
    
    def set_font_size(self, size):
        """设置字体大小"""
        return self.set('ui.font_size', size)
    
    def is_toolbar_visible(self):
        """检查工具栏是否可见"""
        return self.get('ui.show_toolbar', True)
    
    def set_toolbar_visible(self, visible):
        """设置工具栏可见性"""
        return self.set('ui.show_toolbar', visible)
    
    def is_statusbar_visible(self):
        """检查状态栏是否可见"""
        return self.get('ui.show_statusbar', True)
    
    def set_statusbar_visible(self, visible):
        """设置状态栏可见性"""
        return self.set('ui.show_statusbar', visible)