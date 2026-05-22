import os
import sys


APP_ICON_ICO = "app_icon.ico"
APP_ICON_PNG = "app_icon.png"
APP_USER_MODEL_ID = "gmail_transaction_alert.email_extractor.multi_tab"

COLORS = {
    "bg": "#f6f8fb",
    "surface": "#ffffff",
    "surface_alt": "#eef4ff",
    "border": "#d8e0ea",
    "text": "#172033",
    "muted": "#667085",
    "primary": "#2563eb",
    "primary_hover": "#1d4ed8",
    "primary_pressed": "#1e40af",
    "success": "#0f766e",
    "danger": "#dc2626",
    "danger_hover": "#b91c1c",
    "row_alt": "#f9fbff",
    "selected": "#dbeafe",
    "header": "#0f766e",
    "header_dark": "#115e59",
}


def app_path(file_name):
    base_dir = getattr(sys, "_MEIPASS", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return os.path.join(base_dir, file_name)


def external_app_path(file_name):
    if getattr(sys, "frozen", False):
        base_dir = os.path.dirname(sys.executable)
    else:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    return os.path.join(base_dir, file_name)


def configure_windows_taskbar_icon():
    if sys.platform != "win32":
        return

    try:
        import ctypes

        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_USER_MODEL_ID)
    except Exception:
        # Taskbar metadata is best-effort; Tk can still run without it.
        pass
