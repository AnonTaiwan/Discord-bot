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
        self.content, self.image, self.latest = self.filte_data(data)
        print(f"Latest post URL: {self.latest}")
        self.check_data.start()
        self.UpdateCookie.start()
        
    @tasks.loop(minutes=4)
    async def check_data(self):
        await asyncio.sleep(random.randint(1, 10))
        data = self.get_data()
        content, uri, url = self.filte_data(data)
        if url != self.latest and content != self.content and uri != self.image:
            print(f"New post detected: {url}")
            with open('1.jpg', 'wb') as img_file:
                img_response = requests.get(url = uri, headers=self.headers, allow_redirects=True)
                img_file.write(img_response.content)
            self.latest = url
            self.content = content
            self.image = uri
            channel = self.bot.get_channel(1357294484903297127)
            # channel = self.bot.get_channel(1361993681934225548)
            embed = discord.Embed(title='Anon Taiwan 更新了新貼文！', url = url, color=0x00ff00)
            embed.add_field(name='貼文連結', value=url, inline=False)
            embed.add_field(name='貼文內容', value=content, inline=False) 
            file = discord.File(f"1.jpg", filename=f"1.jpg")
            embed.set_image(url=f"attachment://1.jpg")
            await channel.send(content = '<@&1357315095235137636>', embed=embed, file=file) 
            # await channel.send(embed=embed, file=file)
            os.remove('1.jpg')
            
    @tasks.loop(hours=72)
    async def UpdateCookie(self):
        await asyncio.sleep(random.randint(1, 5)*3600)
        response = requests.get('https://www.facebook.com/BANDBAND1027', headers=self.headers)
        self.cookies = response.cookies.get_dict()
        self.cookies['dpr'] = '1.5'
        self.cookies['wd'] = '798x847'
        print("Cookies updated:", self.cookies)
            
    def get_data(self):
        response = requests.get('https://www.facebook.com/BANDBAND1027', headers=self.headers,cookies=self.cookies)
        response.encoding = 'utf-8' 
        pattern = r"\"attachments\":\[{\"styles\"(.*?)}}}"  # 抓取 styles 到 attachments 結尾附近
        match = re.search(pattern, response.text, re.DOTALL)
        if match:
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
                return json.loads(text)
            except json.JSONDecodeError as e:
                print("JSON decode error:", e)
                return None
    
    def filte_data(self,data):
        if 'media' in data['styles']['attachment']:
            if '__typename' in data['styles']['attachment']['media'].keys() and data['styles']['attachment']['media']['__typename'] == 'Video':
                url = data['styles']['attachment']['url'].replace('\\','')
                uri = data['styles']['attachment']['media']['thumbnailImage']['uri'].replace('\\','')
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
                    response.url = f'https://www.facebook.com/122122606034707135/posts/{data['styles']['attachment']['media']['id']}'
            else:
                url = data['styles']['attachment']['media']['url'].replace('\\','')
                media = data['styles']['attachment']['media']
                if 'placeholder_image' in media and 'uri' in media['placeholder_image']:
                    uri = media['placeholder_image']['uri'].replace('\\','')
                elif 'viewer_image' in media and 'uri' in media['viewer_image']:
                    uri = media['viewer_image']['uri'].replace('\\','')
                elif 'image' in media and 'uri' in media['image']:
                    uri = media['image']['uri'].replace('\\','')
                elif 'photo_image' in media and 'uri' in media['photo_image']:
                    uri = media['photo_image']['uri'].replace('\\','')
                else:
                    print("Warning: Could not find image URI in expected locations")
                    uri = url  # フォールバックとしてURLを使用
                response = requests.get(url, headers=self.headers,allow_redirects=True)
                pattern = r'"message_preferred_body":(.*?)},"container'
                match = re.search(pattern, response.text, re.DOTALL)
                temp = json.loads('{"message_preferred_body":' + match.group(1) + '}}') 
                text = temp["message_preferred_body"]['text']
                title = bytes(text,'utf-8').decode(encoding="utf-8", errors="ignore")
                response.url = f'https://www.facebook.com/122122606034707135/posts/{data['styles']['attachment']['media']['id']}'
        else:
            url = data['styles']['attachment']['url'].replace('\\','')
            uri = data['styles']['attachment']['all_subattachments']['nodes'][0]["media"]['viewer_image']['uri'].replace('\\','')
            response = requests.get(url, headers=self.headers,cookies=self.cookies, allow_redirects=True)
            soup = BeautifulSoup(response.text, 'html.parser')
            title = soup.title.string 
        return title, uri, response.url 

def setup(bot: commands.Bot):
    bot.add_cog(Facebook(bot))