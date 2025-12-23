import discord
from discord.ext import commands
from discord import sinks
from datetime import datetime
import utils
import os
import asyncio
import shutil
from io import BytesIO
from pydub import AudioSegment

class Record(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = utils.get_logger('record')
        self.connections = {}
        self.recording_data = {}
        # 確保錄音目錄存在
        self.recordings_dir = utils.TMP_DIR
        os.makedirs(self.recordings_dir, exist_ok=True)
        
    @commands.Cog.listener()
    async def on_ready(self):
        self.logger.info("Record Cog is ready.")
    
    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        """監聽語音狀態更新以處理錄音"""
        if member.bot:
            return  # 忽略機器人
        
        # 用戶離開語音頻道
        elif before.channel and not after.channel:
            if before.channel.id == utils.WORKER_VOICE_CHANNEL_ID:
                voice_client = discord.utils.get(self.bot.voice_clients,
                                            guild=before.channel.guild)  # 機器人的語音頻道
                if voice_client and voice_client.channel == before.channel:
                    if len(before.channel.members) == 1:  # 頻道只剩機器人
                        vc = self.connections[before.channel.guild.id]
                        vc.stop_recording()
                        await vc.disconnect()
                        del self.connections[before.channel.guild.id]
            self.logger.info(f"{member.name} 離開了語音頻道 {before.channel.name}")
        
        # 用戶切換語音頻道
        elif before.channel and after.channel and before.channel != after.channel:
            self.logger.info(f"{member.name} 從 {before.channel.name} 切換到 {after.channel.name}")
    
    async def finished_callback(self, sink: sinks.WaveSink, *args):
        """錄音完成後的回調函數"""
        try:
            channel = self.bot.get_channel(utils.WORKER_CHANNEL_ID)

            def _to_bytes(blob):
                """將 AudioData/BytesIO/bytes 轉為 raw bytes"""
                if hasattr(blob, "file") and blob.file:
                    return blob.file.getvalue()
                if hasattr(blob, "getvalue"):
                    return blob.getvalue()
                try:
                    return bytes(blob)
                except Exception:
                    return b""

            def _to_audio_segment(blob):
                """將單段音訊轉為 AudioSegment 以便混音"""
                raw = _to_bytes(blob)
                bio = BytesIO(raw)
                return AudioSegment.from_file(bio, format=sink.encoding)
            
            recorded_users = []
            
            # 生成時間戳記
            timestamp = datetime.now().strftime("%Y%m%d-%H:%M")
            
            os.makedirs(f"{self.recordings_dir}/{timestamp} 開會紀錄", exist_ok=True)
            file_path = f"{self.recordings_dir}/{timestamp} 開會紀錄"
            user_tracks = []  # 用於後續混音
            
            
            # 為每個用戶收集音訊並建立軌道（不再輸出單獨檔案）
            for user_id, audio in sink.audio_data.items():
                user = self.bot.get_user(user_id)
                recorded_users.append(f"<@{user_id}>")

                audio_list = audio if isinstance(audio, list) else [audio]
                segments = [_to_audio_segment(chunk) for chunk in audio_list]
                if segments:
                    track = segments[0]
                    for seg in segments[1:]:
                        track += seg
                    user_tracks.append(track)

            if not user_tracks:
                await channel.send("❌ 沒有錄到任何聲音，未產出開會總紀錄")
                shutil.rmtree(file_path)
                return

            # 混音：將所有人完整軌道 overlay 成單一檔案（開會總紀錄）
            mixed = user_tracks[0]
            for track in user_tracks[1:]:
                mixed = mixed.overlay(track)

            mixed_filename = f"開會總紀錄.{sink.encoding}"
            mixed_path = f"{file_path}/{mixed_filename}"
            mixed.export(mixed_path, format=sink.encoding)
            
            shutil.make_archive(f"{timestamp} 開會紀錄", 'zip', file_path)
            await channel.send(
                content=f"✅ 錄音完成！已產出開會總紀錄，參與者：{', '.join(recorded_users)}",
                file=discord.File(f"{timestamp} 開會紀錄.zip", filename=f"{file_path}/{timestamp} 開會紀錄.zip"))
            
            
            
            shutil.rmtree(file_path)
            
        except Exception as e:
            self.logger.error(f"處理錄音檔案時發生錯誤：{e}")
            await channel.send(f"❌ 處理錄音時發生錯誤：{e}")
    
    @discord.slash_command(name="start", description="開始錄製語音頻道")
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
        
        # 檢查是否已經在錄音
        if ctx.guild.id in self.connections:
            await ctx.respond("❌ 此伺服器已經在錄音中！", ephemeral=True)
            return
        
        try:
            # 加入語音頻道
            vc = await voice_channel.connect()
            self.connections[ctx.guild.id] = vc
            
            # 開始錄音
            vc.start_recording(
                sinks.WaveSink(),
                self.finished_callback,
            )
            
            await ctx.respond(f"🎙️ 開始錄製 {voice_channel.mention}！使用 `/record stop` 停止錄製。")
            self.logger.info(f"開始在 {voice_channel.name} 錄音，由 {ctx.author.name} 觸發")
            
        except Exception as e:
            self.logger.error(f"開始錄音時發生錯誤：{e}")
            await ctx.respond(f"❌ 開始錄音時發生錯誤：{e}", ephemeral=True)
    
    @discord.slash_command(name="stop", description="停止錄製語音頻道")
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
        
        try:
            vc = self.connections[ctx.guild.id]
            
            # 停止錄音
            vc.stop_recording()
            await ctx.respond("⏹️ 正在停止錄音並處理檔案...")
            
            # 斷開連接
            await vc.disconnect()
            del self.connections[ctx.guild.id]
            
            self.logger.info(f"停止錄音，由 {ctx.author.name} 觸發")
            
        except Exception as e:
            self.logger.error(f"停止錄音時發生錯誤：{e}")
            await ctx.respond(f"❌ 停止錄音時發生錯誤：{e}", ephemeral=True)
    
    @discord.slash_command(name="status", description="查看錄音狀態")
    async def recording_status(self, ctx: discord.ApplicationContext):
        """查看當前錄音狀態"""
        if not self.__is_valid_request(ctx):
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
            except:
                pass
            
def setup(bot):
    bot.add_cog(Record(bot))