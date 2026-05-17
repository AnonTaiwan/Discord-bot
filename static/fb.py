import discord
from discord.ext import commands
from curl_cffi import requests
import re
import json
from bs4 import BeautifulSoup
import os
import random
import asyncio
import time
import logging
from datetime import datetime, timedelta


class Facebook(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.latest = None
        self.content = None
        self.image = None
        self.check_data_lock = asyncio.Lock()
        # 設置日誌
        self.load_latest_post()
        self.setup_logging()
        try:
            with open("JSON/Cookies.json", "r", encoding="utf-8") as f:
                self.cookies = json.load(f)
        except Exception:
            self.cookies = {
                "datr": "y_9haN3HQZQEBj4W0XfaaCnK",
                "sb": "y_9haIwH6HDvW_SGJlsn2aaU",
                "dpr": "2",
                "wd": "798x847",
            }
        self.headers = {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "accept-language": "zh-TW,zh;q=0.9",
            "priority": "u=0, i",
            "sec-ch-ua": '"Google Chrome";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "none",
            "sec-fetch-user": "?1",
            "upgrade-insecure-requests": "1",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
        }
        try:
            self.update_task = self.bot.loop.create_task(self.cookie_scheduler())
            time.sleep(5)
            self.logger.info("開始初始化 Facebook 監控...")
            data = self.get_data()
            if data is None:
                self.logger.warning("無法獲取 Facebook 數據，跳過初始化")
                return
            self.content, self.image, self.latest = self.filte_data(data)
            if self.content is None and self.image is None and self.latest is None:
                self.logger.warning("無法獲取 Facebook 數據，以之前的紀錄代替")
                self.load_latest_post()
                return
            self.logger.info(f"最新貼文 URL: {self.latest}")
        except Exception as e:
            self.logger.error(f"初始化過程中發生錯誤：{e}")
        finally:
            # 無論如何只啟動一次
            asyncio.create_task(self.check_data())

    def setup_logging(self):
        """設置日誌系統"""
        # 創建 logs 目錄（如果不存在）
        if not os.path.exists("logs"):
            os.makedirs("logs")

        # 設置日誌文件名（包含日期）
        log_filename = f"logs/fb_bot_{datetime.now().strftime('%Y%m%d')}.log"

        # 配置日誌格式
        log_format = "%(asctime)s - %(levelname)s - %(message)s"
        date_format = "%Y-%m-%d %H:%M:%S"

        # 配置日誌
        logging.basicConfig(
            level=logging.INFO,
            format=log_format,
            datefmt=date_format,
            handlers=[
                logging.FileHandler(log_filename, encoding="utf-8"),
                logging.StreamHandler(),  # 同時輸出到控制台
            ],
        )

        self.logger = logging.getLogger(__name__)
        self.logger.info("cog/fb.py: 日誌系統初始化完成")

    async def check_data(self):
        while True:
            await asyncio.sleep(10 * 60)
            try:
                await asyncio.sleep(random.randint(1, 10))
                async with self.check_data_lock:
                    data = self.get_data()
                    if data is None:
                        self.logger.warning("在 check_data 中無法獲取 Facebook 數據")
                        await asyncio.sleep(10 * 60)
                        continue
                    content, uri, url = self.filte_data(data)
                    if self.content is None and self.image is None and self.latest is None:
                        self.logger.warning("無法獲取 Facebook 數據，用最近的紀錄代替")
                        self.load_latest_post()
                    if url != self.latest and content != self.content and uri != self.image:
                        self.logger.info(f"檢測到新貼文：{url}")
                        with open("1.jpg", "wb") as img_file:
                            img_response = requests.get(url=uri, headers=self.headers, allow_redirects=True, impersonate="chrome110")
                            img_file.write(img_response.content)
                        channel = self.bot.get_channel(1357294484903297127)
                        # channel = self.bot.get_channel(873263562942992395)
                        embed = discord.Embed(title="Anon Taiwan 更新了新貼文！", url=url, color=0x00FF00)
                        embed.add_field(name="貼文連結", value=url, inline=False)
                        embed.add_field(name="貼文內容", value=content or "（無內容）", inline=False)

                        # 檢查檔案是否存在
                        if os.path.exists("1.jpg"):
                            file = discord.File("1.jpg", filename="1.jpg")
                            embed.set_image(url="attachment://1.jpg")
                            if channel and hasattr(channel, "send"):
                                msg = await channel.send(content="<@&1357315095235137636>", embed=embed, file=file)  # type:ignore
                                await msg.publish()
                            else:
                                self.logger.error("找不到指定的 Discord 頻道或無法發送訊息")
                            os.remove("1.jpg")
                        else:
                            self.logger.warning("檔案 1.jpg 不存在，跳過檔案發送")
                            if channel and hasattr(channel, "send"):
                                msg = await channel.send(content="<@&1357315095235137636>", embed=embed)  # type:ignore
                                await msg.publish()
                            else:
                                self.logger.error("找不到指定的 Discord 頻道或無法發送訊息")
                        self.latest = url
                        self.content = content
                        self.image = uri
                        self.save_latest_post()
                        self.logger.info("新貼文已成功發送到 Discord")

            except Exception:
                pass

    def get_data(self):
        try:
            response = requests.get(
                "https://www.facebook.com/profile.php?id=61566516636930",
                headers=self.headers,
                cookies=self.cookies,
                impersonate="chrome110",
            )
            response.encoding = "utf-8"

            # 檢查回應狀態
            if response.status_code != 200:
                self.logger.warning(f"Facebook 返回狀態碼 {response.status_code}")
                return None

            pattern = r"\"attachments\":\[{\"media\"(.*?)}}}"  # 抓取 styles 到 attachments 結尾附近
            match = re.search(pattern, response.text, re.DOTALL)
            if match:
                text = '{"media"' + match.group(1)
                cnt = 0
                for i in range(len(text)):
                    if text[i] == "{":
                        cnt += 1
                    elif text[i] == "}":
                        cnt -= 1
                try:
                    for i in range(cnt):
                        text += "}"
                    return json.loads(text)
                except json.JSONDecodeError as e:
                    self.logger.error(f"JSON 解析錯誤：{e}")
                    return None
            else:
                self.logger.warning("在 Facebook 回應中找不到 attachments 模式")
                return None
        except Exception as e:
            self.logger.error(f"get_data 中發生錯誤：{e}")
            return None

    def filte_data(self, data):
        if "media" in data["styles"]["attachment"]:
            if (
                "__typename" in data["styles"]["attachment"]["media"].keys()
                and data["styles"]["attachment"]["media"]["__typename"] == "Video"
            ):
                url = data["styles"]["attachment"]["url"].replace("\\", "")
                uri = data["styles"]["attachment"]["media"]["thumbnailImage"]["uri"].replace("\\", "")
                response = requests.get(url, headers=self.headers, cookies=self.cookies, allow_redirects=True, impersonate="chrome110")
                if "reel" not in url:
                    pattern = r'"story":{"message":(.*?)}'
                else:
                    pattern = r'"message":(.*?)",'
                match = re.search(pattern, response.text, re.DOTALL)
                if match:
                    if "reel" not in url:
                        text = '{"message":' + match.group(1) + "}"
                    else:
                        text = '{"message":' + match.group(1) + '"'
                    cnt = 0
                    for i in range(len(text)):
                        if text[i] == "{":
                            cnt += 1
                        elif text[i] == "}":
                            cnt -= 1
                    for i in range(cnt):
                        text += "}"
                    temp = json.loads(text)
                    text = temp["message"]["text"]
                    title = bytes(text, "utf-8").decode(encoding="utf-8", errors="ignore")
                    response.url = f"https://www.facebook.com/61566516636930/posts/{data['styles']['attachment']['media']['id']}"
                else:
                    # 如果找不到匹配，使用預設值
                    self.logger.warning("找不到影片訊息模式")
                    title = "無法解析的影片貼文"
                    response.url = f"https://www.facebook.com/61566516636930/posts/{data['styles']['attachment']['media']['id']}"
            else:
                try:
                    url = data["styles"]["attachment"]["media"]["url"].replace("\\", "")
                    uri = data["styles"]["attachment"]["media"]["photo_image"]["uri"].replace("\\", "")
                    response = requests.get(url, headers=self.headers, allow_redirects=True, impersonate="chrome110")
                    pattern = r'"message_preferred_body":(.*?)},"container'
                    match = re.search(pattern, response.text, re.DOTALL)
                    if match:
                        temp = json.loads('{"message_preferred_body":' + match.group(1) + "}}")
                        text = temp["message_preferred_body"]["text"]
                        title = bytes(text, "utf-8").decode(encoding="utf-8", errors="ignore")
                        response.url = f"https://www.facebook.com/61566516636930/posts/{data['styles']['attachment']['media']['id']}"
                    else:
                        # 如果找不到匹配，嘗試其他模式或使用預設值
                        self.logger.warning("找不到 message_preferred_body 模式")
                        # 嘗試其他可能的模式
                        alt_pattern = r'"message":{"text":"(.*?)"'
                        alt_match = re.search(alt_pattern, response.text, re.DOTALL)
                        if alt_match:
                            title = alt_match.group(1)
                        else:
                            title = "無法解析的圖片貼文"
                        response.url = f"https://www.facebook.com/61566516636930/posts/{data['styles']['attachment']['media']['id']}"
                except Exception as e:
                    self.logger.error(f"filte_data 中發生錯誤：{e}")
                    return None, None, None
        else:
            url = data["styles"]["attachment"]["url"].replace("\\", "")
            uri = data["styles"]["attachment"]["all_subattachments"]["nodes"][0]["media"]["viewer_image"]["uri"].replace("\\", "")
            response = requests.get(url, headers=self.headers, cookies=self.cookies, allow_redirects=True, impersonate="chrome110")
            soup = BeautifulSoup(response.text, "html.parser")
            title = soup.title.string if soup.title else "無法解析的貼文"
        return title, uri, response.url

    async def cookie_scheduler(self):
        try:
            os.makedirs("JSON", exist_ok=True)
            last_time = None
            path = "JSON/last_cookie_update.json"

            # 讀取上次時間
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    timestamp = json.load(f).get("last_update")
                    if timestamp:
                        last_time = datetime.fromisoformat(timestamp)

            # 如果有記錄
            if last_time:
                elapsed = datetime.now() - last_time
                remaining = timedelta(hours=48) - elapsed
                if remaining.total_seconds() > 0:
                    self.logger.info(f"等待剩餘時間：{remaining}")
                    await asyncio.sleep(remaining.total_seconds())

            # 一直跑
            while True:
                await self.UpdateCookie()
                with open(path, "w", encoding="utf-8") as f:
                    json.dump({"last_update": datetime.now().isoformat()}, f, indent=2)
                await asyncio.sleep(48 * 3600)  # 48 小時
                await asyncio.sleep(random.randint(1, 10) * 3600)

        except Exception as e:
            self.logger.error(f"cookie_scheduler 錯誤：{e}")

    async def UpdateCookie(self):
        try:
            self.logger.info("開始更新 Cookies...")
            response = requests.get("https://www.facebook.com/BANDBAND1027", headers=self.headers, impersonate="chrome110")
            self.cookies = response.cookies.get_dict()
            self.cookies["dpr"] = "2"
            self.cookies["wd"] = "798x847"
            self.logger.info(f"Cookies 已更新：{self.cookies}")
            with open("JSON/Cookies.json", "w", encoding="utf-8") as f:
                json.dump(self.cookies, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.logger.error(f"更新 Cookies 時發生錯誤：{e}")

    def save_latest_post(self):
        with open("JSON/latest_post.json", "w", encoding="utf-8") as f:
            json.dump({"latest": self.latest, "content": self.content, "image": self.image}, f, ensure_ascii=False, indent=2)

    def load_latest_post(self):
        try:
            with open("JSON/latest_post.json", "r", encoding="utf-8") as f:
                data = json.load(f)
                self.latest = data.get("latest")
                self.content = data.get("content")
                self.image = data.get("image")  # 修正這裡
        except Exception:
            self.latest = None
            self.content = None
            self.image = None


def setup(bot: commands.Bot):
    bot.add_cog(Facebook(bot))
