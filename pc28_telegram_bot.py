import os
import requests
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from apscheduler.schedulers.background import BackgroundScheduler

BOT_TOKEN = os.getenv("TG_BOT_TOKEN")
ADMIN_USER_ID = int(os.getenv("ADMIN_USER_ID", "0"))
FETCH_INTERVAL = int(os.getenv("FETCH_INTERVAL_SECONDS", "60"))

latest_draw = None

def fetch_pc28_once():
    global latest_draw
    url = "https://www.pc28668.com/"
    resp = requests.get(url, timeout=10)
    soup = BeautifulSoup(resp.text, "html.parser")
    issue_elem = soup.select_one(".kjjg span.issue")
    nums_elem = soup.select(".kjjg .num")
    if issue_elem and nums_elem:
        issue = issue_elem.text.strip()
        numbers = [n.text.strip() for n in nums_elem]
        if issue != latest_draw:
            latest_draw = issue
            return issue, numbers
    return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("PC28 BOT 已啟動，請使用 /subscribe 訂閱推播")

async def subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    context.application.user_data.setdefault("subs", set()).add(user_id)
    await update.message.reply_text("已訂閱 PC28 開獎推播")

async def unsubscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    context.application.user_data.setdefault("subs", set()).discard(user_id)
    await update.message.reply_text("已取消訂閱")

async def push_result(app):
    res = fetch_pc28_once()
    if res:
        issue, numbers = res
        subs = app.user_data.get("subs", set())
        for uid in subs:
            try:
                await app.bot.send_message(uid, f"第 {issue} 期開獎號碼: {', '.join(numbers)}")
            except:
                pass

if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("subscribe", subscribe))
    app.add_handler(CommandHandler("unsubscribe", unsubscribe))

    scheduler = BackgroundScheduler()
    scheduler.add_job(lambda: app.create_task(push_result(app)), "interval", seconds=FETCH_INTERVAL)
    scheduler.start()

    app.run_polling()
