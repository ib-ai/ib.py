from functools import wraps

from discord.ext import commands


def _get_command_wrapper_factory(_original_get_command, _cog):
    def get_command_wrapper(name):
        subcommand = _original_get_command(name)
        if subcommand is None:
            return None

        callback = subcommand.callback

        @wraps(callback)
        async def wrapper(*args, **kwargs):
            return await callback(_cog, *args, **kwargs)

        return wrapper

    return get_command_wrapper


def patch_cog_commands(cog):
    """
    Patch cog commands such that they work with direct calls (without .callback or passing self).
    """
    for attr_name in dir(cog):
        attr = getattr(cog, attr_name)
        if isinstance(attr, commands.Group):
            _get_command = attr.get_command
            attr.get_command = _get_command_wrapper_factory(_get_command, cog)
        elif isinstance(attr, commands.Command):
            callback = attr.callback

            @wraps(callback)
            async def wrapper(*args, _func=callback, _cog=cog, **kwargs):
                return await _func(_cog, *args, **kwargs)

            setattr(cog, attr_name, wrapper)
    return cog
