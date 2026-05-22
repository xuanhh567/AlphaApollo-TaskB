__all__ = ["rl", "sft", "test", "evo"]


def __getattr__(name):
    if name in __all__:
        from .workflows import api

        return getattr(api, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
