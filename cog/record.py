import discord
from discord.ext import commands
from discord import sinks
from datetime import datetime
import utils
import os
import asyncio
import shutil
import io
from pydub import AudioSegment

class Record(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = utils.get_logger('record')
        self.connections = {}
        self.recording_data = {}
        # 確保錄音目錄存在
        self.recordings_dir = utils.TMP_DIR/"recordings"
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
            self.logger.info("開始處理錄音檔案...")
            timestamp = datetime.now().strftime("%Y%m%d_%H:%M")
            combined = AudioSegment.silent(duration=0)
            users = []
            
            start_times = [data.start_time for data in sink.audio_data.values()]
            base_time = min(start_times) if start_times else 0
            
            for user_id, audio in sink.audio_data.items():
                user = self.bot.get_user(user_id)
                if not user:
                    self.logger.warning(f"無法找到用戶 ID {user_id}，跳過錄音處理")
                    continue
                users.append(user.name)
                
                # 生成檔案名稱
                filename = f"{user.name}_{user_id}.wav"
                filepath = self.recordings_dir / filename
                
                # 將錄音資料寫入檔案
                filecontext = audio.file.read()
                with open(filepath, 'wb') as f:
                    f.write(filecontext)
                
                self.logger.info(f"已保存錄音檔案：{filepath}")
                
                # 疊加音軌
                audio_segment = AudioSegment.from_file(audio.file, format="wav")
                offset_ms = (audio.start_time - base_time) * 1000  # 轉換為毫秒
                
                silence = AudioSegment.silent(duration=offset_ms)
                padded_audio = silence + audio_segment
                
                if combined.duration_seconds == 0:
                    combined = padded_audio
                else:
                    combined = combined.overlay(padded_audio)
                    
            combined_filename = f"開會集合_{timestamp}.wav"
            combined_path = self.recordings_dir / combined_filename
            combined.export(combined_path, format="wav")
            
            shutil.make_archive(str(utils.TMP_DIR/"recordings"), 'zip', self.recordings_dir)
            file = discord.File(str(utils.TMP_DIR/"recordings.zip"), filename="recordings.zip")
            await channel.send(f"錄音檔案已準備好，參與者：{', '.join(users)}", file=file)
        
        except Exception as e:
            self.logger.error(f"處理錄音檔案時發生錯誤：{e}")
            

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
        os.makedirs(self.recordings_dir, exist_ok=True)
        
        # 檢查是否已經在錄音
        if ctx.guild.id in self.connections:
            await ctx.respond("❌ 此伺服器已經在錄音中！", ephemeral=True)
            return
        
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
            
            # 開始錄音
            vc.start_recording(
                sinks.WaveSink(),
                self.finished_callback,
                ctx.channel
            )
            
            self.logger.info("錄音已啟動")
            await ctx.edit(content=f"🎙️ 開始錄製 {voice_channel.mention}！\n使用 `/stop` 停止錄製。\n\n⚠️ 注意：請確認頻道內的人有開啟麥克風並說話。")
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