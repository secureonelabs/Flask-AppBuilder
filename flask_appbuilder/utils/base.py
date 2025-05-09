from fnmatch import fnmatch
import logging
from typing import Any, Callable
import unicodedata
from urllib.parse import urlparse

from flask import current_app, request
from flask_babel import gettext
from flask_babel.speaklater import LazyString


log = logging.getLogger(__name__)


def is_safe_redirect_url(url: str) -> bool:
    if url.startswith("///"):
        return False
    try:
        url_info = urlparse(url)
    except ValueError:
        return False
    if not url_info.netloc and url_info.scheme:
        return False
    if unicodedata.category(url[0])[0] == "C":
        return False
    scheme = url_info.scheme
    # Consider URLs without a scheme (e.g. //example.com/p) to be http.
    if not url_info.scheme and url_info.netloc:
        scheme = "http"
    valid_schemes = ["http", "https"]

    safe_hosts = current_app.config.get("FAB_SAFE_REDIRECT_HOSTS", [])
    if not safe_hosts:
        safe_hosts = [urlparse(request.host_url).netloc]

    is_host_allowed = not url_info.netloc or any(
        fnmatch(url_info.netloc, pattern) for pattern in safe_hosts
    )

    return is_host_allowed and (not scheme or scheme in valid_schemes)


def get_safe_redirect(url):
    if url and is_safe_redirect_url(url):
        return url
    log.warning("Invalid redirect detected, falling back to index")
    return current_app.appbuilder.get_url_for_index


def get_column_root_relation(column: str) -> str:
    if "." in column:
        return column.split(".")[0]
    return column


def get_column_leaf(column: str) -> str:
    if "." in column:
        return column.split(".")[1]
    return column


def is_column_dotted(column: str) -> bool:
    return "." in column


def _wrap_lazy_formatter_gettext(
    string: str, lazy_formater: Callable[[str], str], **variables: Any
) -> str:
    return gettext(lazy_formater(string), **variables)


def lazy_formatter_gettext(
    string: str, lazy_formatter: Callable[[str], str], **variables: Any
) -> LazyString:
    """Formats a lazy_gettext string with a custom function

    Example::

        def custom_formatter(string: str) -> str:
            if current_app.config["CONDITIONAL_KEY"]:
                string += " . Condition key is on"
            return string

        hello = lazy_formatter_gettext(u'Hello World', custom_formatter)

        @app.route('/')
        def index():
            return unicode(hello)
    """
    return LazyString(_wrap_lazy_formatter_gettext, string, lazy_formatter, **variables)
