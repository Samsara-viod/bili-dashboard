#!/usr/bin/env python3
"""
B站数据抓取脚本
支持扫码登录、Cookie持久化、WBI签名
- cookie.json: 保存登录Cookie
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

# ============================================================
# 配置
# ============================================================
CONFIG = {
    'mid': '946974',  # 改成你自己的B站UID
}

API_BASE = 'https://api.bilibili.com'
COOKIE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cookie.json')

# ============================================================
# Cookie 管理
# ============================================================
def save_cookie(cookies_dict):
    """保存Cookie到本地文件"""
    with open(COOKIE_FILE, 'w', encoding='utf-8') as f:
        json.dump({
            'cookies': cookies_dict,
            'save_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        }, f, ensure_ascii=False, indent=2)
    print(f"✓ Cookie已保存到 {COOKIE_FILE}")


def load_cookie():
    """从本地文件加载Cookie"""
    if not os.path.exists(COOKIE_FILE):
        return None
    try:
        with open(COOKIE_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        cookies = data.get('cookies', {})
        save_time = data.get('save_time', '未知')
        print(f"✓ 已加载Cookie（保存于 {save_time}）")
        return cookies
    except Exception as e:
        print(f"[WARN] 加载Cookie失败: {e}")
        return None


def check_cookie_valid(cookies):
    """检查Cookie是否还有效"""
    try:
        resp = requests.get(
            f'{API_BASE}/x/web-interface/nav',
            headers=get_headers(cookies),
            cookies=cookies,
            timeout=10
        )
        data = resp.json()
        if data.get('code') == 0 and data.get('data', {}).get('isLogin'):
            uname = data['data'].get('uname', '')
            print(f"✓ Cookie有效，当前登录: {uname}")
            return True
        else:
            print("[WARN] Cookie已失效")
            return False
    except Exception as e:
        print(f"[WARN] 检查Cookie失败: {e}")
        return False


# ============================================================
# 扫码登录
# ============================================================
def qr_login():
    """B站扫码登录，返回Cookie字典"""
    print("\n" + "=" * 50)
    print("  B站扫码登录")
    print("=" * 50)

    # 1. 获取二维码
    print("\n[1/3] 正在获取二维码...")
    resp = requests.get(
        'https://passport.bilibili.com/x/passport-login/web/qrcode/generate',
        timeout=10
    )
    data = resp.json()
    if data.get('code') != 0:
        print(f"✗ 获取二维码失败: {data}")
        return None

    qr_url = data['data']['url']
    qr_key = data['data']['qrcode_key']

    # 2. 显示二维码
    print("[2/3] 请用B站APP扫描下方二维码：\n")
    try:
        import qrcode
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=1,
            border=1,
        )
        qr.add_data(qr_url)
        qr.make(fit=True)
        # 在终端打印二维码
        qr.print_ascii(invert=True)
    except ImportError:
        # 如果没有qrcode库，用纯文本方式
        print(f"  二维码链接（复制到浏览器打开，或用B站APP扫描）：")
        print(f"  {qr_url}")
        print()
        # 尝试生成图片
        try:
            import qrcode
            img = qrcode.make(qr_url)
            img_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'qr_login.png')
            img.save(img_path)
            print(f"  二维码已保存到: {img_path}")
            print(f"  可以用B站APP扫描这张图片")
        except:
            pass

    print(f"\n  等待扫码... (有效期约3分钟)")
    print(f"  提示: 也可以用浏览器打开上面的链接，然后用B站APP扫描浏览器上的二维码")

    # 3. 轮询扫码状态
    print("[3/3] ", end="", flush=True)
    start_time = time.time()
    while time.time() - start_time < 180:  # 3分钟超时
        time.sleep(2)
        try:
            poll_resp = requests.get(
                'https://passport.bilibili.com/x/passport-login/web/qrcode/poll',
                params={'qrcode_key': qr_key},
                timeout=10
            )
            poll_data = poll_resp.json().get('data', {})
            code = poll_data.get('code', -1)

            if code == 0:
                # 扫码成功！提取Cookie
                print("\n✓ 扫码登录成功！")
                cookies = {}
                for cookie in poll_resp.cookies:
                    cookies[cookie.name] = cookie.value
                # 也从Set-Cookie头提取
                for k, v in poll_resp.headers.items():
                    if k.lower() == 'set-cookie':
                        for part in v.split(','):
                            for item in part.split(';'):
                                item = item.strip()
                                if '=' in item:
                                    ck, cv = item.split('=', 1)
                                    cookies[ck.strip()] = cv.strip()

                # 补充从URL参数中提取
                url_params = urllib.parse.urlparse(poll_data.get('url', '')).query
                for param in urllib.parse.parse_qsl(url_params):
                    cookies[param[0]] = param[1]

                return cookies

            elif code == 86038:
                print("\n✗ 二维码已过期")
                return None
            elif code == 86090:
                print("已扫码，等待确认...", end="", flush=True)
            elif code == 86101:
                print(".", end="", flush=True)
            else:
                print(f"\n未知状态: {code} - {poll_data.get('message', '')}")
        except Exception as e:
            print(f"\n轮询失败: {e}")

    print("\n✗ 扫码超时")
    return None


def get_headers(cookies=None):
    """构建请求头"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
        'Referer': 'https://www.bilibili.com',
        'Origin': 'https://www.bilibili.com',
        'Accept': 'application/json, text/plain, */*',
    }
    if cookies:
        cookie_str = '; '.join(f'{k}={v}' for k, v in cookies.items())
        headers['Cookie'] = cookie_str
    return headers


