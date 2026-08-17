#!/usr/bin/env python3
"""
B站数据抓取脚本
用于GitHub Actions定时执行，抓取UP主数据并保存
- data.json: 最新数据
- history.json: 历史记录（每次抓取追加一条）
"""

import requests
import json
import os
from datetime import datetime

# 配置：修改这里为你的B站UID
CONFIG = {
    'mid': '41012204',  # 改成你自己的B站UID
}

# B站API
API_BASE = 'https://api.bilibili.com'

# 请求头
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Referer': 'https://www.bilibili.com',
}


def fetch_data():
    """抓取UP主数据"""
    mid = CONFIG['mid']
    
    # 1. 获取基本信息
    info_url = f'{API_BASE}/x/space/acc/info?mid={mid}'
    info_resp = requests.get(info_url, headers=HEADERS, timeout=10)
    info_data = info_resp.json()
    
    if info_data['code'] != 0:
        print(f"获取基本信息失败: {info_data}")
        return None
    
    info = info_data['data']
    
    # 2. 获取粉丝数
    relation_url = f'{API_BASE}/x/relation/stat?vmid={mid}'
    relation_resp = requests.get(relation_url, headers=HEADERS, timeout=10)
    relation_data = relation_resp.json()
    
    fans = relation_data.get('data', {}).get('follower', 0)
    
    # 3. 获取播放量统计
    upstat_url = f'{API_BASE}/x/space/upstat?mid={mid}'
    upstat_resp = requests.get(upstat_url, headers=HEADERS, timeout=10)
    upstat_data = upstat_resp.json()
    
    total_views = upstat_data.get('data', {}).get('archive', {}).get('view', 0)
    total_likes = upstat_data.get('data', {}).get('likes', 0)
    
    # 4. 获取视频列表（最新20个）
    videos_url = f'{API_BASE}/x/space/arc/search?mid={mid}&ps=20&pn=1'
    videos_resp = requests.get(videos_url, headers=HEADERS, timeout=10)
    videos_data = videos_resp.json()
    
    videos = []
    if videos_data.get('data', {}).get('list', {}).get('vlist'):
        for v in videos_data['data']['list']['vlist'][:20]:
            videos.append({
                'bvid': v.get('bvid', ''),
                'title': v.get('title', ''),
                'pic': v.get('pic', ''),
                'play': v.get('play', 0),
                'video_review': v.get('video_review', 0),  # 弹幕
                'comment': v.get('comment', 0),
                'like': v.get('like', 0),
                'favorites': v.get('favorites', 0),
                'coin': v.get('coin', 0),
                'share': v.get('share', 0),
                'length': v.get('length', ''),
                'created': v.get('created', 0),
            })
    
    # 组装数据
    now = datetime.now()
    data = {
        'update_time': now.strftime('%Y-%m-%d %H:%M:%S'),
        'timestamp': int(now.timestamp()),
        'date': now.strftime('%Y-%m-%d'),
        'mid': int(mid),
        'name': info.get('name', ''),
        'face': info.get('face', ''),
        'sign': info.get('sign', ''),
        'level': info.get('level', 0),
        'fans': fans,
        'total_views': total_views,
        'total_likes': total_likes,
        'video_count': len(videos),
        'videos': videos,
    }
    
    return data


def save_data(data):
    """保存数据到文件"""
    # 1. 保存最新数据到 data.json
    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"✓ 最新数据已保存到 data.json")
    
    # 2. 追加到历史记录 history.json
    history_file = 'history.json'
    history = []
    
    if os.path.exists(history_file):
        try:
            with open(history_file, 'r', encoding='utf-8') as f:
                history = json.load(f)
        except:
            history = []
    
    # 追加新记录（只保存关键字段，避免文件过大）
    history_record = {
        'timestamp': data['timestamp'],
        'date': data['date'],
        'update_time': data['update_time'],
        'fans': data['fans'],
        'total_views': data['total_views'],
        'total_likes': data['total_likes'],
        'video_count': data['video_count'],
        'videos': data['videos'],  # 保存完整视频数据
    }
    
    history.append(history_record)
    
    # 保存历史记录
    with open(history_file, 'w', encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=False, indent=2)
    
    print(f"✓ 历史记录已追加到 history.json (共 {len(history)} 条)")


def main():
    print(f"[{datetime.now()}] 开始抓取数据...")
    
    try:
        data = fetch_data()
        
        if data:
            save_data(data)
            print(f"\n📊 数据摘要:")
            print(f"  UP主: {data['name']}")
            print(f"  粉丝: {data['fans']:,}")
            print(f"  总播放: {data['total_views']:,}")
            print(f"  视频数: {data['video_count']}")
        else:
            print("✗ 抓取失败")
            exit(1)
            
    except Exception as e:
        print(f"✗ 错误: {e}")
        import traceback
        traceback.print_exc()
        exit(1)


if __name__ == '__main__':
    main()
