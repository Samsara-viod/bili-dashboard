# 📊 B站数据看板

> 自动抓取B站数据，每小时更新一次

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 扫码登录

```bash
python login.py
```

会显示二维码，用B站APP扫码登录。登录成功后Cookie会自动保存到 `cookie.json` 并推送到GitHub。

### 3. 查看数据

等待1-2分钟，GitHub Actions会自动抓取数据并更新这个README页面。

也可以手动触发：
- 打开仓库 → **Actions** 标签
- 左侧选 **Fetch Bilibili Data**
- 右侧点 **Run workflow** → **Run workflow**

## 📁 文件说明

| 文件 | 说明 |
|------|------|
| `login.py` | 本地扫码登录脚本 |
| `fetch_data.py` | GitHub Actions运行的数据抓取脚本 |
| `cookie.json` | 登录凭证（自动保存，推送到私有仓库） |
| `requirements.txt` | Python依赖 |

## 🔒 安全说明

- 仓库设为 **Private**，只有你自己能看到
- Cookie保存在私有仓库里，GitHub Actions自动读取
- Cookie有效期约6个月，失效后重新运行 `python login.py`

## ⚙️ 工作原理

```
本地运行 python login.py
    ↓
扫码登录 → 保存cookie.json
    ↓
git push 推送到GitHub（私有仓库）
    ↓
GitHub Actions 每小时运行 fetch_data.py
    ↓
读取cookie.json → 抓取B站数据 → 更新README.md
    ↓
打开GitHub仓库页面 → 直接看数据
```

## ❓ 常见问题

**Q: Cookie失效了怎么办？**

重新运行 `python login.py`，扫码登录即可。

**Q: 数据没有更新？**

检查 Actions 标签页的运行记录，如果有错误会显示日志。

**Q: 可以修改更新频率吗？**

编辑 `.github/workflows/fetch.yml`，修改 `cron` 表达式：
```yaml
schedule:
  # 每30分钟
  - cron: '*/30 * * * *'
  
  # 每2小时
  - cron: '0 */2 * * *'
```

---

*数据每小时自动更新 · 仓库私有，仅自己可见*
