import asyncio
from aiohttp import web
from aiogram.types import Update

from bot_currency import bot_cur
from bot_notes import bot_notes

from bot_currency import dp_cur
from bot_notes import dp_notes


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
