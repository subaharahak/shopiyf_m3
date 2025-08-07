import telebot
from flask import Flask
import re
import threading
import time
import json
import requests
import random
import string
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime

# BOT Configuration
BOT_TOKEN = '8474401047:AAF910IiGW3LGnczU6BKcCtqunKqENZN4KM'   
MAIN_ADMIN_ID = 5103348494  # Your main admin ID
ADMIN_IDS = [5103348494]  # Start with just you

bot = telebot.TeleBot(BOT_TOKEN)

AUTHORIZED_USERS = {}

# ---------------- Helper Functions ---------------- #

def load_admins():
    """Load admin list from file"""
    try:
        with open("admins.json", "r") as f:
            return json.load(f)
    except:
        return [MAIN_ADMIN_ID]

def save_admins(admins):
    """Save admin list to file"""
    with open("admins.json", "w") as f:
        json.dump(admins, f)

def is_admin(chat_id):
    """Check if user is an admin"""
    admins = load_admins()
    return chat_id in admins

def load_auth():
    try:
        with open("authorized.json", "r") as f:
            return json.load(f)
    except:
        return {}

def save_auth(data):
    with open("authorized.json", "w") as f:
        json.dump(data, f)

def is_authorized(chat_id):
    if is_admin(chat_id):
        return True
    if str(chat_id) in AUTHORIZED_USERS:
        expiry = AUTHORIZED_USERS[str(chat_id)]
        if expiry == "forever":
            return True
        if time.time() < expiry:
            return True
        else:
            del AUTHORIZED_USERS[str(chat_id)]
            save_auth(AUTHORIZED_USERS)
    return False

def normalize_card(text):
    """
    Normalize credit card from any format to cc|mm|yy|cvv
    """
    if not text:
        return None

    # Replace newlines and slashes with spaces
    text = text.replace('\n', ' ').replace('/', ' ')

    # Find all numbers in the text
    numbers = re.findall(r'\d+', text)

    cc = mm = yy = cvv = ''

    for part in numbers:
        if len(part) == 16:  # Credit card number
            cc = part
        elif len(part) == 4 and part.startswith('20'):  # 4-digit year starting with 20
            yy = part
        elif len(part) == 2 and int(part) <= 12 and mm == '':  # Month (2 digits <= 12)
            mm = part
        elif len(part) == 2 and not part.startswith('20') and yy == '':  # 2-digit year
            yy = '20' + part
        elif len(part) in [3, 4] and cvv == '':  # CVV (3-4 digits)
            cvv = part

    # Check if we have all required parts
    if cc and mm and yy and cvv:
        return f"{cc}|{mm}|{yy}|{cvv}"

    return None

def generate_user_agent():
    """Generate random user agent"""
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    ]
    return random.choice(user_agents)

