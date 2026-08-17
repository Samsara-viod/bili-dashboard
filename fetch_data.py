#!/usr/bin/env python3
"""
B站数据抓取脚本（GitHub Actions版）
支持从环境变量或cookie.json读取Cookie
抓取数据后更新README.md、data.json、history.json
"""

import requests
import json
import os
import hashlib
import time
import urllib.parse
from datetime import datetime
from functools import reduce

# ============================================================
# 配置
# ============================================================
API_BASE = 'https://api.bilibili.com'
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
COOKIE_FILE = os.path.join(BASE_DIR, 'cookie.json')
README_FILE = os.path.join(BASE_DIR, 'README.md')
DATA_FILE = os.path.join(BASE_DIR, 'data.json')
HISTORY_FILE = os.path.join(BASE_DIR, 'history.json')

# ============================================================
# Cookie管理
# ============================================================
def load_cookie():
    """优先从环境变量读取Cookie，否则从cookie.json读取"""
    # 方式1: 从环境变量读取（GitHub Actions Secrets）
    cookie_json_str = os.environ.get('BILIBILI_COOKIE')
    if cookie_json_str:
        try:
            data = json.loads(cookie_json_str)
            cookies = data.get('cookies', {})
            mid = data.get('mid', '')
            print(f"✓ 已从环境变量加载Cookie (UID: {mid})")
            return cookies, mid
        except Exception as e:
            print(f"✗ 解析环境变量Cookie失败: {e}")
    
    # 方式2: 从cookie.json读取（本地运行）
    if not os.path.exists(COOKIE_FILE):
        print("✗ 未找到Cookie")
        print("  GitHub Actions: 请在 Settings → Secrets 中设置 BILIBILI_COOKIE")
        print("  本地运行: 请先运行 python login.py")
        return None, None
    
    try:
        with open(COOKIE_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        cookies = data.get('cookies', {})
        mid = data.get('mid', '')
        login_time = data.get('login_time', '未知')
        print(f"✓ 已从cookie.json加载Cookie (UID: {mid}, 登录于: {login_time})")
        return cookies, mid
    except Exception as e:
        print(f"✗ 读取cookie.json失败: {e}")
        return None, None

def check_cookie(cookies):
    """检查Cookie是否有效"""
    try:
        resp = requests.get(f'{API_BASE}/x/web-interface/nav', cookies=cookies, timeout=10,
                          headers={'User-Agent': 'Mozilla/5.0', 'Referer': 'https://www.bilibili.com'})
        data = resp.json()
        if data.get('code') == 0 and data.get('data', {}).get('isLogin'):
            uname = data['data'].get('uname', '')
            print(f"✓ Cookie有效，当前用户: {uname}")
            return True
        else:
            print("✗ Cookie已失效")
            return False
    except Exception as e:
        print(f"✗ 检查Cookie失败: {e}")
        return False

# ============================================================
# WBI签名
# ============================================================
MIXIN_KEY_ENC_TAB = [46,47,18,2,53,8,23,32,15,50,10,31,58,3,45,35,27,43,5,49,33,9,42,19,29,28,14,39,12,38,41,13,37,48,7,16,24,55,40,61,26,17,0,1,60,51,30,4,22,25,54,21,56,59,6,63,57,62,11,36,20,34,44,52]

def get_mixin_key(orig):
    return reduce(lambda s, i: s + orig[i], MIXIN_KEY_ENC_TAB, '')[:32]

def enc_wbi(params, cookies):
    try:
        resp = requests.get(f'{API_BASE}/x/web-interface/nav', cookies=cookies, timeout=10,
                          headers={'User-Agent': 'Mozilla/5.0', 'Referer': 'https://www.bilibili.com'})
        data = resp.json().get('data', {})
        img_key = data.get('wbi_img', {}).get('img_url', '').rsplit('/', 1)[-1].split('.')[0]
        sub_key = data.get('wbi_img', {}).get('sub_url', '').rsplit('/', 1)[-1].split('.')[0]
    except:
        return params
    
    if not img_key or not sub_key:
        return params
    
    mixin_key = get_mixin_key(img_key + sub_key)
    params['wts'] = round(time.time())
    params = dict(sorted(params.items()))
    for k, v in params.items():
        params[k] = ''.join(c for c in str(v) if c not in "!'()*")
    query = urllib.parse.urlencode(params)
    params['w_rid'] = hashlib.md5((query + mixin_key).encode()).hexdigest()
    return params

def bili_get(url, params=None, cookies=None, signed=False):
    if params is None:
        params = {}
    if signed and cookies:
        params = enc_wbi(params, cookies)
    headers = {'User-Agent': 'Mozilla/5.0', 'Referer': 'https://www.bilibili.com'}
    resp = requests.get(url, params=params, headers=headers, cookies=cookies, timeout=15)
    return resp.json()

# ============================================================
# 数据抓取
# ============================================================
def fetch_data(cookies, mid):
    """抓取B站数据"""
    info = bili_get(f'{API_BASE}/x/space/wbi/acc/info', {'mid': mid}, cookies, signed=True)
    if info.get('code') != 0:
        print(f"✗ 获取基本信息失败: {info.get('message', 'unknown')}")
        return None
    info = info['data']
    
    relation = bili_get(f'{API_BASE}/x/relation/stat', {'vmid': mid}, cookies)
    fans = relation.get('data', {}).get('follower', 0)
    
    upstat = bili_get(f'{API_BASE}/x/space/upstat', {'mid': mid}, cookies)
    total_views = upstat.get('data', {}).get('archive', {}).get('view', 0)
    total_likes = upstat.get('data', {}).get('likes', 0)
    
    videos_resp = bili_get(f'{API_BASE}/x/space/wbi/arc/search',
                          {'mid': mid, 'ps': 10, 'pn': 1, 'tid': 0, 'order': 'pubdate', 'platform': 'web'},
                          cookies, signed=True)
    
    videos = []
    for v in videos_resp.get('data', {}).get('list', {}).get('vlist', [])[:10]:
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
    
    now = datetime.now()
    return {
        'update_time': now.strftime('%Y-%m-%d %H:%M:%S'),
        'mid': mid,
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

# ============================================================
# 更新README
# ============================================================
def fmt(num):
    """格式化数字"""
    if num >= 100000000:
        return f"{num/100000000:.1f}亿"
    if num >= 10000:
        return f"{num/10000:.1f}万"
    return f"{num:,}"

def update_readme(data):
    """更新README.md"""
    video_rows = ""
    for v in data['videos']:
        date = datetime.fromtimestamp(v['created']).strftime('%Y-%m-%d')
        title = v['title'][:35] + '...' if len(v['title']) > 35 else v['title']
        video_rows += f"| [{title}](https://www.bilibili.com/video/{v['bvid']}) | {fmt(v['play'])} | {fmt(v['video_review'])} | {fmt(v['comment'])} | {fmt(v['like'])} | {date} |\n"
    
    readme = f"""# 📊 B站数据看板

> **{data['name']}** 的个人数据看板
> 
> {data['sign'] if data['sign'] else '这个人很懒，什么都没有写'}

## 📈 账号数据

| 指标 | 数值 |
|------|------|
| 👥 粉丝数 | **{fmt(data['fans'])}** |
| 👁️ 总播放量 | **{fmt(data['total_views'])}** |
| 👍 获赞数 | **{fmt(data['total_likes'])}** |
| 🎬 视频数 | **{data['video_count']}** |

## 🎥 最新视频

| 视频 | 播放 | 弹幕 | 评论 | 点赞 | 发布日期 |
|------|------|------|------|------|----------|
{video_rows}
---

**最后更新**: {data['update_time']}

*数据每小时自动更新 · [查看可视化看板](index.html)*
"""
    
    with open(README_FILE, 'w', encoding='utf-8') as f:
        f.write(readme)
    print("✓ README.md 已更新")

def update_data_json(data):
    """更新data.json（前端页面读取）"""
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print("✓ data.json 已更新")

def update_history_json(data):
    """更新history.json（追加历史记录）"""
    history = []
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                history = json.load(f)
        except:
            history = []
    
    # 构造历史记录条目
    record = {
        'update_time': data['update_time'],
        'timestamp': int(time.time()),
        'fans': data['fans'],
        'total_views': data['total_views'],
        'total_likes': data['total_likes'],
        'video_count': data['video_count'],
    }
    
    # 避免重复（同一小时内只记录一次）
    if history and history[-1].get('update_time') == record['update_time']:
        history[-1] = record
    else:
        history.append(record)
    
    # 最多保留2000条记录
    if len(history) > 2000:
        history = history[-2000:]
    
    with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=False, indent=2)
    print(f"✓ history.json 已更新 (共 {len(history)} 条记录)")

# ============================================================
# 主流程
# ============================================================
def main():
    print(f"[{datetime.now()}] B站数据抓取脚本")
    print("=" * 50)
    
    # 1. 加载Cookie
    cookies, mid = load_cookie()
    if not cookies or not mid:
        exit(1)
    
    # 2. 检查Cookie
    if not check_cookie(cookies):
        print("\n请重新运行: python login.py")
        exit(1)
    
    # 3. 抓取数据
    print(f"\n[抓取数据] UID: {mid}")
    data = fetch_data(cookies, mid)
    
    if not data:
        print("\n✗ 抓取失败")
        exit(1)
    
    # 4. 更新README
    print(f"\n[更新README]")
    update_readme(data)
    
    # 5. 更新data.json（前端页面用）
    print(f"\n[更新data.json]")
    update_data_json(data)
    
    # 6. 更新history.json（前端页面用）
    print(f"\n[更新history.json]")
    update_history_json(data)
    
    # 7. 打印摘要
    print(f"\n{'=' * 50}")
    print(f"📊 数据摘要:")
    print(f"  UP主:   {data['name']}")
    print(f"  粉丝:   {fmt(data['fans'])}")
    print(f"  总播放: {fmt(data['total_views'])}")
    print(f"  获赞:   {fmt(data['total_likes'])}")
    print(f"  视频数: {data['video_count']}")
    print(f"{'=' * 50}")
    print(f"\n✅ 完成！")

if __name__ == '__main__':
    main()
