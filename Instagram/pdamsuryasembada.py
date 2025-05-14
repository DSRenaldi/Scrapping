from glob import glob
from os.path import expanduser
from sqlite3 import connect
import emoji
import pandas as pd
from instaloader import ConnectionException, Instaloader, Post, Profile

# --- Setup Instaloader ---
instaloader = Instaloader(max_connection_attempts=1)

# --- Ambil cookie dari Firefox ---
cookie_path = "C:/Users/rdick/AppData/Roaming/Mozilla/Firefox/Profiles/xcv8f7jy.default-release-1/cookies.sqlite"
FIREFOXCOOKIEFILE = glob(expanduser(cookie_path))[0]

# --- Inject cookie ke session Instaloader ---
instaloader.context._session.cookies.update(
    connect(FIREFOXCOOKIEFILE)
    .execute("SELECT name, value FROM moz_cookies WHERE host='.instagram.com'")
)

# --- Coba login ---
try:
    username = instaloader.test_login()
    if not username:
        raise ConnectionException()
except ConnectionException:
    raise SystemExit("Cookie import failed. Are you logged in successfully in Firefox?")

instaloader.context.username = username
instaloader.save_session_to_file()
instaloader.load_session_from_file("dsrenaldi")

# --- Ambil profil target ---
TARGET_USERNAME = 'pdamsuryasembada'
profile = Profile.from_username(instaloader.context, TARGET_USERNAME)

# --- Ambil komentar dari semua post ---
comments_data = []
print(f"Mengambil postingan dari @{TARGET_USERNAME}...")

for post in profile.get_posts():
    print(f"Post: {post.shortcode} - Mengambil komentar...")
    for comment in post.get_comments():
        comment_text = (emoji.demojize(comment.text)).encode('utf-8', errors='ignore').decode() if comment.text else ""
        comments_data.append({
            "post_shortcode": post.shortcode,
            "post_date": post.date_utc.strftime("%Y-%m-%d %H:%M:%S"),
            "commenter_username": comment.owner.username,
            "comment_text": comment_text,
            "comment_likes": comment.likes_count
        })

# --- Simpan ke CSV ---
df = pd.DataFrame(comments_data)
df.to_csv(f"comments_{TARGET_USERNAME}.csv", index=False, encoding='utf-8-sig')
print(f"Berhasil menyimpan semua komentar ke comments_{TARGET_USERNAME}.csv")