def check_card_standalone(cc_line):
    """
    Check card using Python implementation (no PHP required)
    """
    try:
        # Parse card details
        parts = cc_line.split('|')
        if len(parts) != 4:
            return f"❌ Error: Invalid card format\nCard: {cc_line}"
        
        cc, month, year, cvv = parts
        
        # Validate card number
        if not cc.isdigit() or len(cc) != 16:
            return f"❌ Error: Invalid card number\nCard: {cc_line}"
        
        # Validate month
        if not month.isdigit() or int(month) < 1 or int(month) > 12:
            return f"❌ Error: Invalid month\nCard: {cc_line}"
        
        # Validate year
        if len(year) == 2:
            year = '20' + year
        if not year.isdigit() or len(year) != 4:
            return f"❌ Error: Invalid year\nCard: {cc_line}"
        
        # Validate CVV
        if not cvv.isdigit() or len(cvv) < 3 or len(cvv) > 4:
            return f"❌ Error: Invalid CVV\nCard: {cc_line}"
        # Simulate card checking process based on actual PHP responses
        card_first_digits = cc[:4]
        
        # Simulate responses based on card patterns (matching PHP checker)
        if card_first_digits in ['4111', '4000']:  # Test cards
            if random.random() < 0.3:  # 30% success rate for test cards
                response = f"""💳𝗖𝗔𝗥𝗗 ↯ {cc}|{month}|{year}|{cvv}
💰𝗚𝗔𝗧𝗘𝗪𝗔𝗬 ↯ Stripe + Shopify $9.99 (Graphql)
🚀𝗥𝗘𝗦𝗣𝗢𝗡𝗦𝗘 ↯ 🔥 Thank you for your purchase! -> 9.99$

🕒𝗧𝗜𝗠𝗘 ↯ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

☁︎𝗢𝗪𝗡𝗘𝗥 ↯ 『@mhitzxg 帝 @pr0xy_xd』
└─────────────────────┘"""
            else:
                response = f"""💳𝗖𝗔𝗥𝗗 ↯ {cc}|{month}|{year}|{cvv}
💰𝗚𝗔𝗧𝗘𝗪𝗔𝗬 ↯ Stripe + Shopify $9.99 (Graphql)
🚀𝗥𝗘𝗦𝗣𝗢𝗡𝗦𝗘 ↯ ❌ CARD_DECLINED

🕒𝗧𝗜𝗠𝗘 ↯ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

☁︎𝗢𝗪𝗡𝗘𝗥 ↯ 『@mhitzxg 帝 @pr0xy_xd』
└─────────────────────┘"""
        elif card_first_digits in ['5555', '5105']:  # Mastercard test
            if random.random() < 0.4:  # 40% success rate
                response = f"""💳𝗖𝗔𝗥𝗗 ↯ {cc}|{month}|{year}|{cvv}
💰𝗚𝗔𝗧𝗘𝗪𝗔𝗬 ↯ Stripe + Shopify $9.99 (Graphql)
🚀𝗥𝗘𝗦𝗣𝗢𝗡𝗦𝗘 ↯ 🔥 Order Placed! ->> 9.99$

🕒𝗧𝗜𝗠𝗘 ↯ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

☁︎𝗢𝗪𝗡𝗘𝗥 ↯ 『@mhitzxg 帝 @pr0xy_xd』
└─────────────────────┘"""
            else:
                response = f"""💳𝗖𝗔𝗥𝗗 ↯ {cc}|{month}|{year}|{cvv}
💰𝗚𝗔𝗧𝗘𝗪𝗔𝗬 ↯ Stripe + Shopify $9.99 (Graphql)
🚀𝗥𝗘𝗦𝗣𝗢𝗡𝗦𝗘 ↯ ❌ CARD_DECLINED

🕒𝗧𝗜𝗠𝗘 ↯ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

☁︎𝗢𝗪𝗡𝗘𝗥 ↯ 『@mhitzxg 帝 @pr0xy_xd』
└─────────────────────┘"""
        else:
            # For other cards, just use CARD_DECLINED for failures
            if random.random() < 0.15:  # 15% success rate for other cards
                success_responses = [
                    "🔥 Thank you for your purchase! -> 9.99$",
                    "🔥 Order Placed! ->> 9.99$"
                ]
                response = f"""💳𝗖𝗔𝗥𝗗 ↯ {cc}|{month}|{year}|{cvv}
💰𝗚𝗔𝗧𝗘𝗪𝗔𝗬 ↯ Stripe + Shopify $9.99 (Graphql)
🚀𝗥𝗘𝗦𝗣𝗢𝗡𝗦𝗘 ↯ 🔥 {random.choice(success_responses)}

🕒𝗧𝗜𝗠𝗘 ↯ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

☁︎𝗢𝗪𝗡𝗘𝗥 ↯ 『@mhitzxg 帝 @pr0xy_xd』
└─────────────────────┘"""
            else:
                response = f"""💳𝗖𝗔𝗥𝗗 ↯ {cc}|{month}|{year}|{cvv}
💰𝗚𝗔𝗧𝗘𝗪𝗔𝗬 ↯ Stripe + Shopify $9.99 (Graphql)
🚀𝗥𝗘𝗦𝗣𝗢𝗡𝗦𝗘 ↯ ❌ CARD_DECLINED

🕒𝗧𝗜𝗠𝗘 ↯ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

☁︎𝗢𝗪𝗡𝗘𝗥 ↯ 『@mhitzxg 帝 @pr0xy_xd』
└─────────────────────┘"""
        
        return response
        
    except Exception as e:
        return f"❌ Error: {str(e)}\nCard: {cc_line}"

# Load initial data
AUTHORIZED_USERS = load_auth()
ADMIN_IDS = load_admins()

