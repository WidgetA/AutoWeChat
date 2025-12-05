#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Eagle API 测试脚本
用于测试与 Eagle 素材管理软件的连接和搜索功能
"""

import requests
import json
from config import EAGLE_API_URL, EAGLE_TOKEN

def test_eagle_connection():
    """测试 Eagle API 连接"""
    try:
        # 测试基本连接
        response = requests.get(f"{EAGLE_API_URL}/api/application/info",
                              headers={"Authorization": f"Bearer {EAGLE_TOKEN}"})

        if response.status_code == 200:
            print("✅ Eagle API 连接成功!")
            data = response.json()
            print(f"📱 Eagle 版本: {data.get('version', '未知')}")
            print(f"🏠 库路径: {data.get('library', {}).get('path', '未知')}")
            return True
        else:
            print(f"❌ Eagle API 连接失败: HTTP {response.status_code}")
            print(f"响应内容: {response.text}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"❌ 网络连接错误: {e}")
        return False
    except Exception as e:
        print(f"❌ 其他错误: {e}")
        return False

def test_eagle_library_info():
    """获取 Eagle 库信息"""
    try:
        response = requests.get(f"{EAGLE_API_URL}/api/library/info",
                              headers={"Authorization": f"Bearer {EAGLE_TOKEN}"})

        if response.status_code == 200:
            data = response.json()
            print("📚 库信息:")
            print(f"  - 文件夹数量: {data.get('foldersCount', 0)}")
            print(f"  - 图片数量: {data.get('imagesCount', 0)}")
            print(f"  - 智能文件夹数量: {data.get('smartFoldersCount', 0)}")
            print(f"  - 标签数量: {data.get('tagsCount', 0)}")
            return True
        else:
            print(f"❌ 获取库信息失败: HTTP {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ 获取库信息错误: {e}")
        return False

def search_eagle_images(keyword="relace"):
    """搜索 Eagle 中的图片"""
    try:
        # 调用 /api/item/list 接口搜索图片
        params = {"keyword": keyword}
        response = requests.get(f"{EAGLE_API_URL}/api/item/list",
                              headers={"Authorization": f"Bearer {EAGLE_TOKEN}"},
                              params=params)

        if response.status_code == 200:
            data = response.json()
            items = data.get('data', [])

            if items and len(items) > 0:
                print(f"✅ 成功找到图片！")
                for item in items:
                    name = item.get('name', '未知名称')
                    file_path = item.get('filePath', '未知路径')
                    print(f"📸 图片名称: {name}")
                    print(f"📁 完整文件路径: {file_path}")
                    print("-" * 50)
                return True
            else:
                print("❌ 未找到包含关键词 'relace' 的图片")
                return False
        else:
            print(f"❌ 搜索失败: HTTP {response.status_code}")
            print(f"响应内容: {response.text}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"❌ 网络连接错误: {e}")
        return False
    except Exception as e:
        print(f"❌ 搜索错误: {e}")
        return False

if __name__ == "__main__":
    print("🚀 开始测试 Eagle API 连接...")
    print("=" * 50)

    # 测试连接
    if test_eagle_connection():
        print("\n" + "=" * 50)
        # 获取库信息
        test_eagle_library_info()

        print("\n" + "=" * 50)
        # 搜索图片
        search_eagle_images("relace")

    print("\n" + "=" * 50)
    print("🎯 测试完成!")
