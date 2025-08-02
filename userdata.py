import discord
from discord.ext import commands, bridge, tasks
import csv
TOKEN = "OTk3MjAyMzk4NDg3NTE5MzAz.GSH0uw.dHWYigfeu43GUZMD9pM9hozr-hN8UjKlHq6nQ8"

bot = commands.Bot(command_prefix=".", intents=discord.Intents.all())
data = []
data.append(['名字',"Threads名字","自我介紹"])

@bot.event
async def on_ready():
    print(f"✅ 已登入為 {bot.user}")
    
    # 取得論壇頻道
    channel = bot.get_channel(1357295240326938694)
    
    if isinstance(channel, discord.ForumChannel):
        print(f"✅ 成功取得論壇頻道: {channel.name}")
        
        # 抓取所有 threads（包括已封存和未封存的）
        print("\n🔄 正在抓取所有 threads...")
        all_threads = await get_all_threads(channel)
        print(f"✅ 總共找到 {len(all_threads)} 個 threads")
        for i in all_threads:
            first_message = None
            async for msg in i.history(limit=1, oldest_first=True):
                first_message = msg
                break
            try:
                data.append([i.owner.name,i.name,first_message.content])
            except:
                try:
                    data.append(["用戶興嘉大興嘉大",i.name,first_message.content])
                except:
                    data.append(["用戶興嘉大興嘉大",i.name,"找不到自我介紹"])
                print(f"❌ 找不到 {i.name} 的自我介紹, ID: {i.id}")
        # 分類顯示
        with open('data.csv', 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerows(data)
        active_threads = [t for t in all_threads if not t.archived]
        archived_threads = [t for t in all_threads if t.archived]
        
        print(f"📊 活躍 threads: {len(active_threads)} 個")
        print(f"📦 已封存 threads: {len(archived_threads)} 個")
        
        # 顯示前 10 個 threads 的詳細資訊
        print("\n📋 前 10 個 threads 詳細資訊:")
        for i, thread in enumerate(all_threads[:10], 1):
            status = "🟢 活躍" if not thread.archived else "🔴 已封存"
            print(f"{i}. {thread.name} (ID: {thread.id})")
            print(f"   {status} | 訊息數: {thread.message_count} | 建立者: {thread.owner.name if thread.owner else '未知'}")
            print(f"   建立時間: {thread.created_at.strftime('%Y-%m-%d %H:%M')}")
            print("---")
            
    else:
        print("❌ 該頻道不是論壇頻道或頻道不存在")

async def get_all_threads(channel:discord.ForumChannel):
    """取得頻道中所有的 threads（包括已封存和未封存的）"""
    all_threads = []
    
    # 1. 取得活躍的 threads
    print("📋 正在取得活躍的 threads...")
    active_threads = channel.threads
    all_threads.extend(active_threads)
    
    print(f"✅ 找到 {len(active_threads)} 個活躍 threads")
    
    # 2. 取得已封存的 threads
    print("📦 正在取得已封存的 threads...")
    archived_threads = await channel.archived_threads(limit=None).flatten()
    all_threads.extend(archived_threads)
    print(f"✅ 找到 {len(archived_threads)} 個已封存 threads")
    
    # 3. 移除重複的 threads（如果有）
    unique_threads = []
    seen_ids = set()
    for thread in all_threads:
        if thread.id not in seen_ids:
            unique_threads.append(thread)
            seen_ids.add(thread.id)
    
    print(f"✅ 去重後總共有 {len(unique_threads)} 個唯一 threads")
    return unique_threads

# @bot.command()
# async def all_threads(ctx):
#     """顯示頻道中所有的 threads"""
#     if isinstance(ctx.channel, discord.ForumChannel):
#         await ctx.send("🔄 正在抓取所有 threads...")
        
#         # 取得所有 threads
#         all_threads = await get_all_threads(ctx.channel)
        
#         # 分類統計
#         active_count = len([t for t in all_threads if not t.archived])
#         archived_count = len([t for t in all_threads if t.archived])
        
#         # 計算總訊息數
#         total_messages = sum(thread.message_count for thread in all_threads)
        
#         # 建立統計資訊
#         embed = discord.Embed(title="📊 論壇頻道完整統計", color=0x00ff00)
#         embed.add_field(name="總 Threads", value=len(all_threads), inline=True)
#         embed.add_field(name="活躍 Threads", value=active_count, inline=True)
#         embed.add_field(name="已封存 Threads", value=archived_count, inline=True)
#         embed.add_field(name="總訊息數", value=total_messages, inline=True)
        
#         # 顯示最近的 threads
#         if all_threads:
#             recent_threads = sorted(all_threads, key=lambda x: x.created_at, reverse=True)[:5]
#             threads_text = "\n".join([
#                 f"• {thread.name} ({'🟢' if not thread.archived else '🔴'})" 
#                 for thread in recent_threads
#             ])
#             embed.add_field(name="最近的 Threads", value=threads_text, inline=False)
        
#         await ctx.send(embed=embed)
#     else:
#         await ctx.send("❌ 此命令只能在論壇頻道中使用")

# @bot.command()
# async def thread_list(ctx, limit: int = 20):
#     """列出指定數量的 threads"""
#     if isinstance(ctx.channel, discord.ForumChannel):
#         if limit > 50:
#             await ctx.send("❌ 一次最多只能列出 50 個 threads")
#             return
            
#         await ctx.send(f"🔄 正在抓取前 {limit} 個 threads...")
        
#         # 取得所有 threads 並按建立時間排序
#         all_threads = await get_all_threads(ctx.channel)
#         sorted_threads = sorted(all_threads, key=lambda x: x.created_at, reverse=True)[:limit]
        
#         if sorted_threads:
#             threads_text = ""
#             for i, thread in enumerate(sorted_threads, 1):
#                 status = "🟢" if not thread.archived else "🔴"
#                 threads_text += f"{i}. {status} {thread.name}\n"
#                 threads_text += f"   ID: {thread.id} | 訊息: {thread.message_count}\n"
#                 threads_text += f"   建立者: {thread.owner.name if thread.owner else '未知'}\n"
#                 threads_text += f"   時間: {thread.created_at.strftime('%Y-%m-%d %H:%M')}\n\n"
            
#             # 如果內容太長，分段發送
#             if len(threads_text) > 2000:
#                 chunks = [threads_text[i:i+1900] for i in range(0, len(threads_text), 1900)]
#                 for i, chunk in enumerate(chunks, 1):
#                     embed = discord.Embed(title=f"Threads 列表 (第 {i} 部分)", description=chunk, color=0x00ff00)
#                     await ctx.send(embed=embed)
#             else:
#                 embed = discord.Embed(title="Threads 列表", description=threads_text, color=0x00ff00)
#                 await ctx.send(embed=embed)
#         else:
#             await ctx.send("❌ 沒有找到任何 threads")
#     else:
#         await ctx.send("❌ 此命令只能在論壇頻道中使用")

# @bot.command()
# async def search_all_threads(ctx, keyword: str):
#     """在所有 threads 中搜尋關鍵字"""
#     if isinstance(ctx.channel, discord.ForumChannel):
#         await ctx.send(f"🔍 正在所有 threads 中搜尋 '{keyword}'...")
        
#         # 取得所有 threads
#         all_threads = await get_all_threads(ctx.channel)
        
#         # 搜尋包含關鍵字的 threads
#         matching_threads = []
#         for thread in all_threads:
#             if keyword.lower() in thread.name.lower():
#                 matching_threads.append(thread)
        
#         if matching_threads:
#             # 按建立時間排序
#             matching_threads.sort(key=lambda x: x.created_at, reverse=True)
            
#             threads_text = ""
#             for thread in matching_threads[:10]:  # 最多顯示 10 個
#                 status = "🟢" if not thread.archived else "🔴"
#                 threads_text += f"• {status} {thread.name}\n"
#                 threads_text += f"  ID: {thread.id} | 建立者: {thread.owner.name if thread.owner else '未知'}\n\n"
            
#             embed = discord.Embed(title=f"搜尋結果: '{keyword}'", description=threads_text, color=0x00ff00)
#             embed.set_footer(text=f"找到 {len(matching_threads)} 個結果")
#             await ctx.send(embed=embed)
#         else:
#             await ctx.send(f"❌ 在所有 threads 中找不到包含 '{keyword}' 的結果")
#     else:
#         await ctx.send("❌ 此命令只能在論壇頻道中使用")

bot.run(TOKEN)