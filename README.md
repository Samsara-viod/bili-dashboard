# Bilibili Data Dashboard

私有的B站账号数据看板，支持扫码登录、数据自动保存、历史趋势查询。

## ✨ 特性

- 🔐 **扫码登录** - 首次运行扫码登录，Cookie自动保存
- 📊 **数据全量保存** - 每次抓取追加到 history.json，永久保存
- 📈 **历史趋势查询** - 粉丝/播放/获赞增长曲线
- 🎬 **视频数据追踪** - 每个视频的播放/弹幕/评论/点赞/收藏/投币
- 🔄 **自动更新** - GitHub Actions每小时自动抓取
- 🔒 **完全私有** - 仓库设为Private，只有你能看到

## 🚀 快速开始

### 1. 安装依赖

```bash
cd F:\projects\bilibili-dashboard-github
pip install -r requirements.txt
```

### 2. 修改配置

打开 `fetch_data.py`，找到第24行：

```python
CONFIG = {
    'mid': '946974',  # ← 改成你自己的B站UID
}
```

**如何找UID？** 打开你的B站空间，URL里的数字就是：
```
https://space.bilibili.com/12345678
                          ↑
                      这个数字
```

### 3. 首次运行（扫码登录）

```bash
python fetch_data.py
```

会显示二维码，用B站APP扫码登录。登录成功后Cookie自动保存到 `cookie.json`。

### 4. 推送到GitHub

```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/你的用户名/bili-dashboard.git
git push -u origin main
```

**重要：创建仓库时选择 Private（私有）！**

### 5. 手动触发第一次数据抓取

1. 打开仓库 → **Actions** 标签
2. 左侧选 **Fetch Bilibili Data**
3. 右侧点 **Run workflow** → **Run workflow**
4. 等待几十秒

### 6. 本地查看看板

```bash
git pull
```

然后双击 `index.html` 用浏览器打开。

## 🔐 Cookie说明

- 首次运行需要扫码登录
- Cookie保存在 `cookie.json`（已加入.gitignore，不会上传）
- Cookie有效期约6个月
- Cookie失效后重新运行脚本扫码即可

**GitHub Actions需要Cookie才能运行**，但Cookie文件不会上传到仓库。解决方案：

### 方案A：本地运行（推荐）

不用GitHub Actions，本地用Windows定时任务：

1. 创建 `run.bat`：
```batch
@echo off
cd F:\projects\bilibili-dashboard-github
python fetch_data.py
git pull
git add data.json history.json
git commit -m "Update data"
git push
```

2. 用Windows任务计划程序，每小时运行一次 `run.bat`

### 方案B：手动更新

每次想看数据时：
```bash
python fetch_data.py
git add data.json history.json
git commit -m "Update"
git push
git pull  # 更新本地看板
```

## 📁 文件说明

```
bili-dashboard/
├── fetch_data.py          # 数据抓取脚本（支持扫码登录）
├── index.html             # 前端看板页面
├── cookie.json            # 登录Cookie（自动生成，不上传）
├── data.json              # 最新数据（自动生成）
├── history.json           # 历史记录（自动生成）
├── requirements.txt       # Python依赖
├── .gitignore            # Git忽略配置
└── README.md
```

## 📊 数据说明

### data.json
最新一次抓取的数据，包含：
- UP主基本信息（头像、昵称、签名）
- 粉丝数、总播放量、获赞数
- 最新20个视频的完整数据

### history.json
每次抓取追加一条记录，包含：
- 时间戳
- 粉丝数、总播放量、获赞数
- 最新20个视频的完整数据

## ❓ 常见问题

**Q: Cookie失效了怎么办？**

重新运行 `python fetch_data.py`，扫码登录即可。

**Q: GitHub Actions报错？**

因为Cookie文件不会上传，Actions无法访问API。建议用本地定时任务。

**Q: 可以显示点入率、观看时长吗？**

这些数据只有B站创作中心后台才有，公开API拿不到。

**Q: 如何在手机上查看？**

方式一：手机浏览器访问GitHub Pages（需要Pro账号）
方式二：在GitHub App里打开仓库，查看data.json

## 📝 License

MIT
