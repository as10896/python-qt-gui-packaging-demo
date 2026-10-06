"""UUID Renamer GUI: drop files or folders onto the window to rename them."""

import subprocess
import sys
from functools import cache
from pathlib import Path

from desktop_notifier import DesktopNotifierSync, Icon
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QApplication,
    QFileIconProvider,
    QFrame,
    QLabel,
    QListWidget,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from renamer import expand, rename_to_uuid

APP_NAME = "UUID Renamer"
# Works both from source and inside a PyInstaller bundle, as long as
# assets/ is bundled with `--add-data`
ICON_PATH = Path(__file__).parent / "assets" / "icon.png"


@cache
def native_notifier() -> DesktopNotifierSync | None:
    """Return a native notifier, or None if this platform/build can't use one."""
    is_mac = sys.platform == "darwin"
    # On macOS, Notification Center only works inside an .app bundle
    if is_mac and not getattr(sys, "frozen", False):
        return None
    notifier = DesktopNotifierSync(app_name=APP_NAME, app_icon=Icon(path=ICON_PATH))
    # ...and only if that bundle is signed with an Apple Developer ID.
    # Unsigned (ad-hoc) builds get refused here.
    if is_mac and not notifier.request_authorisation():
        return None
    return notifier


def notify(title: str, message: str):
    if notifier := native_notifier():
        notifier.send(title=title, message=message)
    else:
        # macOS fallback that always works, but shows Script Editor's icon
        subprocess.Popen(
            [
                "osascript",
                "-e", "on run argv",
                "-e", "display notification (item 2 of argv) with title (item 1 of argv)",
                "-e", "end run",
                title,
                message,
            ]
        )


def file_icon(size: int) -> QLabel:
    label = QLabel()
    label.setPixmap(QFileIconProvider().icon(QFileIconProvider.File).pixmap(size, size))
    label.setAlignment(Qt.AlignCenter)
    return label


def centered_label(text: str, style: str) -> QLabel:
    label = QLabel(text)
    label.setAlignment(Qt.AlignCenter)
    label.setStyleSheet(style)
    return label


class IdlePage(QWidget):
    """Default view: a dashed drop zone, plus a log that appears after the first rename."""

    def __init__(self):
        super().__init__()
        zone = QFrame()
        zone.setObjectName("zone")
        zone.setStyleSheet(
            "#zone { border: 2px dashed rgba(128, 128, 128, 0.7); border-radius: 14px; }"
        )
        zone_layout = QVBoxLayout(zone)
        zone_layout.addStretch()
        zone_layout.addWidget(file_icon(64))
        zone_layout.addSpacing(8)
        zone_layout.addWidget(
            centered_label("Drop files or folders here", "font-size: 15px; font-weight: bold;")
        )
        zone_layout.addWidget(
            centered_label("They'll be renamed to UUIDs", "color: palette(placeholder-text);")
        )
        zone_layout.addStretch()

        self.log = QListWidget()
        self.log.setTextElideMode(Qt.ElideMiddle)
        self.log.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.log.setFixedHeight(110)
        self.log.hide()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.addWidget(zone, stretch=1)
        layout.addWidget(self.log)

    def add_log(self, line: str):
        self.log.show()
        self.log.addItem(line)
        self.log.scrollToBottom()


class DropPage(QWidget):
    """Shown while something is being dragged over the window."""

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.addStretch()
        layout.addWidget(file_icon(128))
        layout.addSpacing(12)
        layout.addWidget(
            centered_label("Release to rename", "font-size: 18px; font-weight: bold;")
        )
        layout.addStretch()
        layout.addWidget(
            centered_label(
                "File extensions are kept as-is", "color: palette(placeholder-text);"
            )
        )


class MainWindow(QStackedWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.setAcceptDrops(True)
        self.setFixedSize(340, 380)

        self.idle = IdlePage()
        self.addWidget(self.idle)
        self.addWidget(DropPage())

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.setCurrentIndex(1)

    def dragLeaveEvent(self, event):
        self.setCurrentIndex(0)

    def dropEvent(self, event):
        self.setCurrentIndex(0)
        paths = [url.toLocalFile() for url in event.mimeData().urls()]

        renamed, failed = [], 0
        # Materialize the list first so we don't rename while iterating a folder
        for f in list(expand(paths)):
            try:
                new_path = rename_to_uuid(f)
                renamed.append((f.name, new_path.name))
                self.idle.add_log(f"{f.name}  →  {new_path.name}")
            except OSError as e:
                failed += 1
                self.idle.add_log(f"{f.name}  ✗  {e}")

        if len(renamed) == 1 and not failed:
            old, new = renamed[0]
            notify("Rename complete", f"“{old}” is now “{new}”")
        elif renamed or failed:
            message = f"Renamed {len(renamed)} file(s)"
            if failed:
                message += f", {failed} failed"
            notify("Rename complete", message)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(str(ICON_PATH)))
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
