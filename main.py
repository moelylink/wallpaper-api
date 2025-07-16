import requests
import time
import json
import os
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from zoneinfo import ZoneInfo

# 配置
RANDOM_URL = "https://www.moely.link/random/jump/"
JSON_PATH = "wallpaper.json"
RETRY_DELAY = 1  # 秒

def fetch_wallpaper_data():
    # 循环访问随机跳转页面，直到解析成功
    while True:
        resp = requests.get(RANDOM_URL, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        script = soup.find("script", {"id": "wallpaper", "type": "application/json"})
        if script and script.string:
            return json.loads(script.string)
        time.sleep(RETRY_DELAY)

def load_existing():
    if os.path.exists(JSON_PATH):
        with open(JSON_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_all(data_list):
    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(data_list, f, ensure_ascii=False, indent=2)

def main():
    # 获取当前北京时间
    tz = ZoneInfo("Asia/Shanghai")
    today = datetime.now(tz).date()
    
    # 要插入的“有效日期” = 今天 + 7 天
    target_date = today + timedelta(days=7)
    date_str = target_date.strftime("%Y%m%d")

    # 抓取壁纸元数据
    info = fetch_wallpaper_data()
    # 附加日期字段
    info["date"] = date_str

    # 读取历史
    items = load_existing()

    # 去重：如果已有相同 id 且 date 相同，则不再添加
    if not any(item.get("id") == info["id"] and item.get("date") == info["date"] for item in items):
        items.append(info)

    # 过滤：仅保留 date 在 [today-7 .. today+7] 区间的记录
    min_date = today - timedelta(days=7)
    filtered = [
        item for item in items
        if min_date <= datetime.strptime(item["date"], "%Y%m%d").date() <= target_date
    ]

    # 按 date 排序
    filtered.sort(key=lambda x: x["date"])
    save_all(filtered)

if __name__ == "__main__":
    main()
