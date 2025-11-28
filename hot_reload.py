#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
热加载模块 - 使用watchdog监控文件变化并自动重启应用
"""

import sys
import os
import time
import subprocess
import logging
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


class CodeChangeHandler(FileSystemEventHandler):
    """文件变化处理器"""
    
    def __init__(self, restart_callback, extensions=None, ignore_dirs=None):
        """
        初始化处理器
        
        Args:
            restart_callback: 重启应用的回调函数
            extensions: 监控的文件扩展名列表，默认为 ['.py', '.json', '.ui']
            ignore_dirs: 忽略的目录列表，默认为 ['__pycache__', '.git', 'logs', 'Output']
        """
        super().__init__()
        self.restart_callback = restart_callback
        self.extensions = extensions or ['.py', '.json', '.ui']
        self.ignore_dirs = ignore_dirs or ['__pycache__', '.git', 'logs', 'Output', '.idea', 'venv', 'env']
        self.last_modified = {}  # 改为字典，记录每个文件的最后修改时间
        self.debounce_seconds = 0.5  # 减少防抖时间到0.5秒
        self.pending_restart = False  # 是否有待处理的重启
        
    def should_ignore(self, path):
        """检查是否应该忽略该路径"""
        path_obj = Path(path)
        
        # 检查是否在忽略目录中
        for ignore_dir in self.ignore_dirs:
            if ignore_dir in path_obj.parts:
                return True
        
        # 检查文件扩展名
        if path_obj.suffix not in self.extensions:
            return True
            
        return False
    
    def on_modified(self, event):
        """文件修改事件处理"""
        if event.is_directory:
            return
            
        file_path = event.src_path
        
        # 忽略不需要监控的文件
        if self.should_ignore(file_path):
            return
        
        # 防抖处理：对每个文件单独计时
        current_time = time.time()
        last_time = self.last_modified.get(file_path, 0)
        
        if current_time - last_time < self.debounce_seconds:
            # 同一文件在防抖期间的重复变化被忽略
            return
        
        self.last_modified[file_path] = current_time
        
        # 记录变化并触发重启
        logger.info(f"检测到文件变化: {Path(file_path).name}")
        self.restart_callback()
    
    def on_created(self, event):
        """文件创建事件处理"""
        if event.is_directory:
            return
        
        file_path = event.src_path
        
        if self.should_ignore(file_path):
            return
        
        logger.info(f"检测到新文件: {Path(file_path).name}")
        self.restart_callback()
    
    def on_deleted(self, event):
        """文件删除事件处理"""
        if event.is_directory:
            return
        
        file_path = event.src_path
        
        if self.should_ignore(file_path):
            return
        
        logger.info(f"检测到文件删除: {Path(file_path).name}")
        self.restart_callback()


class HotReloader:
    """热加载管理器"""
    
    def __init__(self, script_path, watch_dirs=None, extensions=None, ignore_dirs=None):
        """
        初始化热加载管理器
        
        Args:
            script_path: 要启动的主脚本路径 (如 main.py)
            watch_dirs: 要监控的目录列表，默认为当前目录
            extensions: 监控的文件扩展名列表
            ignore_dirs: 忽略的目录列表
        """
        self.script_path = script_path
        self.watch_dirs = watch_dirs or ['.']
        self.process = None
        self.observer = None
        self.should_restart = False
        
        # 创建文件变化处理器
        self.handler = CodeChangeHandler(
            restart_callback=self.trigger_restart,
            extensions=extensions,
            ignore_dirs=ignore_dirs
        )
    
    def trigger_restart(self):
        """触发重启标志"""
        if not self.should_restart:
            self.should_restart = True
            logger.info("已设置重启标志，将在下一个检查周期重启...")
    
    def start_app(self):
        """启动应用程序"""
        if self.process:
            self.stop_app()
        
        logger.info("=" * 60)
        logger.info("启动应用程序...")
        logger.info("=" * 60)
        
        # 使用当前Python解释器启动应用
        # 不捕获输出，让它直接打印到控制台，避免阻塞
        self.process = subprocess.Popen(
            [sys.executable, self.script_path]
        )
        
        self.should_restart = False
    
    def stop_app(self):
        """停止应用程序"""
        if self.process:
            logger.info("停止应用程序...")
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                logger.warning("应用程序未响应，强制终止...")
                self.process.kill()
                self.process.wait()
            
            self.process = None
    
    def start_watching(self):
        """开始监控文件变化"""
        logger.info("=" * 60)
        logger.info("热加载已启动 - 监控文件变化中...")
        logger.info(f"监控目录: {', '.join(self.watch_dirs)}")
        logger.info(f"监控扩展名: {', '.join(self.handler.extensions)}")
        logger.info("提示: 修改代码后将自动重启应用")
        logger.info("按 Ctrl+C 停止热加载")
        logger.info("=" * 60)
        
        # 创建观察者并开始监控
        self.observer = Observer()
        for watch_dir in self.watch_dirs:
            abs_path = os.path.abspath(watch_dir)
            if os.path.exists(abs_path):
                self.observer.schedule(self.handler, abs_path, recursive=True)
                logger.info(f"正在监控: {abs_path}")
        
        self.observer.start()
        
        # 首次启动应用
        self.start_app()
        
        try:
            while True:
                # 优先检查是否需要重启
                if self.should_restart:
                    if self.process:
                        logger.info("\n" + "=" * 60)
                        logger.info("重启应用程序...")
                        logger.info("=" * 60)
                        self.stop_app()
                        time.sleep(0.5)  # 等待进程完全停止
                        self.start_app()
                    else:
                        # 如果进程不存在，直接启动
                        self.start_app()
                    continue
                
                # 检查进程状态
                if self.process:
                    retcode = self.process.poll()
                    if retcode is not None:
                        if retcode != 0:
                            logger.error(f"应用程序异常退出，退出码: {retcode}")
                        else:
                            logger.info("应用程序正常退出")
                        # 应用退出后重新启动
                        time.sleep(1)
                        self.start_app()
                
                time.sleep(0.1)
                
        except KeyboardInterrupt:
            logger.info("\n检测到 Ctrl+C，正在停止...")
        finally:
            self.stop()
    
    def stop(self):
        """停止热加载"""
        logger.info("停止文件监控...")
        if self.observer:
            self.observer.stop()
            self.observer.join()
        
        self.stop_app()
        logger.info("热加载已停止")


def main():
    """主函数 - 用于测试热加载功能"""
    import argparse
    
    parser = argparse.ArgumentParser(description='热加载工具 - 监控文件变化并自动重启应用')
    parser.add_argument('script', help='要运行的主脚本路径 (如 main.py)')
    parser.add_argument('--watch', nargs='+', default=['.'], help='要监控的目录列表')
    parser.add_argument('--ext', nargs='+', default=['.py', '.json', '.ui'], help='要监控的文件扩展名')
    parser.add_argument('--ignore', nargs='+', default=['__pycache__', '.git', 'logs', 'Output', '.idea'], 
                        help='要忽略的目录')
    
    args = parser.parse_args()
    
    # 检查脚本是否存在
    if not os.path.exists(args.script):
        logger.error(f"错误: 脚本文件不存在: {args.script}")
        sys.exit(1)
    
    # 创建热加载器并启动
    reloader = HotReloader(
        script_path=args.script,
        watch_dirs=args.watch,
        extensions=args.ext,
        ignore_dirs=args.ignore
    )
    
    reloader.start_watching()


if __name__ == '__main__':
    main()