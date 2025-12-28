import os
import requests
import uuid
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes
)

BOT_TOKEN = os.getenv("8492229745:AAG0Sw07aMATxWLHy2C1AMPsvdfjFsmC3nY")
MAILTM_API = "https://api.mail.tm"

users = {}  # chat_id -> {email, password, token}

# ---------------- Mail.tm helpers ----------------

def create_mail_account():
    domains = requests.get(f"{MAILTM_API}/domains").json()["hydra:member"]
    domain = domains[0]["domain"]

    email = f"{uuid.uuid4()}@{domain}"
    password = str(uuid.uuid4())

    requests.post(
        f"{MAILTM_API}/accounts",
        json={"address": email, "password": password}
    )

    token_res = requests.post(
        f"{MAILTM_API}/token",
        json={"address": email, "password": password}
    ).json()

    return {
        "email": email,
        "password": password,
        "token": token_res["token"]
    }

def get_messages(token):
    res = requests.get(
        f"{MAILTM_API}/messages",
        headers={"Authorization": f"Bearer {token}"}
    ).json()
    return res["hydra:member"]

def read_message(msg_id, token):
    res = requests.get(
        f"{MAILTM_API}/messages/{msg_id}",
        headers={"Authorization": f"Bearer {token}"}
    ).json()
    return res

# ---------------- Telegram commands ----------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📧 Temp Mail Bot Ready\n\n"
        "/newmail - create temp mail\n"
        "/inbox - check inbox\n"
        "/read <id> - read mail"
    )

async def newmail(update: Update, context: ContextTypes.DEFAULT_TYPE):
    acc = create_mail_account()
    users[update.effective_chat.id] = acc

    await update.message.reply_text(
        f"✅ New Temp Mail Created\n\n"
        f"📧 {acc['email']}"
    )

async def inbox(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = users.get(update.effective_chat.id)
    if not user:
        await update.message.reply_text("❌ First create mail: /newmail")
        return

    mails = get_messages(user["token"])
    if not mails:
        await update.message.reply_text("📭 Inbox empty")
        return

    text = "📥 Inbox:\n\n"
    for m in mails:
        text += (
            f"🆔 {m['id']}\n"
            f"From: {m['from']['address']}\n"
            f"Subject: {m['subject']}\n\n"
        )

    await update.message.reply_text(text)

async def read(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = users.get(update.effective_chat.id)
    if not user:
        await update.message.reply_text("❌ No active mail")
        return

    if not context.args:
        await update.message.reply_text("❌ Usage: /read <id>")
        return

    msg = read_message(context.args[0], user["token"])
    await update.message.reply_text(
        f"📨 {msg['subject']}\n\n{msg['text']}"
    )

# ---------------- Main ----------------

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("newmail", newmail))
    app.add_handler(CommandHandler("inbox", inbox))
    app.add_handler(CommandHandler("read", read))

    app.run_polling()

if __name__ == "__main__":
    main()
