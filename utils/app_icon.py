"""アプリのウィンドウアイコン"""
import base64
import os

from utils.paths import get_resource_path

ICON_PNG = os.path.join("assets", "poisora.png")


def apply_default_window_icon():
    """TkEasyGUI が作る全ウィンドウ（popup 含む）の既定アイコンを Poisora のものにする。

    TkEasyGUI は eg.Window 生成時に icon 引数が無ければ widgets.DEFAULT_WINDOW_ICON
    （base64 の PNG）を iconphoto に設定するので、それを差し替える。
    読み込めない場合は TkEasyGUI の既定アイコンのまま動かす。
    """
    try:
        with open(get_resource_path(ICON_PNG), "rb") as f:
            data = base64.b64encode(f.read())
        import TkEasyGUI.widgets as eg_widgets
        eg_widgets.DEFAULT_WINDOW_ICON = data
        return True
    except Exception:
        return False
