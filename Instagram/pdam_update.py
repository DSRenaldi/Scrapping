import os
import time
import emoji
import random
import pandas as pd
from glob import glob
from sqlite3 import connect
from instaloader import Instaloader, Profile, ConnectionException

# ========== KONFIGURASI ==========
USERNAME = "dsrenaldi"
TARGET_USERNAME = "pdamsuryasembada"
COOKIE_PATH = "C:/Users/rdick/AppData/Roaming/Mozilla/Firefox/Profiles/xcv8f7jy.default-release-1/cookies.sqlite"
OUTPUT_FILE = f"comments_{TARGET_USERNAME}.csv"
MAX_POSTS_PER_SESSION = 10
DELAY_RANGE = (5, 10)  # delay acak antara 5 sampai 10 detik

# ========== SETUP INSTALOADER ==========
print("Memulai Instaloader dan login...")
instaloader = Instaloader(max_connection_attempts=1)

# Gunakan cookie dari Firefox
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
    raise SystemExit("Gagal login. Pastikan kamu sudah login di Firefox dan lolos verifikasi.")

instaloader.context.username = username
instaloader.save_session_to_file(USERNAME)
instaloader.load_session_from_file(USERNAME)

# ========== CEK PROGRES SEBELUMNYA ==========
existing_shortcodes = set()
if os.path.exists(OUTPUT_FILE):
    print("Melanjutkan dari file sebelumnya...")
    df_existing = pd.read_csv(OUTPUT_FILE)
    existing_shortcodes = set(df_existing['post_shortcode'].unique())
else:
    df_existing = pd.DataFrame(columns=[
        "post_shortcode", "post_date", "commenter_username", "comment_text", "comment_likes"
    ])

# ========== SCRAPE KOMENTAR ==========
print(f"Mengambil data dari akun @{TARGET_USERNAME}...")
profile = Profile.from_username(instaloader.context, TARGET_USERNAME)

comments_data = []
processed = 0

try:
    for post in profile.get_posts():
        if post.shortcode in existing_shortcodes:
            print(f"[SKIP] {post.shortcode} sudah diproses.")
            continue

        print(f"[{processed+1}] Mengambil komentar dari post: {post.shortcode}...")
        for comment in post.get_comments():
            comment_text = (emoji.demojize(comment.text)).encode('utf-8', errors='ignore').decode() if comment.text else ""
            comments_data.append({
                "post_shortcode": post.shortcode,
                "post_date": post.date_utc.strftime("%Y-%m-%d %H:%M:%S"),
                "commenter_username": comment.owner.username,
                "comment_text": comment_text,
                "comment_likes": comment.likes_count
            })

        # Simpan hasil sementara
        if comments_data:
            df_new = pd.DataFrame(comments_data)
            df_existing = pd.concat([df_existing, df_new], ignore_index=True)
            df_existing.to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig')
            comments_data.clear()
            print(f"[SAVE] Data dari post {post.shortcode} disimpan.")

        processed += 1
        if processed >= MAX_POSTS_PER_SESSION:
            print(f"\n🔒 Sesi selesai: batas {MAX_POSTS_PER_SESSION} postingan tercapai.")
            break

        sleep_time = random.randint(*DELAY_RANGE)
        print(f"[WAIT] Menunggu {sleep_time} detik sebelum post berikutnya...")
        time.sleep(sleep_time)

except Exception as e:
    print(f"\n[ERROR] Proses dihentikan: {e}")
    if comments_data:
        df_new = pd.DataFrame(comments_data)
        df_existing = pd.concat([df_existing, df_new], ignore_index=True)
        df_existing.to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig')
        print("[SAVE] Data sementara berhasil disimpan.")

print("\n✅ Selesai. Data komentar sesi ini berhasil disimpan.")
