from telethon.tl.types import Message, Channel

from .. import loader, main, utils


@loader.tds
class CoreMod(loader.Module):
    """Control core userbot settings"""

    strings = {
        "name": "Settings",
        "too_many_args": "🚫 <b>Too many args</b>",
        "blacklisted": "✅ <b>Чат {} добавлен в черный список Токси!</b>",
        "unblacklisted": "✅ <b>Чат {} больше не в черном списке!</b>",
        "user_blacklisted": "✅ <b>Юзер {} добавлен в черный список Токси!</b>",
        "user_unblacklisted": "✅ <b>Юзер {} больше не в черном списке!</b>",
        "what_prefix": "❓ <b>Какой префикс ставить то?</b>",
        "prefix_incorrect": "🚫 <b>Prefix must be one symbol in length</b>",
        "prefix_set": "✅ <b>Префикс установлен. Напиши</b> <code>{newprefix}setprefix {oldprefix}</code> <b>чтобы вернуть обратно</b>",
        "alias_created": "✅ <b>Алиас создал. Access it with</b> <code>{}</code>",
        "aliases": "<b>Алиасы:</b>\n",
        "no_command": "🚫 <b>Command</b> <code>{}</code> <b>does not exist</b>",
        "alias_args": "🚫 <b>You must provide a command and the alias for it</b>",
        "delalias_args": "🚫 <b>You must provide the alias name</b>",
        "alias_removed": "✅ <b>Алиас</b> <code>{}</code> <b>удален.",
        "no_alias": "<b>🚫 Alias</b> <code>{}</code> <b>does not exist</b>",
        "no_pack": "<b>❓ What translation pack should be added?</b>",
        "bad_pack": "<b>🚫 Invalid translation pack specified</b>",
        "trnsl_saved": "<b>✅ Translation pack added</b>",
        "packs_cleared": "<b>✅ Translations cleared</b>",
        "lang_set": "<b>✅ Язык установлен</b>",
        "db_cleared": "<b>✅ Датабаза очищена</b>",
        "hikka": "👩‍🎤 <b>You are Toxic!</b>\n<b>ToXy version: {}.{}.{}</b>",
    }

    async def client_ready(self, client, db):
        self._db = db
        self._client = client

    async def blacklistcommon(self, message: Message) -> None:
        args = utils.get_args(message)

        if len(args) > 2:
            await utils.answer(message, self.strings("too_many_args", message))
            return

        chatid = None
        module = None

        if args:
            try:
                chatid = int(args[0])
            except ValueError:
                module = args[0]

        if len(args) == 2:
            module = args[1]

        if chatid is None:
            chatid = utils.get_chat_id(message)

        module = self.allmodules.get_classname(module)
        return f"{str(chatid)}.{module}" if module else chatid

    async def toxycmd(self, message: Message) -> None:
        """Get Hikka version"""
        ver = getattr(main, "__version__", False)
        
        await utils.answer(message, self.strings("hikka").format(*ver))

    async def blacklistcmd(self, message: Message) -> None:
        """Blacklist the bot from operating somewhere"""
        chatid = await self.blacklistcommon(message)

        self._db.set(
            main.__name__,
            "blacklist_chats",
            self._db.get(main.__name__, "blacklist_chats", []) + [chatid],
        )

        await utils.answer(message, self.strings("blacklisted", message).format(chatid))

    async def unblacklistcmd(self, message: Message) -> None:
        """Unblacklist the bot from operating somewhere"""
        chatid = await self.blacklistcommon(message)

        self._db.set(
            main.__name__,
            "blacklist_chats",
            list(
                set(self._db.get(main.__name__, "blacklist_chats", [])) - set([chatid])  # skipcq: PTC-W0018
            ),
        )

        await utils.answer(
            message, self.strings("unblacklisted", message).format(chatid)
        )

    async def getuser(self, message: Message) -> None:
        try:
            return int(utils.get_args(message)[0])
        except (ValueError, IndexError):
            reply = await message.get_reply_message()

            if reply:
                return (await message.get_reply_message()).sender_id

            if message.is_private:
                return message.to_id.user_id

            await utils.answer(message, self.strings("who_to_unblacklist", message))
            return

    async def blacklistusercmd(self, message: Message) -> None:
        """Prevent this user from running any commands"""
        user = await self.getuser(message)

        self._db.set(
            main.__name__,
            "blacklist_users",
            self._db.get(main.__name__, "blacklist_users", []) + [user],
        )

        await utils.answer(
            message, self.strings("user_blacklisted", message).format(user)
        )

    async def unblacklistusercmd(self, message: Message) -> None:
        """Allow this user to run permitted commands"""
        user = await self.getuser(message)

        self._db.set(
            main.__name__,
            "blacklist_users",
            list(set(self._db.get(main.__name__, "blacklist_users", [])) - set([user])),  # skipcq: PTC-W0018
        )

        await utils.answer(
            message, self.strings("user_unblacklisted", message).format(user)
        )

    @loader.owner
    async def setprefixcmd(self, message: Message) -> None:
        """Sets command prefix"""
        args = utils.get_args_raw(message)

        if not args:
            await utils.answer(message, self.strings("what_prefix", message))
            return

        if len(args) != 1:
            await utils.answer(message, self.strings("prefix_incorrect", message))
            return

        oldprefix = self._db.get(main.__name__, "command_prefix", ".")
        self._db.set(main.__name__, "command_prefix", args)
        await utils.answer(
            message,
            self.strings("prefix_set", message).format(
                newprefix=utils.escape_html(args[0]),
                oldprefix=utils.escape_html(oldprefix),
            ),
        )

    @loader.owner
    async def aliasescmd(self, message: Message) -> None:
        """Print all your aliases"""
        aliases = self.allmodules.aliases
        string = self.strings("aliases", message)

        string += "\n".join([f"\n{i}: {y}" for i, y in aliases.items()])

        await utils.answer(message, string)

    @loader.owner
    async def addaliascmd(self, message: Message) -> None:
        """Set an alias for a command"""
        args = utils.get_args(message)

        if len(args) != 2:
            await utils.answer(message, self.strings("alias_args", message))
            return

        alias, cmd = args
        ret = self.allmodules.add_alias(alias, cmd)

        if ret:
            self._db.set(
                __name__, "aliases", {**self._db.get(__name__, "aliases"), alias: cmd}
            )
            await utils.answer(
                message,
                self.strings("alias_created", message).format(utils.escape_html(alias)),
            )
        else:
            await utils.answer(
                message,
                self.strings("no_command", message).format(utils.escape_html(cmd)),
            )

    @loader.owner
    async def delaliascmd(self, message: Message) -> None:
        """Remove an alias for a command"""
        args = utils.get_args(message)

        if len(args) != 1:
            await utils.answer(message, self.strings("delalias_args", message))
            return

        alias = args[0]
        ret = self.allmodules.remove_alias(alias)

        if ret:
            current = self._db.get(__name__, "aliases")
            del current[alias]
            self._db.set(__name__, "aliases", current)
            await utils.answer(
                message,
                self.strings("alias_removed", message).format(utils.escape_html(alias)),
            )
        else:
            await utils.answer(
                message,
                self.strings("no_alias", message).format(utils.escape_html(alias)),
            )

    async def addtrnslcmd(self, message: Message) -> None:
        """Add a translation pack
        .addtrnsl <pack>
        Restart required after use"""
        args = utils.get_args(message)

        if len(args) != 1:
            await utils.answer(message, self.strings("no_pack", message))
            return

        pack = args[0]
        if str(pack).isdigit():
            pack = int(pack)

        try:
            pack = await self._client.get_entity(pack)
        except ValueError:
            await utils.answer(message, self.strings("bad_pack", message))
            return

        if isinstance(pack, Channel) and not pack.megagroup:
            self._db.setdefault(main.__name__, {}).setdefault("langpacks", []).append(
                pack.id
            )
            self._db.save()
            await utils.answer(message, self.strings("trnsl_saved", message))
        else:
            await utils.answer(message, self.strings("bad_pack", message))

    async def cleartrnslcmd(self, message: Message) -> None:
        """Remove all translation packs"""
        self._db.set(main.__name__, "langpacks", [])
        await utils.answer(message, self.strings("packs_cleared", message))

    async def setlangcmd(self, message: Message) -> None:
        """Change the preferred language used for translations
        Restart required after use"""
        langs = utils.get_args(message)
        self._db.set(main.__name__, "language", langs)
        await utils.answer(message, self.strings("lang_set", message))

    @loader.owner
    async def cleardbcmd(self, message: Message) -> None:
        """Clears the entire database, effectively performing a factory reset"""
        self._db.clear()
        self._db.save()
        await utils.answer(message, self.strings("db_cleared", message))

    async def _client_ready2(self, client, db):  # skicpq: PYL-W0613
        ret = {
            alias: cmd
            for alias, cmd in db.get(__name__, "aliases", {}).items()
            if self.allmodules.add_alias(alias, cmd)
        }

        db.set(__name__, "aliases", ret)
