from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("reconfillion")
except PackageNotFoundError:  # running from source without an installed package
    __version__ = "unknown"
