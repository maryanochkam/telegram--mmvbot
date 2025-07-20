import logging
import re
import requests
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = "8080984044:AAHFO5lM_KULdtFjc56Aq2NgGtzLRm_sapo"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Отправь мне ссылку на товарную категорию сайта Post4u (например, Zara, Lefties).")

def parse_post4u(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')

        # По новому HTML-сайта: товары внутри блоков с классом "product-thumb"
        items = soup.select(".product-thumb")
        results = []

        for item in items:
            # Название товара
            title_tag = item.select_one(".caption a")
            # Ссылка на товар
            link = title_tag['href'] if title_tag else None
            # Картинка товара — в теге img внутри .image, берём src или data-src
            img_tag = item.select_one(".image img")
            img_url = None
            if img_tag:
                img_url = img_tag.get("data-src") or img_tag.get("src")
                if img_url and img_url.startswith("//"):
                    img_url = "https:" + img_url
            # Цена — в блоке .price
            price_tag = item.select_one(".price")
            price = price_tag.get_text(strip=True) if price_tag else ""

            if title_tag and link and img_url:
                title = title_tag.get_text(strip=True)
                results.append({
                    "title": title,
                    "link": link,
                    "image": img_url,
                    "price": price
                })

        return results
    except Exception as e:
        logger.error(f"Ошибка при парсинге: {e}")
        return []

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()

    if not re.match(r"https://www\.post4u\.com\.ua/.+", url):
        await update.message.reply_text("Пожалуйста, отправь ссылку на категорию товаров сайта Post4u.")
        return

    await update.message.reply_text("Собираю товары, подожди секунду...")

    items = parse_post4u(url)

    if not items:
        await update.message.reply_text("Не смог найти товары на этой странице.")
        return

    for item in items:
        caption = f"{item['title']}\n{item['price']}\n{item['link']}"
        try:
            await update.message.reply_photo(photo=item['image'], caption=caption)
        except Exception as e:
            logger.warning(f"Не удалось отправить фото: {e}")
            await update.message.reply_text(caption)

def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.run_polling()

if __name__ == "__main__":
    main()
