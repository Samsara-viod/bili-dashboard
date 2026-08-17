# Bilibili Data Dashboard

私有的B站账号数据看板，所有数据自动保存，支持历史查询。

## ✨ 特性

- 📊 **数据全量保存** — 每次抓取的数据都追加到 history.json，永久保存
- 📈 **历史趋势查询** — 粉丝/播放/获赞增长曲线，支持7天/30天/全部时间范围
- 🔒 **完全私有** — 仓库设为Private，只有你自己能看到
- 🎬 **视频数据追踪** — 每个视频的播放/弹幕/评论/点赞/收藏/投币
- ⚡ **自动更新** — GitHub Actions每小时自动抓取
- 🆓 **零成本** — 不需要服务器，GitHub免费额度足够

## 🚀 部署步骤

### 1. 创建私有仓库

1. 在GitHub上新建仓库，名字随意（比如 `bili-dashboard`）
2. **重要：选择 Private（私有）**
3. 不要勾选 "Add a README file"（我们会本地推送）

### 2. 修改配置

打开 `fetch_data.py`，第14行：

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

### 3. 推送到GitHub

在项目目录执行：

```bash
cd F:\projects\bilibili-dashboard-github
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/你的用户名/bili-dashboard.git
git push -u origin main
```

### 4. 手动触发第一次数据抓取

1. 打开你的仓库 → **Actions** 标签
2. 左侧选 **Fetch Bilibili Data**
3. 右侧点 **Run workflow** → **Run workflow**
4. 等待几十秒

### 5. 查看数据

**方式一：本地查看（推荐）**

```bash
git clone https://github.com/你的用户名/bili-dashboard.git
cd bili-dashboard
# 直接用浏览器打开 index.html
```

**方式二：GitHub网页查看**

直接在仓库里打开 `data.json` 或 `history.json` 查看原始数据。

**方式三：GitHub Pages（可选）**

如果你想通过网页访问看板：
1. 仓库 → Settings → Pages
2. Source 选 **Deploy from a branch**
3. Branch 选 **main** / **root**
4. 访问 `https://你的用户名.github.io/bili-dashboard/`

**注意：私有仓库的GitHub Pages需要GitHub Pro账号。免费账号的私有仓库无法开启Pages。**

## 📁 文件说明

```
bili-dashboard/
├── .github/workflows/fetch.yml  # 定时任务（每小时抓取）
├── fetch_data.py                # 数据抓取脚本
├── index.html                   # 前端看板页面
├── data.json                    # 最新数据（自动生成）
├── history.json                 # 历史记录（自动生成，越来越大）
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

**数据会越来越多，但每小时只增加一条，一年大约8760条，文件不会太大。**

## 🔧 自定义

### 修改更新频率

编辑 `.github/workflows/fetch.yml`：

```yaml
schedule:
  # 每30分钟
  - cron: '*/30 * * * *'
  
  # 每2小时
  - cron: '0 */2 * * *'
  
  # 每天早8点（北京时间）
  - cron: '0 0 * * *'
```

### 修改抓取的视频数量

编辑 `fetch_data.py`，找到这一行：

```python
for v in videos_data['data']['list']['vlist'][:20]:
```

把 `20` 改成你想要的数量。

## ❓ 常见问题

**Q: 数据没有更新？**

检查 Actions 标签页的运行记录，如果有错误会显示日志。

**Q: history.json 会不会太大？**

每小时一条记录，一年约8760条。每条记录包含20个视频数据，大约几MB，完全没问题。

**Q: 可以删除历史记录吗？**

可以手动编辑 history.json，或者删除后重新抓取。

**Q: 会被B站封IP吗？**

每小时只请求一次，频率极低，不会被封。GitHub Actions的IP池也很大。

**Q: 如何在手机上查看？**

方式一：手机浏览器访问GitHub Pages（如果开启了）
方式二：在GitHub App里打开仓库，查看data.json
方式三：用SSH或Git客户端clone到手机

## 📝 License

MIT