# ============================================================
# WBI 签名
# ============================================================
MIXIN_KEY_ENC_TAB = [
    46, 47, 18, 2, 53, 8, 23, 32, 15, 50, 10, 31, 58, 3, 45, 35,
    27, 43, 5, 49, 33, 9, 42, 19, 29, 28, 14, 39, 12, 38, 41, 13,
    37, 48, 7, 16, 24, 55, 40, 61, 26, 17, 0, 1, 60, 51, 30, 4,
    22, 25, 54, 21, 56, 59, 6, 63, 57, 62, 11, 36, 20, 34, 44, 52,
]


def get_mixin_key(orig):
    return reduce(lambda s, i: s + orig[i], MIXIN_KEY_ENC_TAB, '')[:32]


def enc_wbi(params, cookies=None):
    """对请求参数进行WBI签名"""
    try:
        resp = requests.get(
            f'{API_BASE}/x/web-interface/nav',
            headers=get_headers(cookies),
            cookies=cookies,
            timeout=10
        )
        data = resp.json().get('data', {})
        img_url = data.get('wbi_img', {}).get('img_url', '')
        sub_url = data.get('wbi_img', {}).get('sub_url', '')
        img_key = img_url.rsplit('/', 1)[-1].split('.')[0] if img_url else ''
        sub_key = sub_url.rsplit('/', 1)[-1].split('.')[0] if sub_url else ''
    except:
        img_key, sub_key = '', ''

    if not img_key or not sub_key:
        return params

    mixin_key = get_mixin_key(img_key + sub_key)
    params['wts'] = round(time.time())
    params = dict(sorted(params.items()))
    for k, v in params.items():
        params[k] = ''.join(c for c in str(v) if c not in "!'()*")
    query = urllib.parse.urlencode(params)
    wbi_sign = hashlib.md5((query + mixin_key).encode()).hexdigest()
    params['w_rid'] = wbi_sign
    return params


def bili_get(url, params=None, signed=False, cookies=None):
    """请求B站API"""
    if params is None:
        params = {}
    if signed:
        params = enc_wbi(params, cookies)
    resp = requests.get(
        url, params=params,
        headers=get_headers(cookies),
        cookies=cookies,
        timeout=15
    )
    return resp.json()


# ============================================================
# 数据抓取
# ============================================================
def fetch_data(cookies):
    """抓取UP主数据"""
    mid = CONFIG['mid']

    # 1. 获取基本信息（需要WBI签名 + Cookie）
    info_resp = bili_get(
        f'{API_BASE}/x/space/wbi/acc/info',
        {'mid': mid},
        signed=True,
        cookies=cookies
    )
    if info_resp.get('code') != 0:
        print(f"获取基本信息失败: {info_resp}")
        return None
    info = info_resp['data']

    # 2. 获取粉丝数
    relation = bili_get(
        f'{API_BASE}/x/relation/stat',
        {'vmid': mid},
        cookies=cookies
    )
    fans = relation.get('data', {}).get('follower', 0)

    # 3. 获取播放量统计
    upstat = bili_get(
        f'{API_BASE}/x/space/upstat',
        {'mid': mid},
        cookies=cookies
    )
    total_views = upstat.get('data', {}).get('archive', {}).get('view', 0)
    total_likes = upstat.get('data', {}).get('likes', 0)

    # 4. 获取视频列表（最新20个）
    videos_resp = bili_get(
        f'{API_BASE}/x/space/wbi/arc/search',
        {'mid': mid, 'ps': 20, 'pn': 1, 'tid': 0, 'order': 'pubdate', 'platform': 'web'},
        signed=True,
        cookies=cookies
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

    now = datetime.now()
    return {
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


def save_data(data):
    """保存数据"""
    # 最新数据
    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"✓ 最新数据已保存到 data.json")

    # 追加历史记录
    history_file = 'history.json'
    history = []
    if os.path.exists(history_file):
        try:
            with open(history_file, 'r', encoding='utf-8') as f:
                history = json.load(f)
        except:
            history = []

    history.append({
        'timestamp': data['timestamp'],
        'date': data['date'],
        'update_time': data['update_time'],
        'fans': data['fans'],
        'total_views': data['total_views'],
        'total_likes': data['total_likes'],
        'video_count': data['video_count'],
        'videos': data['videos'],
    })

    with open(history_file, 'w', encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=False, indent=2)
    print(f"✓ 历史记录已追加到 history.json (共 {len(history)} 条)")


# ============================================================
# 主流程
# ============================================================
def main():
    print(f"[{datetime.now()}] B站数据抓取脚本")
    print("=" * 50)

    # 1. 加载或获取Cookie
    cookies = load_cookie()

    if cookies and check_cookie_valid(cookies):
        print("  使用已保存的Cookie")
    else:
        print("\n  需要重新登录")
        cookies = qr_login()
        if not cookies:
            print("\n✗ 登录失败，退出")
            exit(1)
        save_cookie(cookies)

    # 2. 抓取数据
    print(f"\n[抓取数据] UID: {CONFIG['mid']}")
    data = fetch_data(cookies)

    if data:
        save_data(data)
        print(f"\n{'=' * 50}")
        print(f"📊 数据摘要:")
        print(f"  UP主:   {data['name']}")
        print(f"  粉丝:   {data['fans']:,}")
        print(f"  总播放: {data['total_views']:,}")
        print(f"  获赞:   {data['total_likes']:,}")
        print(f"  视频数: {data['video_count']}")
        print(f"{'=' * 50}")
    else:
        print("\n✗ 抓取失败")
        # 可能是Cookie失效，删除Cookie文件
        if os.path.exists(COOKIE_FILE):
            os.remove(COOKIE_FILE)
            print("  Cookie已失效，下次运行需要重新扫码")
        exit(1)


if __name__ == '__main__':
    main()
