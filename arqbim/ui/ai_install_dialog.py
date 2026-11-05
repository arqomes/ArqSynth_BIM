"""Manage ▸ Ligar um assistente de IA… (0.270): the MCP server put in the AI's programs — Claude Desktop with a
click (its config file merged, a copy kept), the line for Claude Code, the JSON for any other — and how to spend few
tokens."""

from PySide6 import QtGui, QtWidgets

from ..i18n import t
from ..mcp import install
from . import theme


class AiInstallDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(t("aiinst.title"))
        layout = QtWidgets.QVBoxLayout(self)
        intro = QtWidgets.QLabel(t("aiinst.intro"))
        intro.setWordWrap(True)
        layout.addWidget(intro)

        desktop = QtWidgets.QGroupBox("Claude Desktop")
        lay = QtWidgets.QVBoxLayout(desktop)
        self.desktop_path = QtWidgets.QLabel(t("aiinst.desktop_path", path=install.desktop_config_path()))
        self.desktop_path.setWordWrap(True)
        self.desktop_button = QtWidgets.QPushButton(t("aiinst.desktop_button"))
        self.desktop_button.clicked.connect(self.install_desktop)
        lay.addWidget(self.desktop_path)
        lay.addWidget(self.desktop_button)
        layout.addWidget(desktop)

        code = QtWidgets.QGroupBox("Claude Code")
        lay = QtWidgets.QVBoxLayout(code)
        self.code_line = QtWidgets.QLineEdit(install.claude_code_line())
        self.code_line.setReadOnly(True)
        copy = QtWidgets.QPushButton(t("aiinst.copy"))
        copy.clicked.connect(lambda: self._copy(self.code_line.text()))
        lay.addWidget(QtWidgets.QLabel(t("aiinst.code_hint")))
        lay.addWidget(self.code_line)
        lay.addWidget(copy)
        layout.addWidget(code)

        other = QtWidgets.QGroupBox(t("aiinst.other"))
        lay = QtWidgets.QVBoxLayout(other)
        self.json = QtWidgets.QPlainTextEdit(install.config_text())
        self.json.setReadOnly(True)
        self.json.setFont(QtGui.QFontDatabase.systemFont(QtGui.QFontDatabase.SystemFont.FixedFont))
        self.json.setMinimumHeight(140)
        copy_json = QtWidgets.QPushButton(t("aiinst.copy"))
        copy_json.clicked.connect(lambda: self._copy(self.json.toPlainText()))
        lay.addWidget(self.json)
        lay.addWidget(copy_json)
        layout.addWidget(other)

        tokens = QtWidgets.QLabel(t("aiinst.tokens"))
        tokens.setWordWrap(True)
        tokens.setStyleSheet("color: %s;" % theme.C["note"])
        layout.addWidget(tokens)
        self.status = QtWidgets.QLabel("")
        self.status.setWordWrap(True)
        layout.addWidget(self.status)
        close = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Close)
        close.rejected.connect(self.reject)
        layout.addWidget(close)
        self.resize(720, 640)

    def _copy(self, text):
        QtWidgets.QApplication.clipboard().setText(text)
        self.status.setText(t("aiinst.copied"))

    def install_desktop(self, path=None):
        """Claude Desktop's config file with this program's server in it (the others kept, a copy left)."""
        try:
            done = install.merge_into(path or install.desktop_config_path())
        except (OSError, ValueError) as exc:
            self.status.setText(t("aiinst.failed", e=exc))
            return False
        self.status.setText(t("aiinst.desktop_done", path=done))
        return True
