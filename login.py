#!/usr/bin/env python3
"""
B站扫码登录脚本 1
本地运行，扫码后保存Cookie到cookie.json，推送到GitHub
"""

import requests
import json
import os
import subprocess
import time
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
COOKIE_FILE = os.path.join(BASE_DIR, 'cookie.json')

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
    'Referer': 'https://www.bilibili.com',
    'Accept': 'application/json, text/plain, */*',
}

# ============================================================
# 扫码登录
# ============================================================
def qr_login():
    print("\n" + "=" * 60)
    print("  B站数据看板 - 扫码登录")
    print("=" * 60)
    print("\n[1/3] 正在获取二维码...")
    
    try:
        resp = requests.get('https://passport.bilibili.com/x/passport-login/web/qrcode/generate', headers=HEADERS, timeout=10)
        data = resp.json()
        if data.get('code') != 0:
            print(f"✗ 获取二维码失败: {data}")
            return None, None
    except Exception as e:
        print(f"✗ 网络请求失败: {e}")
        print("  请检查网络连接")
        return None, None
    
    qr_url = data['data']['url']
    qr_key = data['data']['qrcode_key']
    
    print("✓ 二维码获取成功")
    print("\n[2/3] 请用B站APP扫描二维码：\n")
    
    # 显示二维码
    try:
        import qrcode
        qr = qrcode.QRCode(box_size=1, border=1)
        qr.add_data(qr_url)
        qr.make(fit=True)
        qr.print_ascii(invert=True)
    except ImportError:
        print(f"链接: {qr_url}")
        print("(pip install qrcode 可以显示二维码)")
    except Exception as e:
        print(f"二维码显示失败: {e}")
        print(f"链接: {qr_url}")
    
    print("\n[3/3] 等待扫码...\n")
    
    start_time = time.time()
    while time.time() - start_time < 180:
        time.sleep(2)
        try:
            poll_resp = requests.get('https://passport.bilibili.com/x/passport-login/web/qrcode/poll',
                                    params={'qrcode_key': qr_key}, headers=HEADERS, timeout=10)
            poll_data = poll_resp.json().get('data', {})
            code = poll_data.get('code', -1)
            
            if code == 0:
                cookies = {}
                for cookie in poll_resp.cookies:
                    cookies[cookie.name] = cookie.value
                
                mid = None
                url_params = poll_data.get('url', '')
                if 'mid=' in url_params:
                    mid = url_params.split('mid=')[1].split('&')[0]
                if not mid and 'DedeUserID' in cookies:
                    mid = cookies['DedeUserID']
                
                # 获取用户名
                uname = ''
                try:
                    nav_resp = requests.get('https://api.bilibili.com/x/web-interface/nav',
                                          cookies=cookies, timeout=10,
                                          headers={'User-Agent': 'Mozilla/5.0', 'Referer': 'https://www.bilibili.com'})
                    nav_data = nav_resp.json().get('data', {})
                    uname = nav_data.get('uname', '')
                    if not mid:
                        mid = str(nav_data.get('mid', ''))
                except:
                    pass
                
                print(f"\n✓ 登录成功！用户: {uname} (UID: {mid})")
                return cookies, mid
            
            elif code == 86038:
                print("\n✗ 二维码已过期")
                return None, None
            elif code == 86090:
                print("已扫码，等待确认...")
            elif code == 86101:
                print(".", end="", flush=True)
        except:
            pass
    
    print("\n✗ 扫码超时")
    return None, None

# ============================================================
# 保存Cookie
# ============================================================
def save_cookie(cookies, mid):
    data = {
        'cookies': cookies,
        'mid': mid,
        'login_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    }
    with open(COOKIE_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"\n✓ Cookie已保存到 cookie.json")

# ============================================================
# 推送到GitHub
# ============================================================
def git_push():
    print("\n推送到GitHub...")
    try:
        subprocess.run(['git', 'add', 'cookie.json'], cwd=BASE_DIR, check=True)
        subprocess.run(['git', 'commit', '-m', f'Update cookie: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'],
                      cwd=BASE_DIR, check=True)
        subprocess.run(['git', 'push'], cwd=BASE_DIR, check=True)
        print("✓ 已推送到GitHub")
        print("\nGitHub Actions会自动使用这个Cookie抓取数据")
        print("打开GitHub仓库 → Actions 标签查看运行状态")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ 推送失败: {e}")
        print("请手动执行: git add cookie.json && git commit -m 'update' && git push")
        return False

# ============================================================
# 主流程
# ============================================================
def main():
    # 检查是否已有Cookie
    if os.path.exists(COOKIE_FILE):
        with open(COOKIE_FILE, 'r', encoding='utf-8') as f:
            old = json.load(f)
        print(f"\n已有Cookie（登录于 {old.get('login_time', '未知')}）")
        choice = input("重新扫码登录？(y/N): ").strip().lower()
        if choice != 'y':
            print("保留现有Cookie")
            push = input("是否推送到GitHub？(Y/n): ").strip().lower()
            if push != 'n':
                git_push()
            return
    
    # 扫码登录
    cookies, mid = qr_login()
    if not cookies:
        print("\n✗ 登录失败")
        exit(1)
    
    # 保存
    save_cookie(cookies, mid)
    
    # 推送
    git_push()
    
    print("\n" + "=" * 60)
    print("  ✅ 完成！")
    print("=" * 60)
    print("\n  GitHub Actions会每小时自动抓取数据")
    print("  打开GitHub仓库页面查看README")
    print("=" * 60)

if __name__ == '__main__':
    main()
