import os
import time
import emoji
import pandas as pd
from glob import glob
from sqlite3 import connect
from instaloader import Instaloader, Profile, ConnectionException, Post

# ========== KONFIGURASI ==========
USERNAME = "dsrenaldi"  # nama file session
TARGET_USERNAME = "pdamsuryasembada"
COOKIE_PATH = "C:/Users/rdick/AppData/Roaming/Mozilla/Firefox/Profiles/xcv8f7jy.default-release-1/cookies.sqlite"
OUTPUT_FILE = f"comments_{TARGET_USERNAME}.csv"
DELAY_BETWEEN_POSTS = 5  # detik
LIMIT_POSTS = None  # atur ke int (misal 50) untuk uji coba

# ========== LOAD / BUAT SESSION ==========
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

# ========== RESUME JIKA SUDAH ADA FILE ==========
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

try:
    for i, post in enumerate(profile.get_posts()):
        if LIMIT_POSTS and i >= LIMIT_POSTS:
            break

        if post.shortcode in existing_shortcodes:
            print(f"[SKIP] {post.shortcode} sudah diproses.")
            continue

        print(f"[{i+1}] Mengambil komentar dari post: {post.shortcode}...")
        for comment in post.get_comments():
            comment_text = (emoji.demojize(comment.text)).encode('utf-8', errors='ignore').decode() if comment.text else ""
            comments_data.append({
                "post_shortcode": post.shortcode,
                "post_date": post.date_utc.strftime("%Y-%m-%d %H:%M:%S"),
                "commenter_username": comment.owner.username,
                "comment_text": comment_text,
                "comment_likes": comment.likes_count
            })

        # Simpan per postingan
        if comments_data:
            df_new = pd.DataFrame(comments_data)
            df_existing = pd.concat([df_existing, df_new], ignore_index=True)
            df_existing.to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig')
            comments_data.clear()
            print(f"[SAVE] Disimpan ke {OUTPUT_FILE}")
        
        time.sleep(DELAY_BETWEEN_POSTS)

except Exception as e:
    print(f"\n[ERROR] Proses dihentikan: {e}")
    if comments_data:
        df_new = pd.DataFrame(comments_data)
        df_existing = pd.concat([df_existing, df_new], ignore_index=True)
        df_existing.to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig')
        print("[SAVE] Data sementara berhasil disimpan.")

print("\n✅ Selesai. Semua data komentar berhasil diambil dan disimpan.")
