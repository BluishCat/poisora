"""UI の多言語対応。

文言は locales/<言語コード>.json に「キー: 文言」で置き、コードからは tr("キー") で引く。
文言中の {name} は tr("キー", name=値) で埋める（str.format）。
（t はループ変数などに使われがちで、関数内で t = ... があると呼べなくなるため tr を使う）

言語の決め方:
  - ui_config.json の "language" が "auto"（既定）または未設定なら OS の表示言語に合わせる
  - OS の言語の訳が無ければ英語にする
  - 起動時に一度決めたら変えない（設定画面での変更は再起動後に反映）

訳の探し方は「選んだ言語 → 英語 → 日本語 → キーそのもの」の順。
exe と同じフォルダーの locales/ に xx.json を置くと、言語の追加や同梱の訳の上書きができる。
"""
import json
import locale
import os
import sys

from .paths import get_app_dir

AUTO = "auto"
FALLBACK = "en"
_LAST_RESORT = "ja"  # 元の文言は日本語で書かれているため、最後の頼りにする

_catalogs = None   # {言語コード: {キー: 文言}}
_current = None    # 決定済みの言語コード


def _locale_dirs():
    """同梱の locales → exe の隣の locales の順（後のものが上書きする）"""
    dirs = []
    base = getattr(sys, "_MEIPASS", None)
    if base:
        dirs.append(os.path.join(base, "locales"))
    dirs.append(os.path.join(get_app_dir(), "locales"))
    seen, result = set(), []
    for d in dirs:
        key = os.path.normcase(os.path.abspath(d))
        if key not in seen:
            seen.add(key)
            result.append(d)
    return result


def _load_catalogs():
    catalogs = {}
    for d in _locale_dirs():
        try:
            names = sorted(os.listdir(d))
        except OSError:
            continue
        for name in names:
            code, ext = os.path.splitext(name)
            if ext.lower() != ".json":
                continue
            try:
                with open(os.path.join(d, name), "r", encoding="utf-8") as f:
                    data = json.load(f)
            except (OSError, ValueError) as e:
                print(f"[i18n] {name} を読み込めませんでした: {e}")
                continue
            if isinstance(data, dict):
                catalogs.setdefault(code.lower(), {}).update(
                    {k: v for k, v in data.items() if isinstance(v, (str, dict))})
    return catalogs


def _get_catalogs():
    global _catalogs
    if _catalogs is None:
        _catalogs = _load_catalogs()
    return _catalogs


def _normalize(tag):
    """'ja_JP' / 'ja-JP.UTF-8' / 'Japanese_Japan' などを 'ja' にする"""
    if not tag:
        return None
    tag = str(tag).split(".")[0].replace("-", "_")
    lower = tag.lower()
    if lower.startswith("japanese"):
        return "ja"
    if lower.startswith("english"):
        return "en"
    code = lower.split("_")[0]
    return code if 2 <= len(code) <= 3 and code.isalpha() else None


def system_language():
    """OS の表示言語の言語コード（例: 'ja', 'en'）。分からなければ None"""
    if sys.platform == "win32":
        try:
            import ctypes
            langid = ctypes.windll.kernel32.GetUserDefaultUILanguage()
            code = _normalize(locale.windows_locale.get(langid))
            if code:
                return code
        except Exception:
            pass
    for var in ("LC_ALL", "LC_MESSAGES", "LANG", "LANGUAGE"):
        code = _normalize(os.environ.get(var, "").split(":")[0])
        if code and code != "c":
            return code
    try:
        return _normalize(locale.getlocale()[0])
    except Exception:
        return None


def available_languages():
    """{言語コード: 表示名}。表示名は各ファイルの "_meta.name"（無ければコード）"""
    result = {}
    for code, catalog in sorted(_get_catalogs().items()):
        meta = catalog.get("_meta")
        name = meta.get("name") if isinstance(meta, dict) else None
        result[code] = name or code
    return result


def resolve(setting):
    """設定値（'auto' / 言語コード）から実際に使う言語コードを決める"""
    catalogs = _get_catalogs()
    if setting and setting != AUTO and setting in catalogs:
        return setting
    code = system_language()
    if code in catalogs:
        return code
    return FALLBACK


def _saved_setting():
    try:
        from .ui_config import load_ui_state
        return (load_ui_state() or {}).get("language", AUTO)
    except Exception:
        return AUTO


def init(setting=None):
    """使う言語を決める。setting を省略すると ui_config.json の設定を読む"""
    global _current
    _current = resolve(_saved_setting() if setting is None else setting)
    return _current


def current_language():
    if _current is None:
        init()
    return _current


def _lookup(code, key):
    value = _get_catalogs().get(code, {}).get(key)
    return value if isinstance(value, str) else None


def t(key, **kwargs):
    """キーに対応する今の言語の文言。見つからなければ英語 → 日本語 → キーの順"""
    tried = []
    for code in (current_language(), FALLBACK, _LAST_RESORT):
        if code in tried:
            continue
        tried.append(code)
        text = _lookup(code, key)
        if text is None:
            continue
        if not kwargs:
            return text
        try:
            return text.format(**kwargs)
        except (KeyError, IndexError, ValueError):
            # 追加された訳の書式ミスで落ちないよう、次の言語の文言で試す
            continue
    return key


tr = t
