import csv
from playwright.sync_api import sync_playwright
from pathlib import Path

# 7.4 前往網頁並等待表格
CDP_URL = "http://127.0.0.1:9222"
GOSSIPING_URL = "https://www.ptt.cc/bbs/Gossiping/index.html"
OUTPUT_FILE = Path(__file__).parent / "gossiping.csv"

# 7.6 清理文字
def clean_text(value):
    return " ".join(value.split())
#print("正在連接到 Chrome...")

# 7.2 宣告區：取得 nopCommerce 分頁
def get_page(context):
    for page in context.pages:
        if "ptt.cc" in page.url:
            return page
    return context.new_page()
#print("正在開啟新頁...")

# 7.4 的宣告：前往 PTT 八卦版並等待文章列表載入
def scrape_article(page):
    print(f"【DEBUG A】正在前往網址: {GOSSIPING_URL}")
    page.goto(GOSSIPING_URL)
    repeat_times = 3  # 重複3次 (要爬 3 頁
    cc = 0  # 總文章計數器
    posts = []

    for page_num in range(1, repeat_times + 1):
        print(f"\n【DEBUG】🔄 正在處理第 {page_num} 頁...")
        
        page.wait_for_selector(".r-ent", timeout=30000)
    
# 7.5 擷取PTT文章頁面欄位
        rows = page.locator(".r-ent")
        print(f"【DEBUG】畫面上目前偵測到的文章總數：{rows.count()} 筆")

        for index in range(rows.count()):
            row = rows.nth(index)
        
            title_locator = row.locator(".title a")
            nrec_locator = row.locator(".nrec")
            author_locator = row.locator(".author")
            date_locator = row.locator(".date")

            if title_locator.count() > 0:
                title_value = clean_text(title_locator.inner_text())
                # 【修正網址】補上 PTT 的官方首頁前綴
                url_value = "https://www.ptt.cc" + title_locator.get_attribute("href")
            else:
                # 處理被刪除文章的狀況
                title_value = clean_text(row.locator(".title").inner_text())
                url_value = ""

            posts.append(
                {
                "nrec": clean_text(nrec_locator.inner_text()),
                "title": title_value,
                "author": clean_text(author_locator.inner_text()),
                "date": clean_text(date_locator.inner_text()),
                "url": url_value,
                }
            )

            cc += 1
            print(f"第 {cc} 筆抓取成功: {title_value}")

        if page_num < repeat_times:
            # 鎖定 PTT 上方按鈕群中的「‹ 上一頁」
            prev_btn = page.locator(".btn-group-paging a").nth(1)

            if prev_btn.count() > 0:
                # 2. 拿到它裡面的 href 網址
                prev_href = prev_btn.get_attribute("href")

                if prev_href:
                    next_page_url = "https://www.ptt.cc" + prev_href
                    print(f"【DEBUG】成功抓到上一頁網址: {next_page_url}")
                    print("【DEBUG】正在引導瀏覽器前往下一頁...")

                    # 3. 直接飛過去！
                    page.goto(next_page_url)

                    # 4. 強制讓程式睡 1 秒，等待新畫面渲染完畢
                    page.wait_for_timeout(1000)
                else:
                    print(
                        "【🚨 警告】抓到按鈕但裡面沒有超連結網址，停止翻頁！"
                    )
                    break
            else:
                print("【🚨 警告】找不到「‹ 上一頁」按鈕，停止翻頁！")
                break

    return posts

# 7.7 輸出 CSV
def write_csv(posts):
    fieldnames = ["nrec", "title", "author", "date", "url"]
    print(f"【DEBUG C】預計寫入的絕對路徑是：{OUTPUT_FILE.resolve()}")

    with OUTPUT_FILE.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(posts)
    print("【DEBUG D】檔案寫入完成！")

# 7.1 連到 Chrome，並寫入CSV檔
def main():
    print("【DEBUG E】主程式啟動，正在嘗試連接到 Chrome...")
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(CDP_URL)

        if not browser.contexts:
            raise RuntimeError("找不到 Chrome context，請確認 Chrome 是用 cdp.bat 啟動")
        
        context = browser.contexts[0]

        print("【DEBUG F】連線上 Chrome 了，準備取得分頁...")
        page = get_page(context)

        page.goto(GOSSIPING_URL)
        
        print("\n=== PTT 爬蟲準備中 ===")
        print("請先確認這個 Chrome 已經通過 Cloudflare 並登入 nopCommerce 後台。")
        input("【DEBUG G】確認登入完成後，回到終端機按  [Enter] 開始爬商品...")
        print("【DEBUG H】正在爬取文章資料並處理欄位...")
        posts = scrape_article(page)

        print(f"【DEBUG I】爬蟲結束，抓到 {len(posts)} 筆資料，準備寫入 CSV...")
        write_csv(posts)

        print(f"取得 {len(posts)} 筆八卦版資料")
        print(f"已輸出到 {OUTPUT_FILE}")

        print("🎉 執行成功！")
        browser.close()

if __name__ == "__main__":
    main()
