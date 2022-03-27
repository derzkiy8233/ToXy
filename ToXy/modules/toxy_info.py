from .. import loader, main, utils
import logging
import aiogram
import git

from telethon.utils import get_display_name
from ..inline import InlineQuery, rand

logger = logging.getLogger(__name__)


@loader.tds
class HikkaInfoMod(loader.Module):
    """Show userbot info"""

    strings = {"name": "ToXy info"}

    def get(self, *args) -> dict:
        return self._db.get(self.strings["name"], *args)

    def set(self, *args) -> None:
        return self._db.set(self.strings["name"], *args)

    async def client_ready(self, client, db) -> None:
        self._db = db
        self._client = client
        self._me = await client.get_me()
        self.markup = aiogram.types.inline_keyboard.InlineKeyboardMarkup()
        self.markup.row(
            aiogram.types.inline_keyboard.InlineKeyboardButton(
                "🤵‍♀️ Support", url="https://t.me/ToXicUse"
            )
        )

    async def info_inline_handler(self, query: InlineQuery) -> None:
        """
        Send userbot info
        @allow: all
        """

        try:
            repo = git.Repo()
            ver = repo.heads[0].commit.hexsha
        except Exception:
            ver = "unknown"

        try:
            diff = repo.git.log(["HEAD..origin/alpha", "--oneline"])
            upd = (
                "⚠️ Update required </b><code>.update</code><b>"
                if diff
                else "✅ Up-to-date"
            )
        except Exception:
            upd = ""

        await query.answer(
            [
                aiogram.types.inline_query_result.InlineQueryResultArticle(
                    id=rand(20),
                    title="Send userbot info",
                    description="ℹ This will not compromise any sensitive data",
                    input_message_content=aiogram.types.input_message_content.InputTextMessageContent(
                        (
                            "<b>👩‍🎤 Toxy Userbot</b>"
                            f"<b>🤴 Owner: <a href=\"tg://user?id={self._me.id}\">{get_display_name(self._me)}</a></b>\n"
                            f"<b>🔮 Version: </b><i>{'.'.join(list(map(str, list(main.__version__))))}</i>"
                            f"<b>🧱 Build: </b><a href=\"https://github.com/hikariatama/Hikka/commit/{ver}\">{ver[:8] or 'Unknown'}</a>"
                            f"<b>{upd}</b>"
                            f"<b>{utils.get_named_platform()}</b>"
                        ),
                        "HTML",
                        disable_web_page_preview=True,
                    ),
                    thumb_url="https://github.com/hikariatama/Hikka/raw/master/assets/hikka_pfp.png",
                    thumb_width=128,
                    thumb_height=128,
                    reply_markup=self.markup,
                )
            ],
            cache_time=0,
        )
