import asyncio
import aioschedule as schedule
import time


class Schedule:
    def __init__(self):
        self.tasks = []

    def add_task(self, func):
        self.tasks.append(func)

    def start(self):
        pass


async def job(message='stuff', n=1):
    print("I'm working on:", message)
    await asyncio.sleep(1)


if __name__ == '__main__':
    schedule.every().day.at("15:21").do(job)

    loop = asyncio.get_event_loop()
    while True:
        loop.run_until_complete(schedule.run_pending())
        time.sleep(1)
