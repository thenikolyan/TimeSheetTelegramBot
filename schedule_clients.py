import asyncio
import aioschedule

from handlers import clients


async def schedule_run():
    aioschedule.every().day.at("18:00").do(clients.over_work)
    while True:
        await aioschedule.run_pending()
        await asyncio.sleep(1)