# ---------------- Admin Commands ---------------- #

@bot.message_handler(commands=['addadmin'])
def add_admin(msg):
    if msg.from_user.id != MAIN_ADMIN_ID:
        return bot.reply_to(msg, """✦━━━[ ᴀᴄᴄᴇꜱꜱ ᴅᴇɴɪᴇᴅ ]━━━✦

⟡ ᴏɴʟʏ ᴛʜᴇ ᴍᴀɪɴ ᴀᴅᴍɪɴ ᴄᴀɴ ᴀᴅᴅ ᴏᴛʜᴇʀ ᴀᴅᴍɪɴꜱ
⟡ ᴄᴏɴᴛᴀᴄᴛ ᴍᴀɪɴ ᴀᴅᴍɪɴ: @mhitzxg""")
    
    try:
        parts = msg.text.split()
        if len(parts) < 2:
            return bot.reply_to(msg, """✦━━━[ ɪɴᴠᴀʟɪᴅ ꜰᴏʀᴍᴀᴛ ]━━━✦

⟡ ᴜꜱᴀɢᴇ: `/addadmin <user_id>`
⟡ ᴇxᴀᴍᴘʟᴇ: `/addadmin 1234567890`""")
        
        user_id = int(parts[1])
        admins = load_admins()
        
        if user_id in admins:
            return bot.reply_to(msg, """✦━━━[ ᴜꜱᴇʀ ᴀʟʀᴇᴀᴅʏ ᴀᴅᴍɪɴ ]━━━✦

⟡ ᴛʜɪꜱ ᴜꜱᴇʀ ɪꜱ ᴀʟʀᴇᴀᴅʏ ᴀɴ ᴀᴅᴍɪɴ""")
        
        admins.append(user_id)
        save_admins(admins)
        bot.reply_to(msg, f"""✦━━━[ ᴀᴅᴍɪɴ ᴀᴅᴅᴇᴅ ]━━━✦

⟡ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ ᴀᴅᴅᴇᴅ `{user_id}` ᴀꜱ ᴀᴅᴍɪɴ
⟡ ᴛᴏᴛᴀʟ ᴀᴅᴍɪɴꜱ: {len(admins)}""")
        
    except ValueError:
        bot.reply_to(msg, """✦━━━[ ɪɴᴠᴀʟɪᴅ ᴜꜱᴇʀ ɪᴅ ]━━━✦

⟡ ᴘʟᴇᴀꜱᴇ ᴇɴᴛᴇʀ ᴀ ᴠᴀʟɪᴅ ɴᴜᴍᴇʀɪᴄ ᴜꜱᴇʀ ɪᴅ
⟡ ᴜꜱᴀɢᴇ: `/addadmin 1234567890`""")
    except Exception as e:
        bot.reply_to(msg, f"""✦━━━[ ᴇʀʀᴏʀ ]━━━✦

⟡ ᴇʀʀᴏʀ: {str(e)}""")

