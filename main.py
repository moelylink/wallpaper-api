import json
import os
import time
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

JUMP_URL = "https://www.moely.link/random/jump/?wallpaper=true"
JSON_PATH = "wallpaper.json"

def log(msg: str):
    now = datetime.now(ZoneInfo("Asia/Shanghai")).strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{now}] {msg}")

def fetch_wallpaper_data(retries=1):
    """使用 Playwright 打开页面并获取 <script id="wallpaper"> 中的 JSON 数据，支持失败重试"""
    for attempt in range(retries + 1):
        try:
            with sync_playwright() as p:
                # 使用较新的 User-Agent 避免基础爬虫过滤
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                )
                page = context.new_page()
                log(f"▶️ 打开 {JUMP_URL} (第 {attempt + 1} 次尝试)")
                page.goto(JUMP_URL, timeout=30000, wait_until="domcontentloaded")
                
                # 等待页面发生跳转（URL 包含 /img/）
                try:
                    page.wait_for_url(lambda url: "/img/" in url, timeout=15000)
                except Exception:
                    log("⚠️ 页面未能在 15 秒内自动跳转，尝试获取当前页面内容")
                    
                # 等待目标脚本标签加载
                try:
                    page.wait_for_selector("script#wallpaper", timeout=10000)
                except Exception:
                    log("⚠️ 未在页面中找到 script#wallpaper 标签")

                html = page.content()
                browser.close()

            soup = BeautifulSoup(html, "html5lib")
            script = soup.find("script", {"id": "wallpaper"})
            if script and script.string:
                return json.loads(script.string)
            
            if attempt < retries:
                log("⚠️ 获取数据为空，准备重试...")
                time.sleep(2)
        except Exception as e:
            log(f"❌ 尝试出现异常: {e}")
            if attempt < retries:
                log("⚠️ 准备重试...")
                time.sleep(2)
            else:
                log("❌ 已达到最大重试次数")
    
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
    # 目标范围：今天前 7 天到今天后 7 天
    min_date = today - timedelta(days=7)
    max_date = today + timedelta(days=7)

    log(f"🚀 开始检查壁纸数据范围: {min_date} ~ {max_date}")
    
    items = load_existing()
    existing_dates = {item.get("date") for item in items}
    
    has_changes = False

    # 遍历范围内的每一天，补全缺失的日期
    current_d = min_date
    while current_d <= max_date:
        date_str = current_d.strftime("%Y%m%d")
        if date_str not in existing_dates:
            log(f"🔍 发现缺失日期: {date_str}，开始获取...")
            info = fetch_wallpaper_data(retries=1)
            if info:
                info["date"] = date_str
                items.append(info)
                existing_dates.add(date_str)
                log(f"🎨 日期 {date_str} 补全成功 (ID={info.get('id')})")
                has_changes = True
                # 给服务器一点喘息时间
                time.sleep(1)
            else:
                log(f"❌ 日期 {date_str} 补全失败")
        current_d += timedelta(days=1)

    if not has_changes:
        log("ℹ️ 所有日期均已存在，无需更新")

    # 过滤掉超出 [today-7 .. today+7] 范围的旧数据
    filtered = [
        it for it in items
        if min_date <= datetime.strptime(it["date"], "%Y%m%d").date() <= max_date
    ]
    filtered.sort(key=lambda x: x["date"])
    
    if len(filtered) != len(items) or has_changes:
        save_all(filtered)
    else:
        log("✨ 检查完毕，数据已是最新且无冗余")

if __name__ == "__main__":
    main()
