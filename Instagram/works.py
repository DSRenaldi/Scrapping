from glob import glob
from os.path import expanduser
from sqlite3 import connect
import argparse
import pathlib
import sys
import csv
import time
import emoji
from glob import glob
from os.path import expanduser
from sqlite3 import connect
import os.path
import pandas as pd
from datetime import datetime
from matplotlib import pyplot as plt
from instaloader import ConnectionException, Instaloader, Post
from textblob import TextBlob

instagram =Instaloader()

## only allow one attempt for session connection
instaloader = Instaloader(max_connection_attempts=1)

path_to_firefox_cookies = "C:/Users/rdick/AppData/Roaming/Mozilla/Firefox/Profiles/xcv8f7jy.default-release-1/cookies.sqlite"
FIREFOXCOOKIEFILE = glob(expanduser(path_to_firefox_cookies))[0]


## get cookie id for instagram
instaloader.context._session.cookies.update(connect(FIREFOXCOOKIEFILE)
                                            .execute("SELECT name, value FROM moz_cookies "
                                                     "WHERE host='.instagram.com'"))
## check connection
try:
    username = instaloader.test_login()
    if not username:
        raise ConnectionException()
except ConnectionException:
    raise SystemExit("Cookie import failed. Are you logged in successfully in Firefox?")

instaloader.context.username = username

## save session to instaloader file for later use
instaloader.save_session_to_file()

## login to saved session
instagram.load_session_from_file("dsrenaldi")

## direct instaloader to correct post using it's shortcode
SHORTCODE = 'CV5WqggMDCb'
post = Post.from_shortcode(instagram.context, SHORTCODE)

## get comment metadata from the post
comments_data  = []
for x in post.get_comments():
    comment_text = (emoji.demojize(x.text)).encode('utf-8', errors='ignore').decode() if x.text else ""
    comments_data.append({
        "post_shortcode": post.shortcode,
        "commenter_username": x.owner.username,
        "comment_text": comment_text,
        "comment_likes": x.likes_count
    })

# for x in post.get_comments():
#         post_info = {
#         "post_shortcode":post.shortcode,
#         "commenter_username": x.owner,
#         "comment_text": (emoji.demojize(x.text)).encode('utf-8', errors='ignore').decode() if x.text else "",
#         "comment_likes": x.likes_count
#         }

df = pd.DataFrame(comments_data)
df.to_csv("instagram_comments.csv", index=False, encoding='utf-8-sig')
print("Komentar berhasil disimpan ke instagram_comments.csv")