# -*- coding: utf-8 -*-
# 建議在文件開頭加上編碼聲明

import os
import re
import requests
import argparse
import time
from urllib.parse import urlparse, unquote
from collections import defaultdict
import hashlib
import sys

# --- 配置 ---
# !! 請再次確認這些路徑是否為您專案的正確路徑 !!
DEFAULT_CONTENT_DIR = r"C:\Users\aweholy\Desktop\20250411gemini\hugo_site\content"
DEFAULT_STATIC_IMG_DIR = r"C:\Users\aweholy\Desktop\20250411gemini\hugo_site\static\images"

# 正則表達式匹配 i0, i1, i2.wp.com CDN URL
CDN_REGEX_PATTERN = r"https://i[0-2]\.wp\.com/"
# 原始網域
ORIGINAL_DOMAIN_PREFIX = "https://cmtc.tw"

REQUEST_DELAY = 0.1 # 可以稍微加快一點，但如果遇到問題再調回 0.2
REQUEST_TIMEOUT = 20
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}
# --- 配置結束 ---

# 全局字典，跟踪已處理的 URL 及其對應的本地 Hugo 路徑
# 值可能是 "/images/xxx.jpg" 或 None (如果下載失敗或跳過)
downloaded_images_map = defaultdict(lambda: None) # 預設值改為 None

# 編譯正則表達式以提高效率
markdown_image_regex = re.compile(r"!\[(?P<alt>.*?)\]\((?P<url>[^)]+?)(?:\s+[\"'](?P<title>.*?)[\"'])?\)")
html_image_regex = re.compile(r"<img\s+[^>]*?src\s*=\s*['\"](?P<url>[^'\"]+?)['\"][^>]*?>", re.IGNORECASE)
cdn_regex = re.compile(CDN_REGEX_PATTERN, re.IGNORECASE)

def sanitize_filename(url_path):
    """根據 URL 路徑清理並生成檔名"""
    # 從路徑中提取檔名部分
    filename = os.path.basename(url_path)
    # 解碼可能存在的 URL 編碼
    filename = unquote(filename)
    # 移除查詢參數 (? 後面的所有內容)
    filename = filename.split('?')[0]
    # 替換 Windows 不允許的字符為底線
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # 將一個或多個空格替換為單個連字符 '-'
    filename = re.sub(r'\s+', '-', filename)
    # 移除可能由替換產生的多個連續連字符
    filename = re.sub(r'-+', '-', filename)
    # 移除開頭或結尾的點、空格、連字符
    filename = filename.strip('. -')
    # 如果檔名變空 (例如原名只有特殊字符)，生成基於時間戳的 hash
    if not filename:
        filename = hashlib.md5(str(time.time()).encode()).hexdigest()[:10] + '.img'
    # 確保檔名不會太長 (考慮路徑總長度限制)
    max_len = 100 # 設定一個合理的檔名最大長度
    if len(filename) > max_len:
        name_part, ext_part = os.path.splitext(filename)
        # 確保即使截斷後仍保留副檔名
        name_part = name_part[:max_len - len(ext_part) - 1] # 預留空間給可能的後綴和點
        filename = name_part + ext_part
        print(f"    警告：檔名過長，已截斷為: {filename}")
    return filename

def get_unique_filepath(save_dir, filename):
    """獲取唯一文件儲存路徑，如果衝突則加後綴"""
    filepath = os.path.join(save_dir, filename)
    if not os.path.exists(filepath):
        return filepath, filename

    base, ext = os.path.splitext(filename)
    counter = 1
    # 限制檔名主體長度，為後綴 "-N" 預留空間
    max_base_len = 100 - len(ext) - 4 # -4 for "-999" approx.
    base = base[:max_base_len]

    while True:
        new_filename = f"{base}-{counter}{ext}"
        new_filepath = os.path.join(save_dir, new_filename)
        if not os.path.exists(new_filepath):
            print(f"    檔名衝突: '{filename}' -> 使用新檔名: '{new_filename}'")
            return new_filepath, new_filename
        counter += 1
        if counter > 999: # 設定一個上限防止無限循環
             print(f"    錯誤：嘗試了 999 次仍無法為 '{filename}' 找到唯一檔名，跳過。")
             return None, None

