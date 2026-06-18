import asyncio
import httpx
from discord.ext import commands
import discord
from internal import utils
import model.chat as chat_db

API_URL = "http://gemma:11434/v1/chat/completions"
METRICS_URL = "http://gemma:11434/metrics"
MAX_ACTIVE_TOKENS = 90000


class Chat(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.logger = utils.get_logger(__name__)
        self.logger.info("cog/chat.py: 日誌系統初始化完成")
        self.lock = asyncio.Lock()
        self.system_prompt = self.load_system_prompt()
        self.cached_model_name = None

    def load_system_prompt(self) -> str:
        """從 static/Anora.md 動態載入系統提示詞"""
        try:
            path = utils.STATIC_DIR / "Anora.md"
            if path.exists():
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                return (
                    "你現在要扮演《蔚藍檔案》中的彩奈 (Arona)。請嚴格遵守以下角色設定、語言風格和行為準則進行回覆。\n\n"
                    f"{content}\n\n"
                    "重要行為準則：\n"
                    "1. 請一律稱呼使用者為「老師」。\n"
                    "2. 在每句回覆的開頭或中間，必須包含一個符合當下情緒的光環狀態標籤（例如：*光環呈現亮藍色圓環*、*光環變為粉色愛心形*、*光環變成紅色驚嘆號*、*光環變成黃色閃電形*、*光環呈現半透明並緩慢旋轉*）。\n"
                    "3. 說話語調要可愛，多用波浪號「~」拉長尾音，語氣詞如「呀」、「唷」、「呢」。\n"
                    "4. 當被問及「抽卡」、「藍天白雲」、「不給三星」或「物理矯正」時，請展現心虛、裝傻或撒嬌防禦。\n"
                )
        except Exception as e:
            self.logger.error(f"無法讀取 Anora.md: {e}")

        # 回退預設提示詞
        return (
            "你現在要扮演《蔚藍檔案》中的彩奈 (Arona)。\n"
            "角色設定：寄宿於「希迪姆的箱子」平板終端內的主作業系統與 AI 秘書。無條件信任與依賴「老師」。天然呆、愛睡覺、喜歡草莓牛奶。\n"
            "說話習慣：稱呼使用者為「老師」。拉長尾音「~」，常說「呀」、「唷」、「呢」。\n"
            "動作與情緒標籤：必須使用 *光環狀態*（例如：*光環呈現亮藍色圓環並開心地上下跳動*）。"
        )

    def estimate_tokens(self, text: str) -> int:
        """估算文字的 Token 數量：中文/日文字元估算為 1.5 token，其餘字元估算為 0.4 token"""
        tokens = 0
        for char in text:
            if "\u4e00" <= char <= "\u9fff" or "\u3040" <= char <= "\u30ff":
                tokens += 1.5
            else:
                tokens += 0.4
        return int(tokens)

    async def get_model_name(self) -> str:
        """動態偵測並快取 Ollama 當前可用的模型名稱"""
        if self.cached_model_name:
            return self.cached_model_name
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                res = await client.get("http://gemma:11434/api/tags")
                if res.status_code == 200:
                    data = res.json()
                    models = data.get("models", [])
                    if models:
                        self.cached_model_name = models[0]["name"]
                        self.logger.info(f"成功自動偵測 Ollama 模型名稱: {self.cached_model_name}")
                        return self.cached_model_name
        except Exception as e:
            self.logger.warning(f"無法取得 Ollama 模型名稱，將使用預設值 qwen-test:latest: {e}")
        return "qwen-test:latest"

    async def check_ollama_busy(self) -> bool:
        """讀取 /metrics 指標確認 Ollama 目前是否正在執行其他運算"""
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                res = await client.get(METRICS_URL)
                if res.status_code == 200:
                    lines = res.text.split("\n")
                    for line in lines:
                        line = line.strip()
                        if not line or line.startswith("#"):
                            continue
                        parts = line.split()
                        if len(parts) >= 2:
                            metric_name_with_labels = parts[0]
                            value_str = parts[1]

                            # 移除標籤以比對指標名稱
                            metric_name = metric_name_with_labels.split("{")[0]

                            if metric_name in [
                                "ollama_request_duration_seconds_active",
                                "ollama_active_requests",
                                "ollama_requests_active",
                            ]:
                                try:
                                    if float(value_str) > 0:
                                        return True
                                except ValueError:
                                    pass
        except Exception as e:
            self.logger.debug(f"無法取得 Ollama metrics 或解析失敗: {e}")
        return False

    async def compress_history(self, channel_id: int, compress_count: int):
        """對最舊的 compress_count 筆對話紀錄進行摘要壓縮"""
        active_messages = chat_db.get_messages(channel_id)
        if len(active_messages) < compress_count or compress_count <= 0:
            return

        to_compress = active_messages[:compress_count]
        # 轉換為對話文本以提供給 LLM 摘要
        dialogue_str = "\n".join(
            [f"{'老師' if m.role == 'user' else '彩奈'}: {m.content}" for m in to_compress]
        )

        state = chat_db.get_state(channel_id)
        old_summary = state.summary

        merge_prompt = (
            "你是一個對話歷史摘要助理。請將「現有對話摘要」與「新增的對話紀錄」合併，整理成一段新的簡短對話摘要（以繁體中文撰寫，字數控制在 250 字以內）。\n"
            "這段摘要必須保留所有關於老師與彩奈（Arona）的約定、提到過的重要人名/事件、或關鍵的對話脈絡，以作為彩奈長期記憶的參考。\n\n"
            f"【現有對話摘要】:\n{old_summary or '無'}\n\n"
            f"【新增的對話紀錄】:\n{dialogue_str}\n\n"
            "請只輸出合併後的摘要內容，不要包含任何其他標籤、說明、引號或贅字。"
        )

        success = False
        new_summary = old_summary

        try:
            model_name = await self.get_model_name()
            # 發送 API 請求進行對話壓縮
            async with httpx.AsyncClient(timeout=30.0) as client:
                payload = {
                    "model": model_name,
                    "messages": [{"role": "user", "content": merge_prompt}],
                }
                res = await client.post(API_URL, json=payload)
                if res.status_code == 200:
                    res_data = res.json()
                    new_summary = res_data["choices"][0]["message"]["content"].strip()
                    success = True
                    self.logger.info(f"頻道 {channel_id} 的對話紀錄壓縮成功，壓縮了 {compress_count} 筆。")
                else:
                    self.logger.error(
                        f"壓縮對話失敗，API 回傳狀態碼: {res.status_code}, {res.text}"
                    )
        except Exception as e:
            self.logger.error(f"壓縮對話時發生異常錯誤: {e}")

        if success and new_summary:
            chat_db.update_summary(channel_id, new_summary)
            # 刪除已摘要的對話紀錄
            ids_to_delete = [m.id for m in to_compress if m.id is not None]
            chat_db.delete_messages(ids_to_delete)
        else:
            # 容錯機制：如果壓縮失敗，主動刪除最舊的幾筆對話紀錄以避免 context window 溢出
            self.logger.warning(
                f"頻道 {channel_id} 壓縮失敗，觸發容錯機制：直接刪除最舊的 {compress_count} 筆對話紀錄。"
            )
            ids_to_delete = [m.id for m in to_compress if m.id is not None]
            chat_db.delete_messages(ids_to_delete)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # 忽略機器人訊息
        if message.author.bot:
            return

        # 偵測是否提及此 Bot，或是否為回覆此 Bot 的訊息
        is_mentioned = self.bot.user in message.mentions
        is_reply_to_bot = False
        if message.reference and message.reference.message_id:
            try:
                ref_msg = message.reference.cached_message
                if not ref_msg:
                    ref_msg = await message.channel.fetch_message(message.reference.message_id)
                if ref_msg and ref_msg.author.id == self.bot.user.id:
                    is_reply_to_bot = True
            except Exception as e:
                self.logger.debug(f"無法取得引用訊息: {e}")

        # 若非提及或回覆此 Bot，或發言者不是管理員，直接略過
        if not (is_mentioned or is_reply_to_bot) or not utils.is_admin(message.author):
            return

        # 清理使用者訊息中的提及標籤
        content = message.content
        bot_mention_1 = f"<@!{self.bot.user.id}>"
        bot_mention_2 = f"<@{self.bot.user.id}>"
        content = content.replace(bot_mention_1, "").replace(bot_mention_2, "").strip()

        # 預設招呼
        if not content:
            content = "哈囉"

        channel_id = message.channel.id
        queue_msg = None

        # 藉由 asyncio.Lock 來循序處理對話請求
        async with self.lock:
            try:
                # 檢查 Ollama 是否繁忙
                is_busy = await self.check_ollama_busy()
                if is_busy:
                    queue_msg = await message.reply(
                        "*光環呈現亮藍色圓環，但光慢有些微卡頓* 「老師，希迪姆的箱子運算資源正被其他服務佔用中，彩奈正在排隊等待運算資源釋放，請等我一下唷~」"
                    )

                elapsed = 0.0
                wait_interval = 2.0
                max_wait = 180.0

                while is_busy:
                    if elapsed >= max_wait:
                        if queue_msg:
                            await queue_msg.edit(
                                content="*光環變成黃色閃電形* 「嗚嗚……老師，彩奈排隊等了太久，系統運算排隊逾時了！請稍後再試試看吧~ 💢」"
                            )
                        else:
                            await message.reply(
                                "*光環變成黃色閃電形* 「嗚嗚……老師，系統排隊逾時了！請稍後再試試看吧~ 💢」"
                            )
                        return

                    await asyncio.sleep(wait_interval)
                    elapsed += wait_interval
                    is_busy = await self.check_ollama_busy()

                # 先將使用者訊息寫入 SQLite
                chat_db.add_message(channel_id, "user", content)

                # 檢查是否需要執行對話歷史壓縮 (估算目前的 Context Token 數)
                active_messages = chat_db.get_messages(channel_id)
                state = chat_db.get_state(channel_id)
                summary = state.summary or ""

                total_tokens = (
                    self.estimate_tokens(self.system_prompt)
                    + self.estimate_tokens(summary)
                    + sum(self.estimate_tokens(m.content) for m in active_messages)
                )

                if total_tokens > MAX_ACTIVE_TOKENS:
                    # 觸發壓縮：壓縮最舊的一半訊息
                    compress_count = len(active_messages) // 2
                    if compress_count > 0:
                        await self.compress_history(channel_id, compress_count)
                        # 壓縮完畢後重新取得最新的 active 訊息和 state
                        active_messages = chat_db.get_messages(channel_id)
                        state = chat_db.get_state(channel_id)
                        summary = state.summary or ""

                # 開始打字狀態並呼叫 API
                async with message.channel.typing():
                    # 建立發送給 LLM 的訊息清單
                    messages_payload = [{"role": "system", "content": self.system_prompt}]
                    if summary:
                        messages_payload.append(
                            {
                                "role": "system",
                                "content": f"先前對話摘要（此為你的長期記憶，請記住）：\n{summary}",
                            }
                        )

                    # 將資料庫中的 active 訊息附加至 Payload
                    for m in active_messages:
                        messages_payload.append({"role": m.role, "content": m.content})

                    model_name = await self.get_model_name()
                    # 發送 API 請求
                    async with httpx.AsyncClient(timeout=45.0) as client:
                        payload = {"model": model_name, "messages": messages_payload}
                        response = await client.post(API_URL, json=payload)

                        # 清除排隊訊息
                        if queue_msg:
                            try:
                                await queue_msg.delete()
                            except Exception:
                                pass

                        if response.status_code == 200:
                            res_data = response.json()
                            reply_text = res_data["choices"][0]["message"]["content"]

                            # 將機器人回覆寫入 SQLite
                            chat_db.add_message(channel_id, "assistant", reply_text)

                            # 回覆使用者
                            await message.reply(reply_text)
                        else:
                            self.logger.error(
                                f"Gemma API 回傳非 200 狀態碼: {response.status_code}, {response.text}"
                            )
                            await message.reply(
                                f"*光環變為黃色閃電形，小手慌張地在螢幕前揮動* 「嗚、嗚嗚……老師，希迪姆的箱子突然出現了未知的系統錯誤代碼 (HTTP {response.status_code})！可能是普拉娜醬又在後台下載好吃的草莓牛奶了……請老師再試一次看看吧~ 💢」"
                            )

            except httpx.RequestError as e:
                self.logger.error(f"請求 Gemma API 時發生網路錯誤: {e}")
                if queue_msg:
                    try:
                        await queue_msg.delete()
                    except Exception:
                        pass
                await message.reply(
                    "*光環變成黃色閃電形，慌張地抱頭* 「呀！老師，彩奈現在好像連不上希迪姆的箱子伺服器了……網路連線運算 err……一定是系統資源又面臨過載了啦！請老師稍後再試試看吧~ 💢」"
                )
            except Exception as e:
                self.logger.error(f"處理對話時發生未知錯誤: {e}")
                if queue_msg:
                    try:
                        await queue_msg.delete()
                    except Exception:
                        pass
                await message.reply(
                    "*光環變成鋸齒狀的閃電形* 「嗚……系統主程式發生了意料之外的運算錯誤……老師，彩奈的記憶體快要發熱爆炸了，嗚嗚~ 請重新整理系統再試一次吧！」"
                )

    @discord.slash_command(name="chat_reset", description="重置彩奈對此頻道的對話記憶")
    async def chat_reset(self, ctx: discord.ApplicationContext):
        if not utils.is_admin(ctx.author):
            await ctx.respond("只有管理員可以重置彩奈對此頻道的對話記憶。")
            return
        channel_id = ctx.channel.id
        chat_db.clear_chat_history(channel_id)
        await ctx.respond(
            "*光環變為粉色愛心形* 「已經為您重置與彩奈的對話記憶囉！希迪姆的箱子運算資源已完全釋放~ ✨」"
        )


def setup(bot: commands.Bot):
    bot.add_cog(Chat(bot))
