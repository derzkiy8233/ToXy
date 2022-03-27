import asyncio
import atexit
import functools
import logging
import os
import subprocess
import sys
import uuid
import telethon

import git
from git import Repo, GitCommandError
from telethon.tl.types import Message

from .. import loader, utils

logger = logging.getLogger(__name__)


@loader.tds
class UpdaterMod(loader.Module):
    """Updates itself"""

    strings = {
        "name": "Updater",
        "source": "ℹ️ <b>Read the source code from</b> <a href='{}'>here</a>",
        "restarting_caption": "🔄 <b>Restarting...</b>",
        "downloading": "🔄 <b>Downloading updates...</b>",
        "downloaded": "✅ <b>Downloaded successfully.\nPlease type</b> \n<code>.restart</code> <b>to restart the bot.</b>",
        "installing": "🔁 <b>Installing updates...</b>",
        "success": "✅ <b>Restart successful!</b>",
        "origin_cfg_doc": "Git origin URL, for where to update from",
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            "GIT_ORIGIN_URL",
            "https://github.com/hikariatama/Hikka",
            lambda m: self.strings("origin_cfg_doc", m),
        )

    @loader.owner
    async def restartcmd(self, message: Message) -> None:
        """Restarts the userbot"""
        msg = (
            await utils.answer(message, self.strings("restarting_caption", message))
        )[0]
        await self.restart_common(msg)

    async def prerestart_common(self, message: Message) -> None:
        logger.debug(f"Self-update. {sys.executable} -m {utils.get_base_dir()}")

        check = str(uuid.uuid4())
        self._db.set(__name__, "selfupdatecheck", check)
        await asyncio.sleep(3)
        if self._db.get(__name__, "selfupdatecheck", "") != check:
            raise ValueError("An update is already in progress!")
        self._db.set(__name__, "selfupdatechat", utils.get_chat_id(message))
        self._db.set(__name__, "selfupdatemsg", message.id)

    async def restart_common(self, message: Message) -> None:
        await self.prerestart_common(message)
        atexit.register(functools.partial(restart, *sys.argv[1:]))
        handler = logging.getLogger().handlers[0]
        handler.setLevel(logging.CRITICAL)
        for client in self.allclients:
            # Terminate main loop of all running clients
            # Won't work if not all clients are ready
            if client is not message.client:
                await client.disconnect()
        await message.client.disconnect()

    
