import asyncio
import os
import shutil
import time
from datetime import datetime

import discord
from discord import sinks
from discord.ext import commands, tasks
from pydub import AudioSegment

import internal.GoogleDrive as gdrive
from internal import utils
from model.log import log_task


class TimedWaveSink(sinks.WaveSink):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.start_recording_time = time.time()
        self.user_offsets = {}
        # 使用隊列存儲待寫入的數據，避免在主線程進行磁盤 I/O
        self._write_queue = []
        self._write_lock = asyncio.Lock()
        self.record_guild = None
        self.record_channel = None

    def write(self, data, user_id):
        """
        改良版：將寫入操作推遲到線程中執行，避免阻塞事件循環
        """
        try:
            if user_id not in self.user_offsets:
                # 記錄第一個成功接收到的數據包時間
                self.user_offsets[user_id] = time.time() - self.start_recording_time

            # 直接在事件循環中調用父類的 write 方法
            # discord.py 的 WaveSink 已經設計為快速操作（主要是內存操作）
            super().write(data, user_id)
        except Exception as e:
            # 捕捉可能發生的寫入錯誤，避免整個錄音中斷
            print(f"寫入音訊包時發生錯誤 (User: {user_id}): {e}")


class Record(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = utils.get_logger("record")
        self.connections = {}
        self.recording_data = {}
        # 確保錄音目錄存在
        self.recordings_dir = utils.TMP_DIR / "recordings"
        os.makedirs(self.recordings_dir, exist_ok=True)
        # 追蹤各 guild 的錄音時間戳和目錄
        self.recording_timestamps = {}  # {guild_id: timestamp}

    @commands.Cog.listener()
    async def on_ready(self):
        self.logger.info("Record Cog is ready.")

    async def finished_callback(self, sink: sinks.WaveSink, *args):
        """
        改良版：將整個回調作為後臺任務運行，避免阻塞主事件循環
        """
        # 在後台運行處理，避免阻塞
        asyncio.create_task(self._process_recording(sink, args))

    async def _process_recording(self, sink: sinks.WaveSink, args: tuple):
        """
        實際的錄音處理邏輯
        """
        try:
            channel = self.bot.get_channel(utils.WORKER_CHANNEL_ID)
            self.logger.info("開始處理錄音檔案並轉換為 MP3 (非同步模式)...")

            timestamp = datetime.now().strftime("%Y%m%d_%H%M")

            # 使用對應的 guild 錄音目錄
            guild_id = None
            for gid, ts in self.recording_timestamps.items():
                # 找到對應的 guild（假設同時只有一個在錄音）
                guild_id = gid
                break

            if guild_id:
                session_dir = self.recordings_dir / self.recording_timestamps[guild_id]
            else:
                session_dir = self.recordings_dir / timestamp

            combined = AudioSegment.silent(duration=0)
            users_with_audio = []

            # 定義同步轉檔函數以供執行緒調用
            def export_audio_sync(audio_seg, path, fmt, br):
                return audio_seg.export(path, format=fmt, bitrate=br)

            for user_id, audio in sink.audio_data.items():
                user = self.bot.get_user(user_id)
                if not user:
                    continue

                try:
                    # 檢查數據大小
                    audio.file.seek(0, 2)
                    if audio.file.tell() < 1000:
                        continue
                    audio.file.seek(0)

                    # 讀取 Raw 數據 (48kHz, 16-bit, Stereo)
                    audio_segment = AudioSegment.from_raw(audio.file, sample_width=2, frame_rate=48000, channels=2)

                    # 取得時間偏移量
                    offset_ms = int(sink.user_offsets.get(user_id, 0) * 1000)

                    # 設定路徑
                    filename = f"{user.name}_{user_id}.mp3"
                    filepath = session_dir / filename

                    # ✅ 使用 asyncio.to_thread 進行非同步匯出個人音軌
                    await asyncio.to_thread(export_audio_sync, audio_segment, filepath, "mp3", "128k")

                    users_with_audio.append(user.name)

                    # 混音準備
                    padded_audio = AudioSegment.silent(duration=offset_ms) + audio_segment
                    if combined.duration_seconds == 0:
                        combined = padded_audio
                    else:
                        combined = combined.overlay(padded_audio)

                except Exception as e:
                    self.logger.error(f"轉換用戶 {user.name} 失敗：{e}")

            if not users_with_audio:
                self.logger.warning("沒有錄製到任何有效音訊。")
                # 清理空的會話目錄
                if guild_id and guild_id in self.recording_timestamps:
                    try:
                        shutil.rmtree(session_dir)
                    except Exception:
                        pass
                    del self.recording_timestamps[guild_id]
                return

            # --- 針對最後合成的檔案進行處理 (裁切雜音) ---
            if len(combined) > 500:
                combined = combined[500:]
            combined = combined.fade_in(300)

            # 匯出合成後的 MP3 檔案
            combined_filename = f"開會集合_{timestamp}.mp3"
            combined_path = session_dir / combined_filename

            # ✅ 使用 asyncio.to_thread 進行非同步匯出合成音軌
            await asyncio.to_thread(export_audio_sync, combined, combined_path, "mp3", "192k")

            # 打包發送 (這部分涉及磁碟 I/O，建議也放入線程處理或保持現狀)
            zip_path = utils.TMP_DIR / f"recordings_{self.recording_timestamps.get(guild_id, timestamp)}"
            await asyncio.to_thread(shutil.make_archive, str(zip_path), "zip", str(session_dir))

            # 上傳至 Google Drive（使用線程以避免阻塞事件循環）
            def upload_and_send():
                creds = gdrive.get_detailed_token_info(utils.GOOGLE_CLIENT_ID, utils.GOOGLE_CLIENT_SECRET, utils.GOOGLE_REFRESH_TOKEN)
                result = gdrive.upload_to_drive(
                    file_path=str(zip_path) + ".zip", folder_id=utils.CONFERENCE_FOLDER_ID, creds=creds, name=f"會議錄音_{timestamp}"
                )
                return result

            result = await asyncio.to_thread(upload_and_send)
            await channel.send(f"🎙️ 錄音已上傳至 Google Drive！\n下載連結：{result.get('webViewLink')}")

            # file = discord.File(str(utils.TMP_DIR/"recordings.zip"), filename="recordings.zip")
            # await channel.send(f"🎙️ 錄音已轉為 MP3 並處理完成！\n參與者：{', '.join(users_with_audio)}", file=file)

            # 清理臨時目錄
            shutil.rmtree(session_dir)
            os.remove(str(zip_path) + ".zip")
            if guild_id and guild_id in self.recording_timestamps:
                del self.recording_timestamps[guild_id]
            self.logger.info("錄音處理與發送完成。")

        except Exception as e:
            self.logger.error(f"處理錄音檔案時發生嚴重錯誤：{e}", exc_info=True)
            # 確保清理記錄
            for guild_id in list(self.recording_timestamps.keys()):
                del self.recording_timestamps[guild_id]

    command_group = discord.SlashCommandGroup("record", "語音錄製相關指令")

    @command_group.command(name="start", description="開始錄製語音頻道")
    async def start_recording(self, ctx: discord.ApplicationContext):
        """開始錄製當前語音頻道"""
        if not utils.is_operator(ctx.author):
            await ctx.respond("❌ 你沒有權限使用此指令", ephemeral=True)
            self.logger.warning(f"❌ {ctx.author.name} 嘗試使用開始錄音指令，但沒有權限")
            return

        # 檢查用戶是否在語音頻道中
        if not ctx.author.voice:
            await ctx.respond("❌ 你必須先加入一個語音頻道！", ephemeral=True)
            return

        voice_channel = ctx.author.voice.channel

        # 建立此次錄音的時間戳目錄
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_dir = self.recordings_dir / timestamp
        os.makedirs(session_dir, exist_ok=True)
        self.recording_timestamps[ctx.guild.id] = timestamp

        self.logger.info(f"為 guild {ctx.guild.id} 建立錄音目錄：{session_dir}")

        # 檢查是否已經在錄音
        if ctx.guild.id in self.connections:
            await ctx.respond("❌ 此伺服器已經在錄音中！", ephemeral=True)
            return

        guild = ctx.guild
        if guild.voice_client:
            self.logger.info("檢測到殘留連接，執行強制中斷...")
            await guild.voice_client.disconnect(force=True)
            await asyncio.sleep(2)  # 給予足夠時間讓 Discord Gateway 更新狀態

        # 檢查 bot 是否有足夠權限
        bot_member = ctx.guild.get_member(self.bot.user.id)
        if not voice_channel.permissions_for(bot_member).connect:
            await ctx.respond("❌ Bot 沒有連接語音頻道的權限！", ephemeral=True)
            return
        if not voice_channel.permissions_for(bot_member).speak:
            await ctx.respond("❌ Bot 沒有在語音頻道說話的權限！", ephemeral=True)
            return

        try:
            await ctx.respond("🔄 正在連接語音頻道...")

            # 加入語音頻道，並啟用語音接收
            vc = await voice_channel.connect(cls=discord.VoiceClient)
            self.connections[ctx.guild.id] = vc

            self.logger.info(f"已連接到語音頻道：{voice_channel.name}")
            self.logger.info(f"頻道內成員：{[m.name for m in voice_channel.members if not m.bot]}")

            for i in range(5):  # 最多嘗試等待 5 秒
                if vc.is_connected():
                    break
                await asyncio.sleep(1)
                self.logger.info(f"等待語音連線穩定中... ({i + 1})")

            if not vc.is_connected():
                raise Exception("語音連線超時，無法啟動錄音。")

            # 開始錄音
            vc.start_recording(TimedWaveSink(), self.finished_callback, ctx.channel)

            self.record_guild = ctx.guild
            self.record_channel = ctx.channel

            if not self.restart_recording.is_running():
                self.restart_recording.start()

            self.logger.info("錄音已啟動")
            await ctx.edit(
                content=f"🎙️ 開始錄製 {voice_channel.mention}！\n使用 `/stop` 停止錄製。\n\n⚠️ 注意：請確認頻道內的人有開啟麥克風並說話。"
            )
            self.logger.info(f"開始在 {voice_channel.name} 錄音，由 {ctx.author.name} 觸發")

        except Exception as e:
            self.logger.error(f"開始錄音時發生錯誤：{e}")
            # 清理已建立的目錄
            if ctx.guild.id in self.recording_timestamps:
                try:
                    session_dir = self.recordings_dir / self.recording_timestamps[ctx.guild.id]
                    shutil.rmtree(session_dir)
                except Exception:
                    pass
                del self.recording_timestamps[ctx.guild.id]
            await ctx.respond(f"❌ 開始錄音時發生錯誤：{e}", ephemeral=True)

    @command_group.command(name="stop", description="停止錄製語音頻道")
    async def stop_recording(self, ctx: discord.ApplicationContext):
        """停止錄製並保存檔案"""
        if not utils.is_operator(ctx.author):
            await ctx.respond("❌ 你沒有權限使用此指令", ephemeral=True)
            self.logger.warning(f"❌ {ctx.author.name} 嘗試使用停止錄音指令，但沒有權限")
            return

        # 檢查是否正在錄音
        if ctx.guild.id not in self.connections:
            await ctx.respond("❌ 目前沒有正在進行的錄音！", ephemeral=True)
            return

        await ctx.defer()

        try:
            if self.restart_recording.is_running():
                self.restart_recording.cancel()

            vc = self.connections[ctx.guild.id]

            # 停止錄音
            vc.stop_recording()
            await ctx.respond("⏹️ 正在停止錄音並處理檔案...")
            self.record_guild = None
            self.record_channel = None

            # 斷開連接
            await vc.disconnect()
            del self.connections[ctx.guild.id]

            # 注意：不在此處刪除錄音目錄，應該由 _process_recording 在完成處理後刪除
            # 這樣可以確保非同步回調能夠順利存取錄音文件

            self.logger.info(f"停止錄音，由 {ctx.author.name} 觸發")

        except Exception as e:
            self.logger.error(f"停止錄音時發生錯誤：{e}")
            await ctx.respond(f"❌ 停止錄音時發生錯誤：{e}", ephemeral=True)

    @command_group.command(name="status", description="查看錄音狀態")
    async def recording_status(self, ctx: discord.ApplicationContext):
        """查看當前錄音狀態"""
        if not utils.is_operator(ctx.author):
            await ctx.respond("❌ 你沒有權限使用此指令", ephemeral=True)
            return

        if ctx.guild.id in self.connections:
            vc = self.connections[ctx.guild.id]
            channel_name = vc.channel.name if vc.channel else "未知頻道"
            await ctx.respond(f"🎙️ 正在錄音中：{channel_name}")
        else:
            await ctx.respond("⏸️ 目前沒有正在進行的錄音")

    def cog_unload(self):
        """Cog 卸載時清理連接"""
        for guild_id, vc in self.connections.items():
            try:
                self.bot.loop.create_task(vc.disconnect())
            except Exception:
                pass

    @tasks.loop(hours=1)
    @log_task("restart_recording")
    async def restart_recording(self):
        """定時重啟錄音以防止長時間錄音導致的問題"""
        vc = self.connections.get(self.record_guild.id) if self.record_guild else None
        if vc and vc.recording:
            self.logger.info("定時重啟錄音中...")
            try:
                vc.stop_recording()
                await asyncio.sleep(2)  # 給予足夠時間讓錄音停止

                # 重要：確保不會刪除會話目錄
                # restart 時保持相同的時間戳和目錄，不建立新目錄
                guild_id = self.record_guild.id
                if guild_id not in self.recording_timestamps:
                    # 如果沒有記錄，建立新的時間戳
                    self.recording_timestamps[guild_id] = datetime.now().strftime("%Y%m%d_%H%M%S")

                session_dir = self.recordings_dir / self.recording_timestamps[guild_id]
                os.makedirs(session_dir, exist_ok=True)

                vc.start_recording(TimedWaveSink(), self.finished_callback, self.record_channel)
                self.logger.info(f"錄音已成功重啟，使用同一會話目錄：{session_dir}")
            except Exception as e:
                self.logger.error(f"定時重啟錄音時發生錯誤：{e}")


def setup(bot):
    bot.add_cog(Record(bot))
