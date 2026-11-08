import json
import os
import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes, ConversationHandler
)

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
DATA_FILE = "groups_data.json"

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

AWAITING_GROUP_LINK, AWAITING_GROUP_NAME, AWAITING_VIDEO_URL = range(3)

DEFAULT_GROUPS = [
    {"name": "YouTube Creators Network", "link": "https://t.me/youtubecreators", "niche": "YouTube", "added": "preset"},
    {"name": "SEO & Digital Marketing", "link": "https://t.me/seodigitalmarketing", "niche": "SEO/Marketing", "added": "preset"},
    {"name": "Video Marketing Hub", "link": "https://t.me/videomarketinghub", "niche": "Video", "added": "preset"},
    {"name": "YouTube Growth Community", "link": "https://t.me/ytgrowth", "niche": "YouTube", "added": "preset"},
    {"name": "Digital Marketers UK", "link": "https://t.me/digitalmarketersuk", "niche": "UK Marketing", "added": "preset"},
    {"name": "Content Creators", "link": "https://t.me/contentcreatorshub", "niche": "Content", "added": "preset"},
    {"name": "Promote YouTube Videos", "link": "https://t.me/promoteyoutube", "niche": "YouTube Promo", "added": "preset"},
    {"name": "Social Media Marketing", "link": "https://t.me/socialmediamarketinggroup", "niche": "Social Media", "added": "preset"},
    {"name": "YouTube Subscribers Exchange", "link": "https://t.me/ytsubsexchange", "niche": "YouTube Growth", "added": "preset"},
    {"name": "Viral Content Sharing", "link": "https://t.me/viralcontentsharing", "niche": "Viral/Content", "added": "preset"},
]

def load_data():
    if not os.path.exists(DATA_FILE):
        return {"groups": DEFAULT_GROUPS.copy(), "shares": [], "keywords": ["YouTube", "digital marketing", "SEO"]}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "Welcome to YouTube Group Finder Bot!\n\n"
        "Commands:\n"
        "/groups - View all saved groups\n"
        "/addgroup - Add a new group\n"
        "/share - Log a video share\n"
        "/history - View your sharing history\n"
        "/find keyword - Search for new groups\n"
        "/stats - Your sharing stats"
    )
    await update.message.reply_text(text)

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start(update, context)

async def list_groups(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    groups = data["groups"]
    if not groups:
        await update.message.reply_text("No groups saved yet. Use /addgroup to add one.")
        return
    niches = {}
    for g in groups:
        niche = g.get("niche", "General")
        niches.setdefault(niche, []).append(g)
    text = f"Your Groups ({len(groups)} total)\n\n"
    for niche, grps in niches.items():
        text += f"{niche}:\n"
        for g in grps:
            text += f"- {g['name']}: {g['link']}\n"
        text += "\n"
    keyboard = [[InlineKeyboardButton("Add New Group", callback_data="addgroup")], [InlineKeyboardButton("Log a Share", callback_data="share")]]
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), disable_web_page_preview=True)

async def find_groups(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyword = " ".join(context.args) if context.args else "YouTube digital marketing"
    kw = keyword.replace(" ", "+")
    text = f"Finding groups for: {keyword}\n\nTGStat: https://tgstat.com/search?q={kw}\nTelemetrio: https://telemetr.io/en/channels?channel={kw}\nTelegramChannels: https://telegramchannels.me/groups?search={kw}\n\nUse /addgroup to save a group!"
    await update.message.reply_text(text, disable_web_page_preview=True)

async def addgroup_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.message.reply_text("Send me the Telegram group link (e.g. https://t.me/groupname):")
    else:
        await update.message.reply_text("Send me the Telegram group link (e.g. https://t.me/groupname):")
    return AWAITING_GROUP_LINK

async def receive_group_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    link = update.message.text.strip()
    if not link.startswith("https://t.me/") and not link.startswith("@"):
        await update.message.reply_text("Please send a valid Telegram link (https://t.me/...) or @username")
        return AWAITING_GROUP_LINK
    context.user_data["new_group_link"] = link
    await update.message.reply_text("Now send me a name for this group:")
    return AWAITING_GROUP_NAME

async def receive_group_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text.strip()
    keyboard = [[InlineKeyboardButton("YouTube", callback_data="niche_YouTube"), InlineKeyboardButton("Marketing", callback_data="niche_Marketing")], [InlineKeyboardButton("SEO", callback_data="niche_SEO"), InlineKeyboardButton("General", callback_data="niche_General")]]
    context.user_data["new_group_name"] = name
    await update.message.reply_text("What niche/category is this group?", reply_markup=InlineKeyboardMarkup(keyboard))
    return ConversationHandler.END

async def niche_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    niche = query.data.replace("niche_", "")
    name = context.user_data.get("new_group_name", "Unknown")
    link = context.user_data.get("new_group_link", "")
    data = load_data()
    data["groups"].append({"name": name, "link": link, "niche": niche, "added": datetime.now().strftime("%Y-%m-%d")})
    save_data(data)
    await query.message.reply_text(f"Group saved! Name: {name}, Niche: {niche}. Use /groups to see all.")

async def share_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query:
        await update.callback_query.answer()
        msg = update.callback_query.message
    else:
        msg = update.message
    await msg.reply_text("Paste your YouTube video URL:")
    return AWAITING_VIDEO_URL

async def receive_video_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    if "youtube.com" not in url and "youtu.be" not in url:
        await update.message.reply_text("Please send a valid YouTube URL.")
        return AWAITING_VIDEO_URL
    data = load_data()
    groups = data["groups"]
    if not groups:
        await update.message.reply_text("No groups saved. Use /addgroup first.")
        return ConversationHandler.END
    keyboard = []
    for i, g in enumerate(groups[:20]):
        keyboard.append([InlineKeyboardButton(f"- {g['name']}", callback_data=f"sharetog_{i}")])
    keyboard.append([InlineKeyboardButton("Done Selecting", callback_data="share_done")])
    context.user_data["sharing_url"] = url
    context.user_data["selected_groups"] = []
    await update.message.reply_text("Tap groups you shared to, then Done:", reply_markup=InlineKeyboardMarkup(keyboard))
    return ConversationHandler.END

async def toggle_share_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    idx = int(query.data.replace("sharetog_", ""))
    selected = context.user_data.get("selected_groups", [])
    if idx in selected:
        selected.remove(idx)
    else:
        selected.append(idx)
    context.user_data["selected_groups"] = selected
    data = load_data()
    groups = data["groups"]
    keyboard = []
    for i, g in enumerate(groups[:20]):
        tick = "[x] " if i in selected else "[ ] "
        keyboard.append([InlineKeyboardButton(f"{tick}{g['name']}", callback_data=f"sharetog_{i}")])
    keyboard.append([InlineKeyboardButton("Done Selecting", callback_data="share_done")])
    await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(keyboard))

