import discord
from discord.ext import commands, tasks
from curl_cffi import requests
import json
from datetime import datetime, timedelta, time
import os
import utils
import asyncio
import re
import time
from google import genai

class X(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = utils.get_logger(__name__)
        self.logger.info("cog/x.py: 日誌系統初始化完成")
        self.users = utils.X_DETECT_LIST
        self.channel = utils.TEST_CHANNEL_ID
        with open('JSON/bot.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        self.GEMINI_TOKEN = config.get("GEMINI_TOKEN")
        self.X_ID_TO_NAME = utils.X_ID_TO_NAME
        
    @commands.Cog.listener()
    async def on_ready(self):
        self.logger.info("cog/x.py: Bot 已準備就緒")
        self.gt_value, self.cookies = self.__get_gt_cookies()
        self.new_post = {}
        for post in self.users:
            post = str(post)
            data = self.__fetch_tweets(post)
            self.new_post[post] = data['id_str']
            await asyncio.sleep(3) 
        await asyncio.sleep(300)
        if not self.check_post_updates.is_running():
            self.check_post_updates.start()
        if not self.update_gt_cookies.is_running():
            await asyncio.sleep(2 * 3600)
            self.update_gt_cookies.start()
    
    @tasks.loop(hours=2)
    async def update_gt_cookies(self):
        self.logger.info("開始更新 X 的 gt 和 cookies")
        self.gt_value, self.cookies = self.__get_gt_cookies()
        if self.gt_value and self.cookies:
            self.logger.info(f"成功獲取 gt: {self.gt_value} 和 cookies")
        else:
            self.logger.error("獲取 gt 或 cookies 失敗")
    
    @tasks.loop(minutes=5)
    async def check_post_updates(self):
        channel = self.bot.get_channel(self.channel)
        for post in self.users:
            post = str(post)
            data = self.__fetch_tweets(post)
            if data['id_str'] != self.new_post.get(post):
                text = data['full_text']
                translated_text = self.__translate_text(text)
                images = data['entities'].get('media')
                if images is not None:
                    self.__get_image(images)
                    files = [discord.File(f'tmp/image_{i}.jpg') for i in range(len(images))]
                name = self.X_ID_TO_NAME.get(post, "Unknown")
                embed = discord.Embed(title=name, color=0x1DA1F2)
                embed.add_field(name="原文", value=text, inline=False)
                embed.add_field(name="翻譯", value=translated_text, inline=False)
                embed.set_footer(text=f"來自 X 的最新貼文，發布時間：{data['created_at']}")
                await channel.send(embed=embed, files=files if images is not None else None)
                self.new_post[post] = data['id_str']
                for i in range(len(images)) if images is not None else []:
                    os.remove(f'tmp/image_{i}.jpg')
            await asyncio.sleep(3)
    
    def __get_gt_cookies(self):
        headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'accept-language': 'zh-TW,zh;q=0.9',
            'cache-control': 'no-cache',
            'pragma': 'no-cache',
            'priority': 'u=0, i',
            'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-user': '?1',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36',
        }

        response = requests.get('https://x.com/', headers=headers)
        pattern = r"gt=(\d+);"
        match = re.search(pattern, response.text)
        if match:
            gt_value = match.group(1)
            print("gt value:", gt_value)
            return gt_value, response.cookies.get_dict()

    def __fetch_tweets(self, userId):
        headers = {
            'accept': '*/*',
            'accept-language': 'zh-TW,zh;q=0.9',
            'authorization': 'Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA',
            'content-type': 'application/json',
            'origin': 'https://x.com',
            'priority': 'u=1, i',
            'referer': 'https://x.com/',
            'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36',
            'x-client-transaction-id': 'H0Xv7rsi3t39O920V62HLXluEdkzsRZ8xKPk6wDgjcze2+jArCaLBttE9hHKbXRM9IWAYhvRsh7J2tMymsJOYWx4akQOHA',
            'x-guest-token': self.gt_value,
            'x-twitter-active-user': 'yes',
            'x-twitter-client-language': 'zh-tw',
            'x-xp-forwarded-for': '2431e16dad132fc1950a60089592b1330445c792e033c76c121647bbe77d00d094641f2934314a69cdbae4dccb4cfc16be72e7496927618aa8d3c533c2626a50d0debe88f47b0daae91f15341c78cec143acc85c814b827d31679bdcac7dade2530c1c8a9b2fcb0d09dfbe2555e685994992d2b09e490982fd4d34028eaa6ad9ad267b056f5be3849c78bff635d6809ceb9571d1bf555c1506929a0592449b807cfd0dee420a1de847c04e9e976176d27a93dc5f6bc49c90d8e9f7e515cd14d1b23c29fb9d97e2eb1b6a229f034a5d611efb8fb9ac0418598ed5513ce514a3852c988a5376754941feb7decf2ae9d03bc1ef3047aa453d0244add6',
        }
        variables = {
        "userId": userId,
        "count": 20,
        "includePromotedContent": True,
        "withQuickPromoteEligibilityTweetFields": True,
        "withVoice": True
        }
        params = {
            'variables': json.dumps(variables),
            'features': '{"rweb_video_screen_enabled":false,"payments_enabled":false,"profile_label_improvements_pcf_label_in_post_enabled":true,"rweb_tipjar_consumption_enabled":true,"verified_phone_label_enabled":false,"creator_subscriptions_tweet_preview_api_enabled":true,"responsive_web_graphql_timeline_navigation_enabled":true,"responsive_web_graphql_skip_user_profile_image_extensions_enabled":false,"premium_content_api_read_enabled":false,"communities_web_enable_tweet_community_results_fetch":true,"c9s_tweet_anatomy_moderator_badge_enabled":true,"responsive_web_grok_analyze_button_fetch_trends_enabled":false,"responsive_web_grok_analyze_post_followups_enabled":false,"responsive_web_jetfuel_frame":true,"responsive_web_grok_share_attachment_enabled":true,"articles_preview_enabled":true,"responsive_web_edit_tweet_api_enabled":true,"graphql_is_translatable_rweb_tweet_is_translatable_enabled":true,"view_counts_everywhere_api_enabled":true,"longform_notetweets_consumption_enabled":true,"responsive_web_twitter_article_tweet_consumption_enabled":true,"tweet_awards_web_tipping_enabled":false,"responsive_web_grok_show_grok_translated_post":false,"responsive_web_grok_analysis_button_from_backend":false,"creator_subscriptions_quote_tweet_preview_enabled":false,"freedom_of_speech_not_reach_fetch_enabled":true,"standardized_nudges_misinfo":true,"tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled":true,"longform_notetweets_rich_text_read_enabled":true,"longform_notetweets_inline_media_enabled":true,"responsive_web_grok_image_annotation_enabled":true,"responsive_web_grok_imagine_annotation_enabled":true,"responsive_web_grok_community_note_auto_translation_is_enabled":false,"responsive_web_enhance_cards_enabled":false}',
            'fieldToggles': '{"withArticlePlainText":false}',
        }
        url = 'https://api.x.com/graphql/VfoNveT-zJPGVZMPydZUfQ/UserTweets'
        session = requests.Session()
        session.headers.update(headers)
        session.cookies.update(self.cookies)

        response = session.get(
            url,
            params=params,
        )

        if response.status_code != 200:
            print("Initial request failed, trying to refresh cookies...")
            time.sleep(2)
            session.cookies.clear()
            response = session.get('https://x.com/Hina_Youmiya')
            cookies = response.cookies.get_dict()
            response = session.get(
                url,
                params=params,
            )
        datas = response.json()
        data = datas['data']['user']['result']['timeline']['timeline']['instructions'][2]['entries'][0]['content']['itemContent']['tweet_results']['result']['legacy']
        session.close()
        return data

    def __get_image(self, images):
        headers = {
            'accept': '*/*',
            'accept-language': 'zh-TW,zh;q=0.9',
            'authorization': 'Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA',
            'content-type': 'application/json',
            'origin': 'https://x.com',
            'priority': 'u=1, i',
            'referer': 'https://x.com/',
            'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36',
            'x-client-transaction-id': 'H0Xv7rsi3t39O920V62HLXluEdkzsRZ8xKPk6wDgjcze2+jArCaLBttE9hHKbXRM9IWAYhvRsh7J2tMymsJOYWx4akQOHA',
            'x-guest-token': self.gt_value,
            'x-twitter-active-user': 'yes',
            'x-twitter-client-language': 'zh-tw',
            'x-xp-forwarded-for': '2431e16dad132fc1950a60089592b1330445c792e033c76c121647bbe77d00d094641f2934314a69cdbae4dccb4cfc16be72e7496927618aa8d3c533c2626a50d0debe88f47b0daae91f15341c78cec143acc85c814b827d31679bdcac7dade2530c1c8a9b2fcb0d09dfbe2555e685994992d2b09e490982fd4d34028eaa6ad9ad267b056f5be3849c78bff635d6809ceb9571d1bf555c1506929a0592449b807cfd0dee420a1de847c04e9e976176d27a93dc5f6bc49c90d8e9f7e515cd14d1b23c29fb9d97e2eb1b6a229f034a5d611efb8fb9ac0418598ed5513ce514a3852c988a5376754941feb7decf2ae9d03bc1ef3047aa453d0244add6',
        }
        session = requests.Session()
        session.headers.update(headers)
        session.cookies.update(self.cookies)
        if images is None:
            return
        for image in range(len(images)):
            url = images[image]['media_url_https']
            print(url)
            img_data = session.get(url).content
            with open(f'tmp/image_{image}.jpg', 'wb') as handler:
                handler.write(img_data)

    def __translate_text(self, content):
        client = genai.Client(api_key=self.GEMINI_TOKEN)
        response = client.models.generate_content(
        model="gemini-2.5-flash", contents="請不省略的幫我翻譯以下日文內容 (不用解釋)，並用繁體中文回答：\n" + content
        )
        return response.text

def setup(bot):
    bot.add_cog(X(bot))