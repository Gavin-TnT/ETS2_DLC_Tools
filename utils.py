# -*- coding: utf-8 -*-
"""
工具模块 - utils
提供各种实用工具函数
"""

import os
import sys
import logging
import logging.handlers
import hashlib
import json
from pathlib import Path
from datetime import datetime
import colorlog


def setup_logging(level="INFO", log_file=None, max_size=10485760, backup_count=5):
    """
    设置日志系统
    
    Args:
        level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: 日志文件路径
        max_size: 日志文件最大大小 (字节)
        backup_count: 备份文件数量
    """
    # 创建日志目录
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 配置日志格式
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    color_format = '%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # 创建logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, level.upper()))
    
    # 清除现有的handler
    logger.handlers.clear()
    
    # 控制台handler（带颜色）
    console_handler = colorlog.StreamHandler()
    console_handler.setFormatter(colorlog.ColoredFormatter(
        color_format,
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'red,bg_white',
        }
    ))
    logger.addHandler(console_handler)
    
    # 文件handler（旋转日志）
    if log_file:
        file_handler = logging.handlers.RotatingFileHandler(
            log_file, maxBytes=max_size, backupCount=backup_count, encoding='utf-8'
        )
        file_handler.setFormatter(logging.Formatter(log_format))
        logger.addHandler(file_handler)
    
    return logger


def get_file_hash(file_path, algorithm="md5"):
    """
    计算文件哈希值
    
    Args:
        file_path: 文件路径
        algorithm: 哈希算法 (md5, sha1, sha256)
    
    Returns:
        哈希值字符串
    """
    try:
        hash_obj = getattr(hashlib, algorithm)()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_obj.update(chunk)
        return hash_obj.hexdigest()
    except Exception as e:
        logging.error(f"计算文件哈希失败 {file_path}: {e}")
        return None


def copy_file_with_progress(src, dst, callback=None):
    """
    复制文件并显示进度
    
    Args:
        src: 源文件路径
        dst: 目标文件路径
        callback: 进度回调函数 (current, total)
    """
    try:
        src_path = Path(src)
        dst_path = Path(dst)
        
        # 确保目标目录存在
        dst_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 获取文件大小
        file_size = src_path.stat().st_size
        copied_size = 0
        
        # 复制文件
        with open(src_path, 'rb') as src_file:
            with open(dst_path, 'wb') as dst_file:
                while True:
                    chunk = src_file.read(8192)
                    if not chunk:
                        break
                    dst_file.write(chunk)
                    copied_size += len(chunk)
                    
                    # 调用进度回调
                    if callback:
                        callback(copied_size, file_size)
        
        return True
    except Exception as e:
        logging.error(f"文件复制失败 {src} -> {dst}: {e}")
        return False


def ensure_directory(path):
    """
    确保目录存在
    
    Args:
        path: 目录路径
    
    Returns:
        目录路径对象
    """
    path_obj = Path(path)
    path_obj.mkdir(parents=True, exist_ok=True)
    return path_obj


def get_directory_size(path):
    """
    获取目录大小
    
    Args:
        path: 目录路径
    
    Returns:
        目录大小（字节）
    """
    total_size = 0
    path_obj = Path(path)
    
    try:
        for file_path in path_obj.rglob('*'):
            if file_path.is_file():
                total_size += file_path.stat().st_size
    except Exception as e:
        logging.error(f"计算目录大小失败 {path}: {e}")
    
    return total_size


def format_file_size(size_bytes):
    """
    格式化文件大小
    
    Args:
        size_bytes: 文件大小（字节）
    
    Returns:
        格式化后的字符串
    """
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    size = float(size_bytes)
    
    while size >= 1024.0 and i < len(size_names) - 1:
        size /= 1024.0
        i += 1
    
    return f"{size:.1f} {size_names[i]}"


def get_file_info(file_path):
    """
    获取文件详细信息
    
    Args:
        file_path: 文件路径
    
    Returns:
        文件信息字典
    """
    try:
        path_obj = Path(file_path)
        stat = path_obj.stat()
        
        return {
            'name': path_obj.name,
            'path': str(path_obj.absolute()),
            'size': stat.st_size,
            'size_formatted': format_file_size(stat.st_size),
            'modified': datetime.fromtimestamp(stat.st_mtime),
            'created': datetime.fromtimestamp(stat.st_ctime),
            'is_file': path_obj.is_file(),
            'is_dir': path_obj.is_dir(),
            'extension': path_obj.suffix.lower(),
            'md5': get_file_hash(file_path, 'md5') if path_obj.is_file() else None
        }
    except Exception as e:
        logging.error(f"获取文件信息失败 {file_path}: {e}")
        return None


def find_files(directory, pattern="*", recursive=True):
    """
    查找文件
    
    Args:
        directory: 搜索目录
        pattern: 文件模式
        recursive: 是否递归搜索
    
    Returns:
        文件路径列表
    """
    try:
        path_obj = Path(directory)
        if recursive:
            return list(path_obj.rglob(pattern))
        else:
            return list(path_obj.glob(pattern))
    except Exception as e:
        logging.error(f"查找文件失败 {directory}: {e}")
        return []


