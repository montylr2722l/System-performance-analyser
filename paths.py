"""Application paths."""

import os


def get_app_dir():
    """Directory where settings, reports, and logs are stored."""
    return os.path.dirname(os.path.abspath(__file__))


def get_data_path(filename):
    """Return a writable path next to the app."""
    return os.path.join(get_app_dir(), filename)
