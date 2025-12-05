#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Eagle 图片搜索专用脚本
专门用于搜索 Eagle 库中的图片
"""

import requests
from config import EAGLE_API_URL, EAGLE_TOKEN

def search_eagle_images(keyword):
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

            print(f"🔍 搜索关键词: '{keyword}'")
            print("=" * 50)

            if items and len(items) > 0:
                print(f"✅ 成功找到 {len(items)} 张图片！")
                print()

                for i, item in enumerate(items, 1):
                    name = item.get('name', '未知名称')
                    file_path = item.get('filePath', '未知路径')
                    print(f"📸 图片 {i}:")
                    print(f"   名称: {name}")
                    print(f"   文件路径: {file_path}")
                    print()

                return len(items)
            else:
                print(f"❌ 未找到包含关键词 '{keyword}' 的图片")
                return 0
        else:
            print(f"❌ 搜索失败: HTTP {response.status_code}")
            print(f"响应内容: {response.text}")
            return -1

    except requests.exceptions.RequestException as e:
        print(f"❌ 网络连接错误: {e}")
        return -1
    except Exception as e:
        print(f"❌ 搜索错误: {e}")
        return -1

if __name__ == "__main__":
    print("🚀 Eagle 图片搜索工具")
    print("=" * 50)

    # 搜索关键词 "relace"
    result = search_eagle_images("relace")

    print("=" * 50)
    if result > 0:
        print(f"🎯 搜索完成！找到 {result} 张图片")
    elif result == 0:
        print("🎯 搜索完成！未找到相关图片")
    else:
        print("🎯 搜索失败！请检查 Eagle API 配置")
