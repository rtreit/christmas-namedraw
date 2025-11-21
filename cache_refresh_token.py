"""Backwards-compatible shim to the modern token bootstrap script."""

from scripts.cache_refresh_token import main


if __name__ == "__main__":
    main()
