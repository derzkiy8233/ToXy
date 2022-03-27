
import json
import logging

import telethon
from babel import negotiate_locale
from telethon.tl.types import MessageEntityHashtag

logger = logging.getLogger(__name__)

MAGIC = "#hikka_translate_pack"


class Translator:
    def __init__(self, packs, languages, data_root):
        self._packs = packs
        self._languages = languages
        self._data_root = data_root

    async def init(self, client):
        self._data = {}
        for pack in self._packs:
            try:
                [message] = await client.get_messages(pack, 1)
            except (ValueError, telethon.errors.rpcerrorlist.ChannelPrivateError):
                # We can't access the channel
                logger.warning(
                    "No translation pack found for %r", pack, exc_info=True
                )
                continue
            if not message.document or not message.entities:
                logger.info(
                    "Last message in translation pack %r has no document/entities",
                    pack,
                )
                continue
            found = False
            for ent in filter(
                lambda x: isinstance(x, MessageEntityHashtag), message.entities
            ):
                if (
                    message.message[ent.offset : ent.offset + ent.length] == MAGIC
                    and message.file
                ):
                    logger.debug("Got translation message")
                    found = True
                    break
            if not found:
                logger.info("Didn't find translation hashtags")
                continue
            try:
                ndata = json.loads(
                    (await message.download_media(bytes)).decode("utf-8")
                )
            except (json.decoder.JSONDecodeError, UnicodeDecodeError):
                logger.exception("Unable to decode %s", pack)
                continue
            try:
                self._data.setdefault(ndata["language"], {}).update(ndata["data"])
            except KeyError:
                logger.exception("Translation pack follows wrong format")

    def set_preferred_languages(self, languages):
        self._languages = languages

    def getkey(self, key, lang_code=None):
        locales = []
        for locale, strings in self._data.items():
            if key in strings:
                locales += [locale]
        target_locales = [lang_code] if lang_code else self._languages
        locale = negotiate_locale(target_locales, locales)
        return self._data.get(locale, {}).get(key, False)

    def gettext(self, english_text):
        return self.getkey(english_text) or english_text