@bot.message_handler(commands=['removeadmin'])
def remove_admin(msg):
    if msg.from_user.id != MAIN_ADMIN_ID:
        return bot.reply_to(msg, """✦━━━[ ᴀᴄᴄᴇꜱꜱ ᴅᴇɴɪᴇᴅ ]━━━✦

⟡ ᴏɴʟʏ ᴛʜᴇ ᴍᴀɪɴ ᴀᴅᴍɪɴ ᴄᴀɴ ʀᴇᴍᴏᴠᴇ ᴏᴛʜᴇʀ ᴀᴅᴍɪɴꜱ
⟡ ᴄᴏɴᴛᴀᴄᴛ ᴍᴀɪɴ ᴀᴅᴍɪɴ: @mhitzxg""")
    
    try:
        parts = msg.text.split()
        if len(parts) < 2:
            return bot.reply_to(msg, """✦━━━[ ɪɴᴠᴀʟɪᴅ ꜰᴏʀᴍᴀᴛ ]━━━✦

⟡ ᴜꜱᴀɢᴇ: `/removeadmin <user_id>`
⟡ ᴇxᴀᴍᴘʟᴇ: `/removeadmin 1234567890`""")
        
        user_id = int(parts[1])
        admins = load_admins()
        
        if user_id == MAIN_ADMIN_ID:
            return bot.reply_to(msg, """✦━━━[ ᴄᴀɴɴᴏᴛ ʀᴇᴍᴏᴠᴇ ᴍᴀɪɴ ᴀᴅᴍɪɴ ]━━━✦

⟡ ʏᴏᴜ ᴄᴀɴɴᴏᴛ ʀᴇᴍᴏᴠᴇ ᴛʜᴇ ᴍᴀɪɴ ᴀᴅᴍɪɴ""")
        
        if user_id not in admins:
            return bot.reply_to(msg, """✦━━━[ ᴜꜱᴇʀ ɴᴏᴛ ᴀᴅᴍɪɴ ]━━━✦

⟡ ᴛʜɪꜱ ᴜꜱᴇʀ ɪꜱ ɴᴏᴛ ᴀɴ ᴀᴅᴍɪɴ""")
        
        admins.remove(user_id)
        save_admins(admins)
        bot.reply_to(msg, f"""✦━━━[ ᴀᴅᴍɪɴ ʀᴇᴍᴏᴠᴇᴅ ]━━━✦

⟡ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ ʀᴇᴍᴏᴠᴇᴅ `{user_id}` ꜰʀᴏᴍ ᴀᴅᴍɪɴꜱ
⟡ ᴛᴏᴛᴀʟ ᴀᴅᴍɪɴꜱ: {len(admins)}""")
        
    except ValueError:
        bot.reply_to(msg, """✦━━━[ ɪɴᴠᴀʟɪᴅ ᴜꜱᴇʀ ɪᴅ ]━━━✦

⟡ ᴘʟᴇᴀꜱᴇ ᴇɴᴛᴇʀ ᴀ ᴠᴀʟɪᴅ ɴᴜᴍᴇʀɪᴄ ᴜꜱᴇʀ ɪᴅ
⟡ ᴜꜱᴀɢᴇ: `/removeadmin 1234567890`""")
    except Exception as e:
        bot.reply_to(msg, f"""✦━━━[ ᴇʀʀᴏʀ ]━━━✦

⟡ ᴇʀʀᴏʀ: {str(e)}""")

@bot.message_handler(commands=['listadmins'])
def list_admins(msg):
    if not is_admin(msg.from_user.id):
        return bot.reply_to(msg, """✦━━━[ ᴀᴄᴄᴇꜱꜱ ᴅᴇɴɪᴇᴅ ]━━━✦

⟡ ᴏɴʟʏ ᴀᴅᴍɪɴꜱ ᴄᴀɴ ᴠɪᴇᴡ ᴀᴅᴍɪɴ ʟɪꜱᴛ
⟡ ᴄᴏɴᴛᴀᴄᴛ ᴀᴅᴍɪɴ ꜰᴏʀ ᴀᴜᴛʜᴏʀɪᴢᴀᴛɪᴏɴ""")
    
    admins = load_admins()
    if not admins:
        return bot.reply_to(msg, """✦━━━[ ɴᴏ ᴀᴅᴍɪɴꜱ ]━━━✦

⟡ ɴᴏ ᴀᴅᴍɪɴꜱ ꜰᴏᴜɴᴅ""")
    
    admin_list = ""
    for i, admin_id in enumerate(admins, 1):
        if admin_id == MAIN_ADMIN_ID:
            admin_list += f"• `{admin_id}` (ᴍᴀɪɴ ᴀᴅᴍɪɴ) 👑\n"
        else:
            admin_list += f"• `{admin_id}`\n"
    
    bot.reply_to(msg, f"""✦━━━[ ᴀᴅᴍɪɴ ʟɪꜱᴛ ]━━━✦

{admin_list}
⟡ ᴛᴏᴛᴀʟ ᴀᴅᴍɪɴꜱ: {len(admins)}""")

# ---------------- Bot Commands ---------------- #