def download_image(image_url, save_dir):
    """下載圖片，返回成功下載後的 Hugo 相對路徑，否則返回 None"""
    original_url_to_map = image_url # 用原始 URL 作為 key 來記錄處理狀態

    # 檢查是否已經處理過 (無論成功失敗)
    if original_url_to_map in downloaded_images_map:
        return downloaded_images_map[original_url_to_map] # 返回之前記錄的結果 (可能是路徑，也可能是 None)

    print(f"  處理圖片 URL: {image_url}")

    # 判斷是否是目標 URL (CDN 或原始域)
    is_cdn = cdn_regex.match(image_url)
    is_original = image_url.startswith(ORIGINAL_DOMAIN_PREFIX)

    if not (is_cdn or is_original):
        # print(f"    跳過非目標 URL: {image_url}")
        downloaded_images_map[original_url_to_map] = None # 標記為已處理但跳過
        return None

    # 提取用於生成檔名的路徑部分
    try:
        parsed_url = urlparse(image_url)
        path_part_for_filename = parsed_url.path
    except ValueError:
        print(f"    錯誤：無法解析 URL: {image_url}")
        downloaded_images_map[original_url_to_map] = None
        return None

    if not path_part_for_filename:
        print(f"    錯誤：URL 中缺少路徑部分: {image_url}")
        downloaded_images_map[original_url_to_map] = None
        return None

    # 稍微延遲
    time.sleep(REQUEST_DELAY)

    try:
        # 直接使用找到的 URL (CDN 或 原始域) 進行下載
        response = requests.get(image_url, headers=HEADERS, stream=True, timeout=REQUEST_TIMEOUT)
        response.raise_for_status() # 檢查 HTTP 錯誤

        # 清理檔名
        clean_filename = sanitize_filename(path_part_for_filename)

        # 確保儲存目錄存在
        os.makedirs(save_dir, exist_ok=True)

        # 獲取唯一儲存路徑
        save_filepath, unique_filename = get_unique_filepath(save_dir, clean_filename)

        if not save_filepath: # 無法獲取唯一路徑，標記失敗
            downloaded_images_map[original_url_to_map] = None
            return None

        # 下載文件
        print(f"    正在下載到: {save_filepath}")
        with open(save_filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"    下載完成.")

        # 生成 Hugo 使用的根相對路徑
        hugo_relative_path = f"/images/{unique_filename}".replace(os.sep, '/')
        downloaded_images_map[original_url_to_map] = hugo_relative_path # 記錄成功結果
        return hugo_relative_path

    except requests.exceptions.RequestException as e:
        print(f"    錯誤：下載圖片失敗 {image_url}: {e}")
        downloaded_images_map[original_url_to_map] = None # 記錄失敗
        return None
    except Exception as e:
        print(f"    錯誤：處理圖片時發生未知錯誤 {image_url}: {e}")
        downloaded_images_map[original_url_to_map] = None # 記錄失敗
        return None

