import os
import time
import emoji
import random
import pandas as pd
from glob import glob
from sqlite3 import connect
from instaloader import Instaloader, Profile, ConnectionException
from datetime import datetime

# ========== KONFIGURASI ==========
USERNAME = "dickysyarif123"
TARGET_USERNAME = "pdamsuryasembada"
COOKIE_PATH = "C:/Users/rdick/AppData/Roaming/Mozilla/Firefox/Profiles/xcv8f7jy.default-release-1/cookies.sqlite"
OUTPUT_FILE = f"trial_comments_{TARGET_USERNAME}.csv"
SHORTCODE_FILE = "shortcode_list.txt"
LOG_FILE = "log.txt"
MAX_POSTS_PER_SESSION = 10
MAX_SESSIONS = 10
SESSION_DELAY = (60, 90)
DEFAULT_DELAY_RANGE = (5, 10)
FAST_DELAY_RANGE = (3, 5)
SHORTCODE_THRESHOLD = 100

# ========== FUNGSI UTILITAS ==========
def log_status(shortcode, total_comments, status):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a", encoding="utf-8") as log:
        log.write(f"[{now}] Post: {shortcode} | Komentar: {total_comments} | Status: {status}\n")

def load_existing_shortcodes():
    if os.path.exists(SHORTCODE_FILE):
        with open(SHORTCODE_FILE, "r", encoding="utf-8") as f:
            return set(line.strip() for line in f)
    else:
        open(SHORTCODE_FILE, "w", encoding="utf-8").close()
        return set()

def save_shortcode(shortcode):
    with open(SHORTCODE_FILE, "a", encoding="utf-8") as f:
        f.write(f"{shortcode}\n")

def append_to_csv(data, output_file):
    df = pd.DataFrame(data)
    if os.path.exists(output_file):
        df.to_csv(output_file, mode='a', index=False, header=False, encoding='utf-8-sig')
    else:
        df.to_csv(output_file, index=False, encoding='utf-8-sig')

def get_delay_range(current_count):
    return FAST_DELAY_RANGE if current_count >= SHORTCODE_THRESHOLD else DEFAULT_DELAY_RANGE

# ========== SETUP INSTALOADER ==========
print("🔐 Memulai Instaloader dan login...")
instaloader = Instaloader(max_connection_attempts=1)
session_file = f"session-{USERNAME}"

try:
    if os.path.exists(session_file):
        instaloader.load_session_from_file(USERNAME)
        print(f"✅ Berhasil login menggunakan file sesi: {session_file}")
    else:
        # Gunakan cookie Firefox
        cookie_file = glob(os.path.expanduser(COOKIE_PATH))[0]
        instaloader.context._session.cookies.update(
            connect(cookie_file)
            .execute("SELECT name, value FROM moz_cookies WHERE host='.instagram.com'")
        )
        username = instaloader.test_login()
        if not username:
            raise ConnectionException()
        instaloader.context.username = username
        instaloader.save_session_to_file(USERNAME)
        print("✅ Login berhasil dan sesi disimpan.")

except ConnectionException:
    raise SystemExit("❌ Gagal login. Pastikan sudah login ke Instagram di Firefox.")

# ========== MULAI SCRAPING ==========
print(f"📸 Memulai scraping komentar dari akun @{TARGET_USERNAME}")
profile = Profile.from_username(instaloader.context, TARGET_USERNAME)
existing_shortcodes = load_existing_shortcodes()
sessions_completed = 0
post_iterator = profile.get_posts()

while sessions_completed < MAX_SESSIONS:
    print(f"\n🚀 Sesi #{sessions_completed + 1} dimulai...")
    processed = 0
    comments_data = []

    try:
        while processed < MAX_POSTS_PER_SESSION:
            try:
                post = next(post_iterator)
            except StopIteration:
                print("\n✅ Semua postingan sudah diproses.")
                break

            shortcode = post.shortcode

            # Delay pengecekan
            delay_range = get_delay_range(len(existing_shortcodes))
            sleep_time = random.randint(*delay_range)
            print(f"[CHECK] Tidur {sleep_time} detik sebelum memeriksa shortcode...")
            time.sleep(sleep_time)

            if shortcode in existing_shortcodes:
                print(f"[SKIP] Post {shortcode} sudah diproses.")
                continue

            print(f"[{processed + 1}] Mengambil komentar dari post: {shortcode}")
            try:
                for comment in post.get_comments():
                    comment_text = emoji.demojize(comment.text) if comment.text else ""
                    comments_data.append({
                        "post_shortcode": shortcode,
                        "post_date": post.date_utc.strftime("%Y-%m-%d %H:%M:%S"),
                        "commenter_username": comment.owner.username,
                        "comment_text": comment_text.encode('utf-8', errors='ignore').decode(),
                        "comment_likes": comment.likes_count
                    })

                total_comments = len(comments_data)

                append_to_csv(comments_data, OUTPUT_FILE)
                save_shortcode(shortcode)
                existing_shortcodes.add(shortcode)
                log_status(shortcode, total_comments, "Sukses")
                print(f"[SAVE] Komentar dari post {shortcode} disimpan. Jumlah komentar: {total_comments}")
                comments_data.clear()

            except Exception as e:
                log_status(shortcode, len(comments_data), f"Gagal: {e}")
                print(f"[ERROR] Gagal memproses {shortcode}: {e}")

            processed += 1
            post_sleep = random.randint(*DEFAULT_DELAY_RANGE)
            print(f"[WAIT] Tidur selama {post_sleep} detik sebelum post berikutnya...")
            time.sleep(post_sleep)

        sessions_completed += 1

        if sessions_completed < MAX_SESSIONS:
            pause_time = random.randint(*SESSION_DELAY)
            print(f"\n[PAUSE] Tidur {pause_time} detik sebelum sesi berikutnya...\n")
            time.sleep(pause_time)

    except StopIteration:
        print("\n✅ Semua postingan sudah diproses.")
        break

print("\n🎉 Proses scraping selesai.")