def safe_delete(path):
    """
    安全删除文件或目录
    
    Args:
        path: 要删除的路径
    
    Returns:
        是否成功删除
    """
    try:
        path_obj = Path(path)
        if path_obj.is_file():
            path_obj.unlink()
        elif path_obj.is_dir():
            import shutil
            shutil.rmtree(path_obj)
        return True
    except Exception as e:
        logging.error(f"删除失败 {path}: {e}")
        return False


def backup_file(src, backup_dir="backups", suffix=None):
    """
    备份文件
    
    Args:
        src: 源文件路径
        backup_dir: 备份目录
        suffix: 备份文件后缀
    
    Returns:
        备份文件路径或None
    """
    try:
        src_path = Path(src)
        if not src_path.exists():
            logging.error(f"源文件不存在: {src}")
            return None
        
        # 创建备份目录
        backup_path = ensure_directory(backup_dir)
        
        # 生成备份文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if suffix:
            backup_name = f"{src_path.stem}_{timestamp}_{suffix}{src_path.suffix}"
        else:
            backup_name = f"{src_path.stem}_{timestamp}_backup{src_path.suffix}"
        
        backup_file_path = backup_path / backup_name
        
        # 复制文件
        import shutil
        if src_path.is_file():
            shutil.copy2(src_path, backup_file_path)
        else:
            shutil.copytree(src_path, backup_file_path)
        
        logging.info(f"文件已备份: {src} -> {backup_file_path}")
        return backup_file_path
    
    except Exception as e:
        logging.error(f"备份文件失败 {src}: {e}")
        return None


def load_json_file(file_path, default=None):
    """
    安全加载JSON文件
    
    Args:
        file_path: JSON文件路径
        default: 默认值
    
    Returns:
        JSON数据或默认值
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"加载JSON文件失败 {file_path}: {e}")
        return default or {}


def save_json_file(data, file_path, indent=4):
    """
    安全保存JSON文件
    
    Args:
        data: 要保存的数据
        file_path: 文件路径
        indent: 缩进空格数
    
    Returns:
        是否成功保存
    """
    try:
        # 确保目录存在
        ensure_directory(Path(file_path).parent)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=indent, ensure_ascii=False)
        
        return True
    except Exception as e:
        logging.error(f"保存JSON文件失败 {file_path}: {e}")
        return False


def is_valid_game_directory(path):
    """
    检查是否为有效的游戏目录
    
    Args:
        path: 游戏目录路径
    
    Returns:
        是否有效
    """
    try:
        path_obj = Path(path)
        if not path_obj.is_dir():
            return False
        
        # 检查是否存在游戏关键文件
        required_files = ["eurotrucks2.exe", "game.log.txt"]
        return any((path_obj / file).exists() for file in required_files)
    except Exception:
        return False


def get_ets2_default_paths():
    """
    获取ETS2默认路径
    
    Returns:
        默认路径字典
    """
    paths = {}
    
    # 文档目录
    if os.name == 'nt':  # Windows
        documents = Path.home() / "Documents"
        paths['documents'] = documents
        paths['ets2_config'] = documents / "Euro Truck Simulator 2"
        paths['ets2_mods'] = documents / "Euro Truck Simulator 2" / "mod"
        
        # Steam默认安装路径
        steam_paths = [
            Path("C:/Program Files (x86)/Steam/steamapps/common/Euro Truck Simulator 2"),
            Path("C:/Program Files/Steam/steamapps/common/Euro Truck Simulator 2"),
            Path.home() / "Steam" / "steamapps" / "common" / "Euro Truck Simulator 2"
        ]
        
        for steam_path in steam_paths:
            if steam_path.exists():
                paths['ets2_install'] = steam_path
                break
    
    elif os.name == 'posix':  # Linux/Mac
        paths['documents'] = Path.home() / "Documents"
        paths['ets2_config'] = Path.home() / ".local" / "share" / "Euro Truck Simulator 2"
        paths['ets2_mods'] = Path.home() / ".local" / "share" / "Euro Truck Simulator 2" / "mod"
        
        # Steam默认安装路径 (Linux)
        steam_path = Path.home() / ".local" / "share" / "Steam" / "steamapps" / "common" / "Euro Truck Simulator 2"
        if steam_path.exists():
            paths['ets2_install'] = steam_path
    
    return paths


def create_progress_callback(progress_bar=None, status_label=None):
    """
    创建进度回调函数
    
    Args:
        progress_bar: 进度条控件
        status_label: 状态标签控件
    
    Returns:
        进度回调函数
    """
    def callback(current, total):
        if total > 0:
            percentage = (current / total) * 100
            
            if progress_bar:
                progress_bar.setValue(int(percentage))
            
            if status_label:
                status_label.setText(f"进度: {percentage:.1f}% ({format_file_size(current)} / {format_file_size(total)})")
            
            # 处理Qt事件
            try:
                from PyQt6.QtWidgets import QApplication
                QApplication.processEvents()
            except ImportError:
                pass
    
    return callback