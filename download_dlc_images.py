#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DLC图片下载脚本
从dlcs_info.json中读取所有DLC的header_image链接，下载到本地resources/dlc_images目录
"""

import os
import sys
import json
import requests
from pathlib import Path
from urllib.parse import urlparse

def download_image(url, save_path, dlc_name):
    """
    下载单个图片
    
    Args:
        url: 图片URL
        save_path: 保存路径
        dlc_name: DLC名称（用于日志）
    
    Returns:
        bool: 是否下载成功
    """
    try:
        print(f"正在下载: {dlc_name}")
        print(f"  URL: {url}")
        
        # 发送HTTP GET请求
        response = requests.get(url, timeout=30, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        response.raise_for_status()
        
        # 保存图片
        with open(save_path, 'wb') as f:
            f.write(response.content)
        
        print(f"  ✓ 下载成功: {save_path}")
        return True
        
    except Exception as e:
        print(f"  ✗ 下载失败: {e}")
        return False

def main():
    """主函数"""
    print("=" * 60)
    print("DLC图片下载工具")
    print("=" * 60)
    
    # 确定项目根目录
    if getattr(sys, 'frozen', False):
        base_path = Path(sys.executable).parent
    else:
        base_path = Path(__file__).parent
    
    # 读取dlcs_info.json
    dlcs_info_path = base_path / "dlcs_info.json"
    if not dlcs_info_path.exists():
        print(f"错误: 找不到 {dlcs_info_path}")
        return False
    
    print(f"\n读取DLC信息: {dlcs_info_path}")
    try:
        with open(dlcs_info_path, 'r', encoding='utf-8') as f:
            dlcs_info = json.load(f)
    except Exception as e:
        print(f"错误: 读取DLC信息失败: {e}")
        return False
    
    print(f"找到 {len(dlcs_info)} 个DLC")
    
    # 创建图片保存目录
    images_dir = base_path / "resources" / "dlc_images"
    images_dir.mkdir(parents=True, exist_ok=True)
    print(f"\n图片保存目录: {images_dir}")
    
    # 下载所有图片
    print("\n开始下载图片...")
    print("-" * 60)
    
    success_count = 0
    failed_count = 0
    skipped_count = 0
    
    for i, dlc in enumerate(dlcs_info, 1):
        dlc_name = dlc.get('name', 'Unknown')
        dlc_id = dlc.get('dlc_id', 0)
        header_image = dlc.get('header_image', '')
        
        print(f"\n[{i}/{len(dlcs_info)}] {dlc_name} (ID: {dlc_id})")
        
        # 跳过没有图片链接的DLC
        if not header_image:
            print("  ⊘ 跳过: 没有图片链接")
            skipped_count += 1
            continue
        
        # 生成文件名: dlc_id.jpg
        filename = f"{dlc_id}.jpg"
        save_path = images_dir / filename
        
        # 如果文件已存在，跳过下载
        if save_path.exists():
            print(f"  ⊘ 跳过: 文件已存在 ({save_path.name})")
            skipped_count += 1
            continue
        
        # 下载图片
        if download_image(header_image, save_path, dlc_name):
            success_count += 1
        else:
            failed_count += 1
    
    # 输出统计信息
    print("\n" + "=" * 60)
    print("下载完成!")
    print(f"成功: {success_count} 个")
    print(f"失败: {failed_count} 个")
    print(f"跳过: {skipped_count} 个")
    print(f"总计: {len(dlcs_info)} 个DLC")
    print("=" * 60)
    
    return failed_count == 0

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n用户中断下载")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)