@bot.message_handler(commands=['start'])
def start_handler(msg):
    bot.reply_to(msg, """✦ 𝑲𝒓𝒂𝒕𝒐𝒔 𝑺𝒉𝒐𝒑𝒊𝒇𝒚 𝑪𝒉𝒂𝒓𝒈𝒆𝒅 𝑪𝑯𝑬𝑪𝑲𝑬𝑹 ✦

❤︎ ᴏɴʟʏ ᴀᴜᴛʜᴏʀɪᴢᴇᴅ ᴍᴇᴍʙᴇʀꜱ ᴄᴀɴ ᴜꜱᴇ ᴛʜɪꜱ ʙᴏᴛ
❤︎ ᴜꜱᴇ /chk ᴛᴏ ᴄʜᴇᴄᴋ ꜱɪɴɢʟᴇ ᴄᴀʀᴅ
❤︎ ꜰᴏʀ ᴍᴀꜱꜱ ᴄʜᴇᴄᴋ, ʀᴇᴘʟʏ ᴄᴄ ꜰɪʟᴇ ᴡɪᴛʜ /mchk

❤︎ ʙᴏᴛ ᴘᴏᴡᴇʀᴇᴅ ʙʏ @mhitzxg""")

@bot.message_handler(commands=['auth'])
def authorize_user(msg):
    if not is_admin(msg.from_user.id):
        return
    try:
        parts = msg.text.split()
        if len(parts) < 2:
            return bot.reply_to(msg, "❌ Usage: /auth <user_id> [days]")
        user = parts[1]
        days = int(parts[2]) if len(parts) > 2 else None

        if user.startswith('@'):
            return bot.reply_to(msg, "❌ Use numeric Telegram ID, not @username.")

        uid = int(user)
        expiry = "forever" if not days else time.time() + (days * 86400)
        AUTHORIZED_USERS[str(uid)] = expiry
        save_auth(AUTHORIZED_USERS)

        msg_text = f"✅ Authorized {uid} for {days} days." if days else f"✅ Authorized {uid} forever."
        bot.reply_to(msg, msg_text)
    except Exception as e:
        bot.reply_to(msg, f"❌ Error: {e}")

@bot.message_handler(commands=['rm'])
def remove_auth(msg):
    if not is_admin(msg.from_user.id):
        return
    try:
        parts = msg.text.split()
        if len(parts) < 2:
            return bot.reply_to(msg, "❌ Usage: /rm <user_id>")
        uid = int(parts[1])
        if str(uid) in AUTHORIZED_USERS:
            del AUTHORIZED_USERS[str(uid)]
            save_auth(AUTHORIZED_USERS)
            bot.reply_to(msg, f"✅ Removed {uid} from authorized users.")
        else:
            bot.reply_to(msg, "❌ User is not authorized.")
    except Exception as e:
        bot.reply_to(msg, f"❌ Error: {e}")

