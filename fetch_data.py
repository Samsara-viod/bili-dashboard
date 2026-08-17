#!/usr/bin/env python3
"""
B站数据抓取脚本（带WBI签名）
用于GitHub Actions定时执行，抓取UP主数据并保存
- data.json: 最新数据
- history.json: 历史记录（每次抓取追加一条）
"""

import requests
import json
import os
import hashlib
import time
import urllib.parse
from datetime import datetime
from functools import reduce

# 配置：修改这里为你的B站UID
CONFIG = {
    'mid': '946974',  # 改成你自己的B站UID
}

# B站API
API_BASE = 'https://api.bilibili.com'

# 请求头
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
    'Referer': 'https://www.bilibili.com',
    'Origin': 'https://www.bilibili.com',
    'Accept': 'application/json, text/plain, */*',
}

# ============================================================
# WBI 签名（B站反爬必须）
# ============================================================
MIXIN_KEY_ENC_TAB = [
    46, 47, 18, 2, 53, 8, 23, 32, 15, 50, 10, 31, 58, 3, 45, 35,
    27, 43, 5, 49, 33, 9, 42, 19, 29, 28, 14, 39, 12, 38, 41, 13,
    37, 48, 7, 16, 24, 55, 40, 61, 26, 17, 0, 1, 60, 51, 30, 4,
    22, 25, 54, 21, 56, 59, 6, 63, 57, 62, 11, 36, 20, 34, 44, 52,
]


def get_mixin_key(orig):
    return reduce(lambda s, i: s + orig[i], MIXIN_KEY_ENC_TAB, '')[:32]


def get_wbi_keys():
    """获取WBI签名所需的img_key和sub_key"""
    try:
        resp = requests.get(
            f'{API_BASE}/x/web-interface/nav',
            headers=HEADERS, timeout=10
        )
        data = resp.json().get('data', {})
        img_url = data.get('wbi_img', {}).get('img_url', '')
        sub_url = data.get('wbi_img', {}).get('sub_url', '')
        img_key = img_url.rsplit('/', 1)[-1].split('.')[0] if img_url else ''
        sub_key = sub_url.rsplit('/', 1)[-1].split('.')[0] if sub_url else ''
        return img_key, sub_key
    except Exception as e:
        print(f"[WARN] 获取WBI Keys失败: {e}")
        return '', ''


def enc_wbi(params):
    """对请求参数进行WBI签名"""
    img_key, sub_key = get_wbi_keys()
    if not img_key or not sub_key:
        return params

    mixin_key = get_mixin_key(img_key + sub_key)
    params['wts'] = round(time.time())

    # 按key排序
    params = dict(sorted(params.items()))
    # 过滤特殊字符
    for k, v in params.items():
        params[k] = ''.join(c for c in str(v) if c not in "!'()*")

    query = urllib.parse.urlencode(params)
    wbi_sign = hashlib.md5((query + mixin_key).encode()).hexdigest()
    params['w_rid'] = wbi_sign
    return params


def bili_get(url, params=None, signed=False):
    """请求B站API，signed=True时自动加WBI签名"""
    if params is None:
        params = {}
    if signed:
        params = enc_wbi(params)
    resp = requests.get(url, params=params, headers=HEADERS, timeout=15)
    return resp.json()


# ============================================================
# 数据抓取
# ============================================================
def fetch_data():
    """抓取UP主数据"""
    mid = CONFIG['mid']

    # 1. 获取基本信息（需要WBI签名）
    info = bili_get(
        f'{API_BASE}/x/space/wbi/acc/info',
        {'mid': mid},
        signed=True
    )
    if info.get('code') != 0:
        print(f"获取基本信息失败: {info}")
        return None
    info = info['data']

    # 2. 获取粉丝数
    relation = bili_get(f'{API_BASE}/x/relation/stat', {'vmid': mid})
    fans = relation.get('data', {}).get('follower', 0)

    # 3. 获取播放量统计
    upstat = bili_get(f'{API_BASE}/x/space/upstat', {'mid': mid})
    total_views = upstat.get('data', {}).get('archive', {}).get('view', 0)
    total_likes = upstat.get('data', {}).get('likes', 0)

    # 4. 获取视频列表（最新20个，需要WBI签名）
    videos_resp = bili_get(
        f'{API_BASE}/x/space/wbi/arc/search',
        {'mid': mid, 'ps': 20, 'pn': 1, 'tid': 0, 'order': 'pubdate', 'platform': 'web'},
        signed=True
    )

    videos = []
    vlist = videos_resp.get('data', {}).get('list', {}).get('vlist', [])
    for v in vlist[:20]:
        videos.append({
            'bvid': v.get('bvid', ''),
            'title': v.get('title', ''),
            'pic': v.get('pic', ''),
            'play': v.get('play', 0),
            'video_review': v.get('video_review', 0),
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

    # 追加新记录
    history_record = {
        'timestamp': data['timestamp'],
        'date': data['date'],
        'update_time': data['update_time'],
        'fans': data['fans'],
        'total_views': data['total_views'],
        'total_likes': data['total_likes'],
        'video_count': data['video_count'],
        'videos': data['videos'],
    }

    history.append(history_record)

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
