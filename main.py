import requests
import json
import os
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from zoneinfo import ZoneInfo

# 配置
RANDOM_URL = "https://www.moely.link/random/jump/?wallpaper=true"
JSON_PATH = "wallpaper.json"

def log(msg):
    now = datetime.now(ZoneInfo("Asia/Shanghai")).strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{now}] {msg}")

def fetch_wallpaper_data():
    try:
        resp = requests.get(RANDOM_URL, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        script = soup.find("script", {"id": "wallpaper", "type": "application/json"})
        if script and script.string:
            return json.loads(script.string)
        else:
            log("❌ 页面中未找到壁纸数据")
            return None
    except Exception as e:
        log(f"❌ 请求或解析失败: {e}")
        return None

def load_existing():
    if os.path.exists(JSON_PATH):
        with open(JSON_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_all(data_list):
    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(data_list, f, ensure_ascii=False, indent=2)
    log(f"✅ 壁纸信息保存成功，共 {len(data_list)} 条记录")

def main():
    tz = ZoneInfo("Asia/Shanghai")
    today = datetime.now(tz).date()
    target_date = today + timedelta(days=7)
    date_str = target_date.strftime("%Y%m%d")

    log("🚀 开始获取随机壁纸信息")
    info = fetch_wallpaper_data()
    if not info:
        log("⚠️ 获取失败，程序终止")
        return

    info["date"] = date_str
    log(f"✅ 成功获取 wallpaper ID: {info.get('id')}，目标日期: {date_str}")

    items = load_existing()

    # 判断是否已存在相同记录
    if not any(item.get("date") == info["date"] for item in items):
        items.append(info)
        log("🎨 新壁纸添加成功")
    else:
        log("ℹ️ 壁纸已存在，不重复添加")

    # 保留 [today - 7, today + 7] 范围的记录
    min_date = today - timedelta(days=7)
    filtered = [
        item for item in items
        if min_date <= datetime.strptime(item["date"], "%Y%m%d").date() <= target_date
    ]
    filtered.sort(key=lambda x: x["date"])
    save_all(filtered)

if __name__ == "__main__":
    main()
