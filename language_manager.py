# -*- coding: utf-8 -*-
"""
语言管理器 - Language Manager
负责加载和管理多语言翻译文件
"""

import json
import os
from pathlib import Path
import logging


class LanguageManager:
    """语言管理器类"""
    
    def __init__(self, language_dir=None):
        """
        初始化语言管理器
        
        Args:
            language_dir: 语言文件目录路径，默认为当前文件所在目录的language文件夹
        """
        self.logger = logging.getLogger(__name__)
        
        # 设置语言文件目录
        if language_dir is None:
            self.language_dir = Path(__file__).parent / "language"
        else:
            self.language_dir = Path(language_dir)
        
        # 当前语言代码
        self.current_language = 'zh_CN'
        
        # 当前语言的翻译数据
        self.translations = {}
        
        # 支持的语言列表
        self.supported_languages = {
            'zh_CN': '中文',
            'en': 'English'
        }
        
        # 加载默认语言
        self.load_language(self.current_language)
    
    def load_language(self, language_code):
        """
        加载指定语言的翻译文件
        
        Args:
            language_code: 语言代码，如 'zh_CN', 'en'
            
        Returns:
            bool: 加载是否成功
        """
        if language_code not in self.supported_languages:
            self.logger.warning(f"不支持的语言代码: {language_code}")
            return False
        
        # 构建语言文件路径
        language_file = self.language_dir / f"{language_code}.json"
        
        if not language_file.exists():
            self.logger.error(f"语言文件不存在: {language_file}")
            return False
        
        try:
            with open(language_file, 'r', encoding='utf-8') as f:
                self.translations = json.load(f)
            
            self.current_language = language_code
            self.logger.info(f"语言文件加载成功: {language_code}")
            return True
            
        except json.JSONDecodeError as e:
            self.logger.error(f"语言文件JSON格式错误: {e}")
            return False
        except Exception as e:
            self.logger.error(f"加载语言文件失败: {e}")
            return False
    
    def tr(self, key, default=None, **kwargs):
        """
        获取翻译文本
        
        Args:
            key: 翻译键，支持点分路径，如 'nav.settings'
            default: 默认值，如果翻译不存在则返回此值
            **kwargs: 格式化参数，用于替换文本中的占位符
            
        Returns:
            str: 翻译后的文本
        """
        if not key:
            return default or ""
        
        # 支持点分路径的键
        keys = key.split('.')
        value = self.translations
        
        try:
            for k in keys:
                value = value[k]
            
            # 如果找到的是字符串，进行格式化
            if isinstance(value, str):
                if kwargs:
                    return value.format(**kwargs)
                return value
            else:
                # 如果不是字符串，返回默认值
                return default or str(value)
                
        except (KeyError, TypeError):
            # 如果键不存在，返回默认值或原始键
            if default is not None:
                return default
            
            self.logger.warning(f"翻译键不存在: {key}")
            return key  # 返回原始键作为标识
    
    def get_current_language(self):
        """获取当前语言代码"""
        return self.current_language
    
    def get_current_language_name(self):
        """获取当前语言名称"""
        return self.supported_languages.get(self.current_language, 'Unknown')
    
    def get_supported_languages(self):
        """获取支持的语言列表"""
        return self.supported_languages.copy()
    
    def set_language(self, language_code):
        """
        设置当前语言
        
        Args:
            language_code: 语言代码
            
        Returns:
            bool: 设置是否成功
        """
        return self.load_language(language_code)


# 全局语言管理器实例
_language_manager = None


def get_language_manager():
    """获取全局语言管理器实例"""
    global _language_manager
    if _language_manager is None:
        _language_manager = LanguageManager()
    return _language_manager


def tr(key, default=None, **kwargs):
    """
    快捷翻译函数
    
    Args:
        key: 翻译键
        default: 默认值
        **kwargs: 格式化参数
        
    Returns:
        str: 翻译后的文本
    """
    return get_language_manager().tr(key, default, **kwargs)