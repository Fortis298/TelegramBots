import asyncio
import asyncpg
import aiohttp
from aiohttp import web
from aiogram.types import Update

# БОТЫ
from bot_currency import bot_cur
from bot_notes import bot_notes

# ДИСПЕЧЕРЫ
from bot_currency import dp_cur
from bot_notes import dp_notes


# db
from bot_notes import BD_NOTES


async def tg_webhook_cur(request):
  data = await request.json()
  update = Update(**data)
  await dp_cur.feed_update(bot_cur, update)
  return web.Response(text="ok")  
    
async def tg_webhook_notes(request):
  data = await request.json()
  update = Update(**data)
  await dp_notes.feed_update(bot_notes, update)
  return web.Response(text="ok")  

async def uptime_robot(request):
  return web.Response(text="ok")  

async def main():
  import bot_currency
  bot_currency.session_global = aiohttp.ClientSession()
  
  pool_main = await asyncpg.create_pool(BD_NOTES)
  
  import bot_notes
  bot_notes.pool = pool_main
  
  app = web.Application()
  app.router.add_post("/webhook/bot_cur", tg_webhook_cur)
  app.router.add_post("/webhook/bot_notes", tg_webhook_notes)
  app.router.add_get("/", uptime_robot)

  runner = web.AppRunner(app)
  await runner.setup()
  site = web.TCPSite(runner, "0.0.0.0", 8080)
  await site.start()
  
  await asyncio.Event().wait()


asyncio.run(main())