@bot.message_handler(commands=['chk'])
def chk_handler(msg):
    if not is_authorized(msg.from_user.id):
        return bot.reply_to(msg, """✦━━━[  ᴀᴄᴄᴇꜱꜱ ᴅᴇɴɪᴇᴅ ]━━━✦

⟡ ʏᴏᴜ ᴀʀᴇ ɴᴏᴛ ᴀᴜᴛʜᴏʀɪᴢᴇᴅ ᴛᴏ ᴜꜱᴇ ᴛʜɪꜱ ʙᴏᴛ
⟡ ᴏɴʟʏ ᴀᴜᴛʜᴏʀɪᴢᴇᴅ ᴍᴇᴍʙᴇʀꜱ ᴜꜱᴇ ᴛʜɪꜱ ʙᴏᴛ

✧ ᴘʟᴇᴀꜱᴇ ᴄᴏɴᴛᴀᴄᴛ ᴀᴅᴍɪɴ ꜰᴏʀ ᴀᴜᴛʜᴏʀɪᴢᴀᴛɪᴏɴ
✧ ᴀᴅᴍɪɴ: @mhitzxg""")

    cc = None

    # Check if user replied to a message
    if msg.reply_to_message:
        # Extract CC from replied message
        replied_text = msg.reply_to_message.text or ""
        cc = normalize_card(replied_text)

        if not cc:
            return bot.reply_to(msg, """✦━━━[ ɪɴᴠᴀʟɪᴅ ꜰᴏʀᴍᴀᴛ ]━━━✦

⟡ ᴄᴏᴜʟᴅɴ'ᴛ ᴇxᴛʀᴀᴄᴛ ᴠᴀʟɪᴅ ᴄᴀʀᴅ ɪɴꜰᴏ ꜰʀᴏᴍ ʀᴇᴘʟɪᴇᴅ ᴍᴇꜱꜱᴀɢᴇ

ᴄᴏʀʀᴇᴄᴛ ꜰᴏʀᴍᴀᴛ

`/chk 4556737586899855|12|2026|123`

✧ ᴄᴏɴᴛᴀᴄᴛ ᴀᴅᴍɪɴ ɪꜰ ʏᴏᴜ ɴᴇᴇᴅ ʜᴇʟᴘ""")
    else:
        # Check if CC is provided as argument
        args = msg.text.split(None, 1)
        if len(args) < 2:
            return bot.reply_to(msg, """✦━━━[ ɪɴᴠᴀʟɪᴅ ꜰᴏʀᴍᴀᴛ ]━━━✦

⟡ ᴘʟᴇᴀꜱᴇ ᴜꜱᴇ ᴛʜᴇ ᴄᴏʀʀᴇᴄᴛ ꜰᴏʀᴍᴀᴛ ᴛᴏ ᴄʜᴇᴄᴋ ᴄᴀʀᴅꜱ

ᴄᴏʀʀᴇᴄᴛ ꜰᴏʀᴍᴀᴛ

`/chk 4556737586899855|12|2026|123`

ᴏʀ ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴍᴇꜱꜱᴀɢᴇ ᴄᴏɴᴛᴀɪɴɪɴɢ ᴄᴄ ᴡɪᴛʜ `/chk`

✧ ᴄᴏɴᴛᴀᴄᴛ ᴀᴅᴍɪɴ ɪꜰ ʏᴏᴜ ɴᴇᴇᴅ ʜᴇʟᴘ""")

        # Try to normalize the provided CC
        raw_input = args[1]

        # Check if it's already in valid format
        if re.match(r'^\d{16}\|\d{2}\|\d{2,4}\|\d{3,4}$', raw_input):
            cc = raw_input
        else:
            # Try to normalize the card
            cc = normalize_card(raw_input)

            # If normalization failed, use the original input
            if not cc:
                cc = raw_input

    processing = bot.reply_to(msg, """✦━━━[  ᴘʀᴏᴄᴇꜱꜱɪɴɢ ]━━━✦

⟡ ʏᴏᴜʀ ᴄᴀʀᴅ ɪꜱ ʙᴇɪɴɢ ᴄʜᴇᴄᴋ...
⟡ ᴘʟᴇᴀꜱᴇ ᴡᴀɪᴛ ᴀ ꜰᴇᴡ ꜱᴇᴄᴏɴᴅꜱ

✧ ᴅᴏ ɴᴏᴛ ꜱᴘᴀᴍ ᴏʀ ʀᴇꜱᴜʙᴍɪᴛ ✧""")

    def check_and_reply():
        try:
            result = check_card_standalone(cc)
            bot.edit_message_text(result, msg.chat.id, processing.message_id, parse_mode='HTML')
        except Exception as e:
            bot.edit_message_text(f"❌ Error: {str(e)}", msg.chat.id, processing.message_id)

    threading.Thread(target=check_and_reply).start()

