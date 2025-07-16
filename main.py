import json
import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

JUMP_URL = "https://www.moely.link/random/jump/?wallpaper=true"
JSON_PATH = "wallpaper.json"

def log(msg: str):
    now = datetime.now(ZoneInfo("Asia/Shanghai")).strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{now}] {msg}")

def fetch_wallpaper_data():
    """使用 Playwright 打开页面并获取 <script id="wallpaper"> 中的 JSON 数据"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        log(f"▶️ 打开 {JUMP_URL}")
        page.goto(JUMP_URL, timeout=30000)
        page.wait_for_load_state("load")
        html = page.content()
        browser.close()

    soup = BeautifulSoup(html, "html.parser")
    script = soup.find("script", {"id": "wallpaper", "type": "application/json"})
    if script and script.string:
        return json.loads(script.string)
    else:
        return None

def load_existing():
    if os.path.exists(JSON_PATH):
        with open(JSON_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_all(data_list):
    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(data_list, f, ensure_ascii=False, indent=2)
    log(f"✅ 保存 {JSON_PATH}，共 {len(data_list)} 条记录")

def main():
    tz = ZoneInfo("Asia/Shanghai")
    today = datetime.now(tz).date()
    target_date = today + timedelta(days=7)
    date_str = target_date.strftime("%Y%m%d")

    log("🚀 开始获取随机壁纸信息")
    info = fetch_wallpaper_data()
    if not info:
        log("❌ 未能获取到 wallpaper 数据，程序终止")
        return

    info["date"] = date_str
    log(f"✅ 获取到 wallpaper ID={info.get('id')}，目标日期={date_str}")

    items = load_existing()

    # 基于 date 判断是否已存在
    if not any(item.get("date") == date_str for item in items):
        items.append(info)
        log("🎨 壁纸添加成功")
    else:
        log("ℹ️ 壁纸已存在，不重复添加")

    # 过滤保留 [today-7 .. today+7]
    min_date = today - timedelta(days=7)
    filtered = [
        it for it in items
        if min_date <= datetime.strptime(it["date"], "%Y%m%d").date() <= target_date
    ]
    filtered.sort(key=lambda x: x["date"])
    save_all(filtered)

if __name__ == "__main__":
    main()