def process_markdown_file(filepath, save_dir, dry_run=True):
    """處理單個 Markdown 文件"""
    print(f"\n處理文件: {os.path.relpath(filepath, os.path.dirname(DEFAULT_CONTENT_DIR))}") # 顯示相對路徑
    encodings_to_try = ['utf-8', 'gbk', 'big5'] # 嘗試不同編碼
    content = None
    original_encoding = 'utf-8'

    # 嘗試讀取文件
    for enc in encodings_to_try:
        try:
            with open(filepath, 'r', encoding=enc) as f:
                content = f.read()
            original_encoding = enc
            break
        except UnicodeDecodeError:
            continue
        except Exception as e:
            print(f"  讀取文件時發生錯誤 ({enc}): {e}")
            return False, 0 # 返回修改狀態和替換數量

    if content is None:
        print(f"  錯誤：嘗試所有編碼後仍無法讀取文件，跳過。")
        return False, 0

    modified_in_this_file = False
    replacements_in_this_file = 0
    replacements_map = {} # key: old_url, value: new_hugo_path

    # 查找所有可能的圖片 URL (Markdown + HTML)
    urls_in_file = set()
    for match in markdown_image_regex.finditer(content):
        urls_in_file.add(match.group('url').strip())
    for match in html_image_regex.finditer(content):
        urls_in_file.add(match.group('url').strip())

    # 處理每個 URL
    for url in urls_in_file:
        # 檢查是否是目標 URL (CDN 或 原始域)
        if cdn_regex.match(url) or url.startswith(ORIGINAL_DOMAIN_PREFIX):
            new_hugo_path = download_image(url, save_dir)
            if new_hugo_path: # 下載成功或之前已成功
                replacements_map[url] = new_hugo_path
            # 如果 new_hugo_path 是 None, 表示下載失敗或跳過, 不加入替換列表

    # 如果有需要替換的內容
    if replacements_map:
        print(f"  找到 {len(replacements_map)} 個需處理的連結...")
        new_content = content
        current_file_replace_count = 0

        for old_url, new_url in replacements_map.items():
            # 記錄準備替換
            # print(f"    準備替換: '{old_url}' -> '{new_url}'")

            # 執行精確替換 (使用正則確保邊界)
            # 處理 Markdown: ![alt](url) 或 ![alt](url "title")
            # 增加對 URL 前後可能存在的空格的處理 (\s*)
            markdown_pattern = r'(!\[.*?\]\(\s*)' + re.escape(old_url) + r'(\s*(?:[\'\"].*?[\'\""\'])?\))'
            count_before = new_content.count(old_url) # 粗略計數
            new_content = re.sub(markdown_pattern, r'\1' + new_url + r'\2', new_content)
            count_after = new_content.count(old_url) # 粗略計數

            # 處理 HTML: src="url" or src='url'
            html_pattern = r'(<img\s+[^>]*?src\s*=\s*[\'\"])' + re.escape(old_url) + r'([\'\"][^>]*?>)'
            new_content = re.sub(html_pattern, r'\1' + new_url + r'\2', new_content, flags=re.IGNORECASE)
            count_final = new_content.count(old_url)

            replace_occurrences = count_before - count_final
            if replace_occurrences > 0:
                print(f"    已準備替換 '{os.path.basename(urlparse(old_url).path)}' -> '{new_url}' ({replace_occurrences} 處)")
                current_file_replace_count += replace_occurrences


        # 檢查內容是否真的發生了變化
        if new_content != content:
            modified_in_this_file = True
            print(f"  => 文件內容已準備更新 ({current_file_replace_count} 處替換)。")
            if not dry_run:
                try:
                    with open(filepath, 'w', encoding=original_encoding) as f:
                        f.write(new_content)
                    print(f"  => 成功更新文件!")
                except Exception as e:
                    print(f"  => 錯誤：寫入文件失敗: {e}")
                    modified_in_this_file = False # 標記為未成功
            else:
                 print("     (試運行 - 未實際寫入)")
        else:
             print("  內容無需更新 (可能替換未匹配或已完成)。")

    return modified_in_this_file, replacements_in_this_file # 返回是否修改及替換數量

