import os
import time
import emoji
import random
import pandas as pd
from glob import glob
from sqlite3 import connect
from datetime import datetime
from instaloader import Instaloader, Profile, ConnectionException

# ========== KONFIGURASI ==========
USERNAME = "dsrenaldi"
TARGET_USERNAME = "pdamsuryasembada"
COOKIE_PATH = "C:/Users/rdick/AppData/Roaming/Mozilla/Firefox/Profiles/xcv8f7jy.default-release-1/cookies.sqlite"
OUTPUT_FILE = f"trial_comments_{TARGET_USERNAME}.csv"
SHORTCODE_LOG = "shortcode_list.txt"
LOG_FILE = "log.txt"
MAX_POSTS_PER_SESSION = 10
DELAY_RANGE = (5, 10)

# ========== SETUP INSTALOADER ==========
print("🚀 Login menggunakan session Instaloader...")
instaloader = Instaloader(max_connection_attempts=1)

FIREFOXCOOKIEFILE = glob(os.path.expanduser(COOKIE_PATH))[0]
instaloader.context._session.cookies.update(
    connect(FIREFOXCOOKIEFILE)
    .execute("SELECT name, value FROM moz_cookies WHERE host='.instagram.com'")
)

try:
    username = instaloader.test_login()
    if not username:
        raise ConnectionException()
except ConnectionException:
    raise SystemExit("❌ Gagal login. Pastikan kamu sudah login di Firefox dan lolos verifikasi.")

instaloader.context.username = username
instaloader.save_session_to_file(USERNAME)
instaloader.load_session_from_file(USERNAME)

# ========== SIAPKAN FILE SHORTCODE DAN LOG ==========
if not os.path.exists(SHORTCODE_LOG):
    print("📄 Membuat file shortcode_list.txt...")
    open(SHORTCODE_LOG, 'w').close()

with open(SHORTCODE_LOG, 'r') as f:
    processed_shortcodes = set(line.strip() for line in f.readlines())

if not os.path.exists(LOG_FILE):
    open(LOG_FILE, 'w').close()

# ========== LOAD CSV KOMENTAR ==========
if os.path.exists(OUTPUT_FILE):
    print("📁 Melanjutkan dari file komentar sebelumnya...")
    df_existing = pd.read_csv(OUTPUT_FILE)
else:
    df_existing = pd.DataFrame(columns=[
        "post_shortcode", "post_date", "commenter_username", "comment_text", "comment_likes"
    ])

# ========== LOG FUNCTION ==========
def log_status(shortcode, total_comments, status):
    with open(LOG_FILE, 'a', encoding='utf-8') as log:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log.write(f"[{now}] Post: {shortcode} | Komentar: {total_comments} | Status: {status}\n")

# ========== MULAI SCRAPING ==========
print(f"📤 Mengambil postingan dari akun @{TARGET_USERNAME}...")
profile = Profile.from_username(instaloader.context, TARGET_USERNAME)

comments_data = []
processed = 0

try:
    for post in profile.get_posts():
        shortcode = post.shortcode

        # Cek apakah sudah diproses
        if shortcode in processed_shortcodes:
            print(f"[SKIP] Post {shortcode} sudah diambil sebelumnya.")
            continue

        print(f"[{processed + 1}] Scraping komentar dari post: {shortcode}")
        total = 0
        for comment in post.get_comments():
            comment_text = (emoji.demojize(comment.text)).encode('utf-8', errors='ignore').decode() if comment.text else ""
            comments_data.append({
                "post_shortcode": shortcode,
                "post_date": post.date_utc.strftime("%Y-%m-%d %H:%M:%S"),
                "commenter_username": comment.owner.username,
                "comment_text": comment_text,
                "comment_likes": comment.likes_count
            })
            total += 1

        # Simpan ke CSV
        if comments_data:
            df_new = pd.DataFrame(comments_data)
            df_existing = pd.concat([df_existing, df_new], ignore_index=True)
            df_existing.to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig')
            comments_data.clear()
            print(f"[SAVE] {total} komentar disimpan untuk post {shortcode}.")

        # Simpan shortcode
        with open(SHORTCODE_LOG, 'a') as f:
            f.write(shortcode + '\n')
        processed_shortcodes.add(shortcode)

        # Log sukses
        log_status(shortcode, total, "✅ Sukses")

        processed += 1
        if processed >= MAX_POSTS_PER_SESSION:
            print(f"\n🔒 Batas {MAX_POSTS_PER_SESSION} postingan tercapai.")
            break

        sleep_time = random.randint(*DELAY_RANGE)
        print(f"[WAIT] Menunggu {sleep_time} detik...")
        time.sleep(sleep_time)

except Exception as e:
    print(f"\n[ERROR] Terjadi kesalahan: {e}")
    log_status(shortcode, len(comments_data), f"❌ Gagal: {e}")
    if comments_data:
        df_new = pd.DataFrame(comments_data)
        df_existing = pd.concat([df_existing, df_new], ignore_index=True)
        df_existing.to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig')
        print("[SAVE] Data sementara berhasil disimpan.")

print("\n✅ Selesai. Semua data disimpan dan dicatat di log.")