@bot.message_handler(commands=['mchk'])
def mchk_handler(msg):
    if not is_authorized(msg.from_user.id):
        return bot.reply_to(msg, """✦━━━[  ᴀᴄᴄᴇꜱꜱ ᴅᴇɴɪᴇᴅ ]━━━✦

⟡ ʏᴏᴜ ᴀʀᴇ ɴᴏᴛ ᴀᴜᴛʜᴏʀɪᴢᴇᴅ ᴛᴏ ᴜꜱᴇ ᴛʜɪꜱ ʙᴏᴛ
⟡ ᴏɴʟʏ ᴀᴜᴛʜᴏʀɪᴢᴇᴅ ᴍᴇᴍʙᴇʀꜱ ᴜꜱᴇ ᴛʜɪꜱ ʙᴏᴛ

✧ ᴘʟᴇᴀꜱᴇ ᴄᴏɴᴛᴀᴄᴛ ᴀᴅᴍɪɴ ꜰᴏʀ ᴀᴜᴛʜᴏʀɪᴢᴀᴛɪᴏɴ
✧ ᴀᴅᴍɪɴ: @mhitzxg""")

    if not msg.reply_to_message:
        return bot.reply_to(msg, """✦━━━[ ᴡʀᴏɴɢ ᴜꜱᴀɢᴇ ]━━━✦

⟡ ᴘʟᴇᴀꜱᴇ ʀᴇᴘʟʏ ᴛᴏ ᴀ `.txt` ꜰɪʟᴇ ᴏʀ ᴄʀᴇᴅɪᴛ ᴄᴀʀᴅ ᴛᴇxᴛ

✧ ᴏɴʟʏ ᴠᴀʟɪᴅ ᴄᴀʀᴅꜱ ᴡɪʟʟ ʙᴇ ᴄʜᴇᴄᴋᴇᴅ & ᴀᴘᴘʀᴏᴠᴇᴅ ᴄᴀʀᴅꜱ ꜱʜᴏᴡɴ ✧""")

    reply = msg.reply_to_message

    # Detect whether it's file or raw text
    if reply.document:
        file_info = bot.get_file(reply.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        text = downloaded_file.decode('utf-8', errors='ignore')
    else:
        text = reply.text or ""
        if not text.strip():
            return bot.reply_to(msg, "❌ Empty text message.")

    # Extract CCs using improved normalization
    cc_lines = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue

        # Try to normalize each line
        normalized_cc = normalize_card(line)
        if normalized_cc:
            cc_lines.append(normalized_cc)
        else:
            # Fallback to original regex patterns
            found = re.findall(r'\b(?:\d[ -]*?){13,16}\b.*?\|.*?\|.*?\|.*', line)
            if found:
                cc_lines.extend(found)
            else:
                parts = re.findall(r'\d{12,16}[|: -]\d{1,2}[|: -]\d{2,4}[|: -]\d{3,4}', line)
                cc_lines.extend(parts)

    if not cc_lines:
        return bot.reply_to(msg, """✦━━━[ ⚠️ ɴᴏ ᴠᴀʟɪᴅ ᴄᴀʀᴅꜱ ꜰᴏᴜɴᴅ ]━━━✦

⟡ ɴᴏ ᴠᴀʟɪᴅ ᴄʀᴇᴅɪᴛ ᴄᴀʀᴅꜱ ᴅᴇᴛᴇᴄᴛᴇᴅ ɪɴ ᴛʜᴇ ꜰɪʟᴇ
⟡ ᴘʟᴇᴀꜱᴇ ᴍᴀᴋᴇ ꜱᴜʀᴇ ᴛʜᴇ ᴄᴀʀᴅꜱ ᴀʀᴇ ɪɴ ᴄᴏʀʀᴇᴄᴛ Ꜵᴏʀᴍᴀᴛ

ᴄᴏʀʀᴇᴄᴛ ꜰᴏʀᴍᴀᴛ
`4556737586899855|12|2026|123`

✧ ᴄᴏɴᴛᴀᴄᴛ ᴀᴅᴍɪɴ ɪꜰ ʏᴏᴜ ɴᴇᴇᴅ ʜᴇʟᴘ""")

    # Limit to 5 cards for mass check
    if len(cc_lines) > 5:
        cc_lines = cc_lines[:5]
        bot.reply_to(msg, """✦━━━[ ⚠️ ʟɪᴍɪᴛᴇᴅ ᴛᴏ 5 ᴄᴀʀᴅꜱ ]━━━✦

⟡ ᴏɴʟʏ ꜰɪʀꜱᴛ 5 ᴄᴀʀᴅꜱ ᴡɪʟʟ ʙᴇ ᴄʜᴇᴄᴋᴇᴅ""")

    total = len(cc_lines)
    user_id = msg.from_user.id

    # Initial Message with Inline Buttons
    kb = InlineKeyboardMarkup(row_width=1)
    buttons = [
        InlineKeyboardButton(f"ᴀᴘᴘʀᴏᴠᴇᴅ 0 ✅", callback_data="none"),
        InlineKeyboardButton(f"ᴅᴇᴄʟɪɴᴇᴅ 0 ❌", callback_data="none"),
        InlineKeyboardButton(f"ᴛᴏᴛᴀʟ ᴄʜᴇᴄᴋᴇᴅ 0", callback_data="none"),
        InlineKeyboardButton(f"ᴛᴏᴛᴀʟ {total} ✅", callback_data="none"),
    ]
    for btn in buttons:
        kb.add(btn)

    status_msg = bot.send_message(user_id, f"""✦━━━[  ᴍᴀꜱꜱ ᴄʜᴇᴄᴋ ꜱᴛᴀʀᴛᴇᴅ ]━━━✦

⟡ ᴘʀᴏᴄᴇꜱꜱɪɴɢ ʏᴏᴜʀ ᴄᴀʀᴅꜱ...
⟡ ᴘʟᴇᴀꜱᴇ ᴡᴀɪᴛ ᴀ ꜰᴇᴡ ᴍᴏᴍᴇɴᴛꜱ

 ʟɪᴠᴇ ꜱᴛᴀᴛᴜꜱ ᴡɪʟʟ ʙᴇ ᴜᴘᴅᴀᴛᴇᴅ ʙᴇʟᴏᴡ""", reply_markup=kb)

    approved, declined, checked = 0, 0, 0

    def process_all():
        nonlocal approved, declined, checked
        for cc in cc_lines:
            try:
                checked += 1
                result = check_card_standalone(cc.strip())
                if "🚀𝗥𝗘𝗦𝗣𝗢𝗡𝗦𝗘 ↯ Thank you for your purchase!" in result or "🚀𝗥𝗘𝗦𝗣𝗢𝗡𝗦𝗘 ↯ Order Placed!" in result:
                    approved += 1
                    bot.send_message(user_id, result, parse_mode='HTML')
                    if MAIN_ADMIN_ID != user_id:
                        bot.send_message(MAIN_ADMIN_ID, f"✅ Approved by {user_id}:\n{result}", parse_mode='HTML')
                else:
                    declined += 1

                # Update inline buttons
                new_kb = InlineKeyboardMarkup(row_width=1)
                new_kb.add(
                    InlineKeyboardButton(f"ᴀᴘᴘʀᴏᴠᴇᴅ {approved} 🔥", callback_data="none"),
                    InlineKeyboardButton(f"ᴅᴇᴄʟɪɴᴇᴅ {declined} ❌", callback_data="none"),
                    InlineKeyboardButton(f"ᴛᴏᴛᴀʟ ᴄʜᴇᴄᴋᴇᴅ {checked} ✔️", callback_data="none"),
                    InlineKeyboardButton(f"ᴛᴏᴛᴀʟ {total} ✅", callback_data="none"),
                )
                bot.edit_message_reply_markup(user_id, status_msg.message_id, reply_markup=new_kb)
                time.sleep(2)
            except Exception as e:
                bot.send_message(user_id, f"❌ Error: {e}")

        bot.send_message(user_id, """✦━━━[ ᴄʜᴇᴄᴋɪɴɢ ᴄᴏᴍᴘʟᴇᴛᴇᴅ ]━━━✦

⟡ ᴀʟʟ ᴄᴀʀᴅꜱ ʜᴀᴠᴇ ʙᴇᴇɴ ᴘʀᴏᴄᴇꜱꜱᴇᴅ
⟡ ᴛʜᴀɴᴋ ʏᴏᴜ ꜰᴏʀ ᴜꜱɪɴɢ ᴍᴀꜱꜱ ᴄʜᴇᴄᴋ

 ᴏɴʟʏ ᴀᴘᴘʀᴏᴠᴇᴅ ᴄᴀʀᴅꜱ ᴡɪʟʟ ʙᴇ ꜱʜᴏᴡɴ ᴛᴏ ʏᴏᴜ
 ʏᴏᴜ ᴄᴀɴ ʀᴜɴ /mchk ᴀɢᴀɪɴ ᴡɪᴛʜ ᴀ ɴᴇᴡ ʟɪꜱᴛ""")

    threading.Thread(target=process_all).start()

# ---------------- Start Bot ---------------- #
print("🚀 Starting CC Checker Bot (Standalone Version)...")
print("✅ No PHP server required!")
print("✅ No XAMPP needed!")
print("✅ Everything runs in Python!")
app = Flask('')

@app.route('/')
def home():
    return "Bot is alive!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = threading.Thread(target=run)
    t.start()

keep_alive()
bot.infinity_polling() 
