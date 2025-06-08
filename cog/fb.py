import discord
from discord.ext import commands, bridge, tasks
import requests
import re
import json
from bs4 import BeautifulSoup
import os
import shutil
import random
import asyncio
import logging

# 設置日誌
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('facebook_debug.log'),
        logging.StreamHandler()
    ]
)

class Facebook(commands.Cog):
    def __init__(self,bot: commands.Bot):
        self.bot = bot
        self.latest = None
        self.content = None
        self.image = None
        self.headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'accept-language': 'zh-TW,zh;q=0.9',
            'cache-control': 'no-cache',
            'pragma': 'no-cache',
            'priority': 'u=0, i',
            'sec-ch-ua': '"Chromium";v="136", "Google Chrome";v="136", "Not.A/Brand";v="99"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'none',
            'sec-fetch-user': '?1',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36',
        }
        self.cookies = {
            'datr': 'v4RCaCFBBlFnfbA7BLJjeZpw',
            'sb': 'v4RCaHRXccrV3Nutc30JS9Jo',
            'dpr': '1.5',
            'wd': '798x847',
        }
    
    @commands.Cog.listener()
    async def on_ready(self):
        data = self.get_data()
        if data is None:
            logging.error("Failed to get initial data during startup")
            self.content, self.image, self.latest = None, None, None
        else:
            result = self.filte_data(data)
            if result is None or None in result:
                logging.error("Failed to process initial data during startup")
                self.content, self.image, self.latest = None, None, None
            else:
                self.content, self.image, self.latest = result
                logging.info(f"Successfully initialized with latest post URL: {self.latest}")
        
        self.check_data.start()
        self.UpdateCookie.start()
        
    @tasks.loop(minutes=4)
    async def check_data(self):
        await asyncio.sleep(random.randint(1, 10))
        try:
            data = self.get_data()
            if data is None:
                logging.error("get_data() returned None")
                return
            
            result = self.filte_data(data)
            if result is None or None in result:
                logging.error("filte_data() returned None or invalid data")
                return
                
            content, uri, url = result
            
            if content is None or uri is None or url is None:
                logging.error("One or more data fields is None")
                return
            
            if url != self.latest and content != self.content and uri != self.image:
                logging.info(f"New post detected: {url}")
                try:
                    with open('1.jpg', 'wb') as img_file:
                        img_response = requests.get(url = uri, headers=self.headers, allow_redirects=True)
                        img_file.write(img_response.content)
                    
                    self.latest = url
                    self.content = content
                    self.image = uri
                    
                    channel = self.bot.get_channel(1357294484903297127)
                    embed = discord.Embed(title='Anon Taiwan 更新了新貼文！', url = url, color=0x00ff00)
                    embed.add_field(name='貼文連結', value=url, inline=False)
                    embed.add_field(name='貼文內容', value=content, inline=False) 
                    file = discord.File(f"1.jpg", filename=f"1.jpg")
                    embed.set_image(url=f"attachment://1.jpg")
                    await channel.send(content = '<@&1357315095235137636>', embed=embed, file=file) 
                    os.remove('1.jpg')
                    logging.info(f"Successfully sent notification for new post: {url}")
                except Exception as e:
                    logging.error(f"Error sending Discord notification: {e}")
        except Exception as e:
            logging.error(f"Error in check_data: {str(e)}", exc_info=True)
            
    @tasks.loop(hours=72)
    async def UpdateCookie(self):
        await asyncio.sleep(random.randint(1, 5)*3600)
        try:
            response = requests.get('https://www.facebook.com/BANDBAND1027', headers=self.headers)
            self.cookies = response.cookies.get_dict()
            self.cookies['dpr'] = '1.5'
            self.cookies['wd'] = '798x847'
            logging.info("Cookies updated: %s", self.cookies)
        except Exception as e:
            logging.error(f"Error updating cookies: {str(e)}", exc_info=True)
            
    def get_data(self):
        try:
            response = requests.get('https://www.facebook.com/BANDBAND1027', headers=self.headers, cookies=self.cookies)
            response.encoding = 'utf-8'
            
            # 記錄響應狀態和頭信息
            logging.debug(f"Response status code: {response.status_code}")
            logging.debug(f"Response headers: {response.headers}")
            
            # 保存完整的響應內容到文件中以供分析
            with open('facebook_response.html', 'w', encoding='utf-8') as f:
                f.write(response.text)
            
            pattern = r"\"attachments\":\[{\"styles\"(.*?)}}}"
            match = re.search(pattern, response.text, re.DOTALL)
            
            if not match:
                logging.error("No match found for the pattern in the response")
                return None
                
            text = '{"styles"' + match.group(1)
            cnt = 0
            for i in range(len(text)):
                if text[i] == '{':
                    cnt += 1
                elif text[i] == '}':
                    cnt -= 1
                    
            try:
                for i in range(cnt):
                    text += '}'
                # 保存提取的 JSON 數據以供分析
                with open('extracted_data.json', 'w', encoding='utf-8') as f:
                    f.write(text)
                    
                return json.loads(text)
            except json.JSONDecodeError as e:
                logging.error(f"JSON decode error: {str(e)}")
                logging.error(f"Problematic JSON text: {text}")
                return None
                
        except requests.RequestException as e:
            logging.error(f"Request error: {str(e)}", exc_info=True)
            return None
        except Exception as e:
            logging.error(f"Unexpected error in get_data: {str(e)}", exc_info=True)
            return None
    
    def filte_data(self,data):
        try:
            if not data or 'styles' not in data or 'attachment' not in data['styles']:
                logging.error("Invalid data structure: missing styles or attachment")
                return None, None, None
                
            attachment = data['styles']['attachment']
            
            if 'media' in attachment:
                # 處理單一媒體（圖片或視頻）
                logging.info("Processing single media attachment")
                if '__typename' in attachment['media'] and attachment['media']['__typename'] == 'Video':
                    # 處理視頻
                    url = attachment['url'].replace('\\','')
                    uri = attachment['media']['thumbnailImage']['uri'].replace('\\','')
                    response = requests.get(url, headers=self.headers,cookies=self.cookies, allow_redirects=True)
                    pattern = r'"story":{"message":(.*?)}'
                    match = re.search(pattern, response.text, re.DOTALL)
                    if match:
                        text = '{"message":' + match.group(1) + '}'
                        cnt = 0
                        for i in range(len(text)):
                            if text[i] == '{':
                                cnt += 1
                            elif text[i] == '}':
                                cnt -= 1
                        for i in range(cnt):
                            text += '}'
                        temp = json.loads(text)
                        text = temp['message']['text']
                        title = bytes(text,'utf-8').decode(encoding="utf-8", errors="ignore")
                        response.url = f'https://www.facebook.com/122122606034707135/posts/{attachment['media']['id']}'
                else:
                    # 處理單一圖片
                    url = attachment['media']['url'].replace('\\','')
                    media = attachment['media']
                    if 'photo_image' in media and 'uri' in media['photo_image']:
                        uri = media['photo_image']['uri'].replace('\\','')
                    elif 'viewer_image' in media and 'uri' in media['viewer_image']:
                        uri = media['viewer_image']['uri'].replace('\\','')
                    elif 'image' in media and 'uri' in media['image']:
                        uri = media['image']['uri'].replace('\\','')
                    else:
                        logging.warning("Could not find image URI in expected locations")
                        uri = url
                    response = requests.get(url, headers=self.headers,allow_redirects=True)
                    pattern = r'"message_preferred_body":(.*?)},"container'
                    match = re.search(pattern, response.text, re.DOTALL)
                    if match:
                        temp = json.loads('{"message_preferred_body":' + match.group(1) + '}}') 
                        text = temp["message_preferred_body"]['text']
                        title = bytes(text,'utf-8').decode(encoding="utf-8", errors="ignore")
                    else:
                        title = "無法提取貼文內容"
                    response.url = f'https://www.facebook.com/122122606034707135/posts/{attachment['media']['id']}'
            else:
                # 處理相簿（多張圖片）
                logging.info("Processing album attachment")
                
                # 檢查是否有所需的結構
                if 'all_subattachments' not in attachment:
                    logging.error("Missing all_subattachments in attachment")
                    return None, None, None
                    
                subattachments = attachment['all_subattachments']
                if 'nodes' not in subattachments or not subattachments['nodes']:
                    logging.error("Missing or empty nodes in all_subattachments")
                    return None, None, None
                
                url = attachment['url'].replace('\\','') if 'url' in attachment else None
                if not url:
                    logging.error("Missing URL in attachment")
                    return None, None, None
                
                # 從第一個節點獲取圖片
                first_node = subattachments['nodes'][0]
                if 'media' not in first_node:
                    logging.error("Missing media in first node")
                    return None, None, None
                    
                media = first_node['media']
                
                # 嘗試多種可能的圖片URI路徑
                uri = None
                uri_paths = ['viewer_image', 'photo_image', 'image']
                for path in uri_paths:
                    if path in media and 'uri' in media[path]:
                        uri = media[path]['uri'].replace('\\','')
                        logging.info(f"Found image URI using path: {path}")
                        break
                
                if not uri:
                    logging.error("Could not find image URI in any expected location")
                    # 使用URL作為備用
                    uri = url
                
                # 獲取貼文內容
                try:
                    response = requests.get(url, headers=self.headers,cookies=self.cookies, allow_redirects=True)
                    
                    # 嘗試多種模式來提取標題
                    patterns = [
                        r'"message_preferred_body":(.*?)},"container',
                        r'"story":{"message":(.*?)}',
                        r'"text":"([^"]*)"'
                    ]
                    
                    title = None
                    for pattern in patterns:
                        match = re.search(pattern, response.text, re.DOTALL)
                        if match:
                            try:
                                if 'message_preferred_body' in pattern:
                                    temp = json.loads('{"message_preferred_body":' + match.group(1) + '}}') 
                                    title = temp["message_preferred_body"]['text']
                                elif 'story' in pattern:
                                    text = '{"message":' + match.group(1) + '}'
                                    cnt = 0
                                    for i in range(len(text)):
                                        if text[i] == '{':
                                            cnt += 1
                                        elif text[i] == '}':
                                            cnt -= 1
                                    for i in range(cnt):
                                        text += '}'
                                    temp = json.loads(text)
                                    title = temp['message']['text']
                                else:
                                    title = match.group(1)
                                break
                            except (json.JSONDecodeError, KeyError) as e:
                                logging.warning(f"Failed to parse with pattern {pattern}: {e}")
                                continue
                    
                    if not title:
                        logging.warning("Could not extract post content, using fallback method")
                        # 使用BeautifulSoup作為備用方法
                        soup = BeautifulSoup(response.text, 'html.parser')
                        title = soup.title.string if soup.title else "無法提取貼文內容"
                    
                    title = bytes(title,'utf-8').decode(encoding="utf-8", errors="ignore")
                    
                    # 構建貼文URL
                    media_id = media.get('id')
                    if media_id:
                        response.url = f'https://www.facebook.com/122122606034707135/posts/{media_id}'
                    else:
                        response.url = url
                        
                except Exception as e:
                    logging.error(f"Error processing album content: {e}")
                    title = "處理貼文內容時發生錯誤"
                    response = requests.Response()
                    response.url = url
            
            logging.info(f"Successfully processed post: title='{title[:50]}...', uri='{uri[:50]}...', url='{response.url}'")
            return title, uri, response.url
            
        except Exception as e:
            logging.error(f"Error in filte_data: {str(e)}", exc_info=True)
            return None, None, None

def setup(bot: commands.Bot):
    bot.add_cog(Facebook(bot))