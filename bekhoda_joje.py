import telebot
import json
import random
import os
import pytz
from datetime import datetime
import schedule
import time
import threading

# توکن ربات بدون فاصله اضافی
TOKEN = '8100747572:AAElzdHLgMQefTjuZTX_x6PS92v4Gk0C43s'
bot = telebot.TeleBot(TOKEN)

# آیدی چنل
CHANNEL_ID = '@matashtashiokenkades'

# فایل ذخیره‌سازی کاربران
USERS_FILE = 'users.json'

# بارگذاری کاربران
def load_users():
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, 'r') as f:
        return json.load(f)

# ذخیره کاربران
def save_users(users):
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f)

users = load_users()

# لیست پست‌های کانال
channel_posts = list(range(1, 26))

# گرفتن تاریخ امروز به وقت تهران
def get_tehran_date():
    tehran = pytz.timezone('Asia/Tehran')
    now = datetime.now(tehran)
    return now.strftime('%Y-%m-%d')

# بررسی اینکه امروز کاربر چندتا عکس گرفته
def has_received_today(user_id):
    today = get_tehran_date()
    return users.get(user_id, {}).get('sent_today', {}).get(today, 0) >= 2

# ارسال عکس به کاربر و آپدیت شمارنده
def send_random_photo(user_id):
    sent = users[user_id]['sent']
    remaining = list(set(channel_posts) - set(sent))
    if not remaining:
        return
    post_id = random.choice(remaining)
    try:
        bot.forward_message(user_id, CHANNEL_ID, post_id)
        users[user_id]['sent'].append(post_id)
        users[user_id]['last_sent'] = get_tehran_date()

        today = get_tehran_date()
        if 'sent_today' not in users[user_id]:
            users[user_id]['sent_today'] = {}
        users[user_id]['sent_today'][today] = users[user_id]['sent_today'].get(today, 0) + 1

        save_users(users)
    except Exception as e:
        print(f"Error sending to {user_id}: {e}")

# پیام خوش‌آمد + بررسی تقلب
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = str(message.chat.id)
    if user_id not in users:
        users[user_id] = {'sent': [], 'last_sent': '', 'sent_today': {}}
    today = get_tehran_date()
    sent_count = users.get(user_id, {}).get('sent_today', {}).get(today, 0)

    if sent_count < 2:
        bot.send_message(message.chat.id, 'سلام دختر امیرحسین، الان حالت چطوره؟ الان عکستو میفرستم')
        send_random_photo(user_id)
    else:
        bot.send_message(message.chat.id, 'قرار نبود تقلب کنی دختر امیرحسین، امروز دوتا گرفتی دیگه بسته، فردا بیا دوباره 🦊🦋')

# پاسخ به پیام‌های خاص
@bot.message_handler(func=lambda msg: True)
def reply_to_thanks(message):
    user_id = str(message.chat.id)

    # فوروارد پیام به آیدی خاص
    if message.chat.id == 5801214694 and message.text != "/start":
        try:
            bot.forward_message(7017209038, message.chat.id, message.message_id)
        except Exception as e:
            print(f"خطا در فوروارد پیام: {e}")

    if user_id not in users:
        users[user_id] = {'sent': [], 'last_sent': '', 'sent_today': {}}
    save_users(users)

    print(f"[{datetime.now()}] پیام از {user_id}: {message.text}")

    if 'ممنون' in message.text:
        bot.reply_to(message, 'خواهش میکنم، خوشحالم که دختر امیرحسین رو خوشحال کردم')

# ارسال خودکار روزانه
def job():
    for user_id in users:
        if not has_received_today(user_id):
            send_random_photo(user_id)

def schedule_daily():
    schedule.every().day.at("08:00").do(job)
    while True:
        schedule.run_pending()
        time.sleep(30)

# اجرای ترد زمان‌بندی
threading.Thread(target=schedule_daily, daemon=True).start()

# اجرای ربات
print("من اینجام امیرحسین بریم دو تا جوجه نشون دخترت بدیم؟")
bot.infinity_polling()