async def share_done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    url = context.user_data.get("sharing_url", "")
    selected_idxs = context.user_data.get("selected_groups", [])
    if not selected_idxs:
        await query.message.reply_text("No groups selected. Share cancelled.")
        return
    data = load_data()
    groups = data["groups"]
    shared_to = [groups[i]["name"] for i in selected_idxs if i < len(groups)]
    record = {"url": url, "groups": shared_to, "date": datetime.now().strftime("%Y-%m-%d %H:%M")}
    data["shares"].append(record)
    save_data(data)
    await query.message.reply_text(f"Share logged! Video: {url}, Shared to: {', '.join(shared_to)}")

async def history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    shares = data.get("shares", [])
    if not shares:
        await update.message.reply_text("No sharing history yet. Use /share to log your first share!")
        return
    text = f"Sharing History ({len(shares)} entries)\n\n"
    for s in reversed(shares[-15:]):
        groups_str = ", ".join(s["groups"][:3])
        text += f"{s['date']}\n{s['url']}\n{groups_str}\n\n"
    await update.message.reply_text(text, disable_web_page_preview=True)

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    groups = data.get("groups", [])
    shares = data.get("shares", [])
    total_shares = sum(len(s.get("groups", [])) for s in shares)
    most_shared = {}
    for s in shares:
        for g in s.get("groups", []):
            most_shared[g] = most_shared.get(g, 0) + 1
    top_groups = sorted(most_shared.items(), key=lambda x: x[1], reverse=True)[:5]
    text = f"Your Stats\n\nGroups saved: {len(groups)}\nVideos shared: {len(shares)}\nTotal posts: {total_shares}\n\n"
    if top_groups:
        text += "Most shared to:\n"
        for name, count in top_groups:
            text += f"  {name}: {count} times\n"
    await update.message.reply_text(text)

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Cancelled.")
    return ConversationHandler.END

async def button_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query.data == "addgroup":
        await addgroup_start(update, context)
    elif query.data == "share":
        await share_start(update, context)
    elif query.data.startswith("niche_"):
        await niche_selected(update, context)
    elif query.data.startswith("sharetog_"):
        await toggle_share_group(update, context)
    elif query.data == "share_done":
        await share_done(update, context)

def main():
    if not BOT_TOKEN:
        print("ERROR: Set BOT_TOKEN environment variable!")
        return
    app = Application.builder().token(BOT_TOKEN).build()
    addgroup_conv = ConversationHandler(
        entry_points=[CommandHandler("addgroup", addgroup_start)],
        states={
            AWAITING_GROUP_LINK: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_group_link)],
            AWAITING_GROUP_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_group_name)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    share_conv = ConversationHandler(
        entry_points=[CommandHandler("share", share_start)],
        states={
            AWAITING_VIDEO_URL: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_video_url)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("groups", list_groups))
    app.add_handler(CommandHandler("find", find_groups))
    app.add_handler(CommandHandler("history", history))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(addgroup_conv)
    app.add_handler(share_conv)
    app.add_handler(CallbackQueryHandler(button_router))
    print("Bot is running!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