# --- 主程式入口 ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=f"掃描 Hugo content 目錄下的 .md 文件，下載來自 CDN ({CDN_REGEX_PATTERN}) 或原始域 ({ORIGINAL_DOMAIN_PREFIX}) 的圖片到 static/images，並更新連結。")
    parser.add_argument("--content-dir", default=DEFAULT_CONTENT_DIR, help=f"Hugo content 目錄的路徑 (預設: {DEFAULT_CONTENT_DIR})")
    parser.add_argument("--img-dir", default=DEFAULT_STATIC_IMG_DIR, help=f"Hugo static/images 目錄的路徑 (預設: {DEFAULT_STATIC_IMG_DIR})")
    parser.add_argument("--run", action="store_true", help="實際執行下載和文件修改操作（預設為試運行）。請務必先試運行並備份！")

    args = parser.parse_args()
    content_directory = os.path.abspath(args.content_dir)
    static_images_directory = os.path.abspath(args.img_dir)
    is_dry_run = not args.run

    print("=" * 50)
    print("Hugo 圖片本地化腳本 (v2 - 支援 CDN)")
    print("=" * 50)
    print(f"Content 目錄: {content_directory}")
    print(f"圖片儲存目錄: {static_images_directory}")
    print(f"目標網域模式: CDN ({CDN_REGEX_PATTERN}) 或 原始域 ({ORIGINAL_DOMAIN_PREFIX})")
    print(f"試運行模式: {'啟用' if is_dry_run else '禁用 (將實際操作!)'}")
    print("-" * 50)

    # 檢查路徑
    if not os.path.isdir(content_directory):
        print(f"錯誤：Content 目錄不存在: {content_directory}")
        sys.exit(1)
    if not os.path.isdir(os.path.dirname(static_images_directory)):
         print(f"錯誤：圖片儲存目錄的上層目錄 (通常是 static) 不存在: {os.path.dirname(static_images_directory)}")
         sys.exit(1)
    os.makedirs(static_images_directory, exist_ok=True) # 確保 images 目錄存在

    # 實際運行前確認
    if not is_dry_run:
        confirm = input("警告：您已禁用試運行模式！\n"
                        "腳本將會下載圖片並直接修改您的 .md 文件。\n"
                        "強烈建議您在繼續操作前已完整備份專案。\n"
                        "輸入 'yes' 確認執行實際操作: ")
        if confirm.lower() != 'yes':
            print("操作已由用戶取消。")
            sys.exit(0)
        print("-" * 30 + "\n") # 分隔線

    # 初始化計數器
    total_files_processed = 0
    total_files_modified = 0
    total_replacements_made = 0 # 計算總替換次數

    # 遍歷文件並處理
    for dirpath, dirnames, filenames in os.walk(content_directory):
        for filename in filenames:
            if filename.lower().endswith(".md"):
                total_files_processed += 1
                filepath = os.path.join(dirpath, filename)
                was_modified, replacements_count = process_markdown_file(filepath, static_images_directory, is_dry_run)
                if was_modified:
                    total_files_modified += 1
                    # 注意: process_markdown_file 目前返回的 replacements_count 可能不準確, 先不累加
                    # total_replacements_made += replacements_count

    # 打印最終總結
    print("\n" + "=" * 50)
    print("處理完成。")
    print(f"總共處理的 Markdown 文件數: {total_files_processed}")
    successful_downloads = len([p for p in downloaded_images_map.values() if p])
    failed_or_skipped = len(downloaded_images_map) - successful_downloads

    if is_dry_run:
        print(f"檢測到並計劃修改的文件數: {total_files_modified}")
        print(f"檢測到並計劃下載的圖片 URL 數量 (包括已處理): {len(downloaded_images_map)}")
        # print(f"預計替換的總次數: {total_replacements_made}") # 替換次數統計可能不準
        print("試運行結束。未做實際更改。")
    else:
        print(f"成功修改的文件數: {total_files_modified}")
        print(f"成功下載並記錄的圖片數量: {successful_downloads}")
        print(f"下載失敗或跳過的圖片數量: {failed_or_skipped}")
        # print(f"實際替換的總次數: {total_replacements_made}")
        print("文件修改和圖片下載過程結束。")