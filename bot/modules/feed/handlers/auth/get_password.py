from typing import Any

from extensions.handlers.message.base import BaseHandler
from services.gkfeed_auth import GkfeedAuthService
from modules.feed.handlers.auth._states import FSM


class PasswordHandler(BaseHandler):
    async def handle(self) -> Any:
        await self.state.set_state(FSM.finish)
        await self.event.delete()

        if self.event.text is None:
            raise ValueError("event.text is None")
        if self.event.from_user is None:
            raise ValueError("event.from_user is None")

        data = await self.state.get_data()
        login = data.get("login")
        if not login:
            raise ValueError("'login' not in state data")

        if await GkfeedAuthService().login(
            user_id=self.event.from_user.id,
            login=login,
            password=self.event.text,
        ):
            await self.event.answer("Successfully logged in!")
        else:
            await self.event.answer("Invalid password.")
