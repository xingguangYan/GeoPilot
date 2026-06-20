"""GeoPilot Chat Dialog - Natural-Language Geospatial Interface"""
import os, sys, json, traceback, html

from qgis.PyQt.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton,
    QComboBox, QLabel, QLineEdit, QSplitter, QMessageBox,
    QGroupBox, QFormLayout, QCheckBox, QProgressBar, QTabWidget,
    QWidget, QScrollArea, QFrame, QDialogButtonBox
)
from qgis.PyQt.QtGui import QTextCursor, QFont, QIcon, QPixmap
from qgis.PyQt.QtCore import Qt, QThread, pyqtSignal, QSettings, QUrl
from qgis.core import QgsProject, QgsLayerTreeLayer, QgsMessageLog

PLUGIN_DIR = os.path.dirname(os.path.abspath(__file__))
SCRIPTS_DIR = os.path.join(PLUGIN_DIR, "scripts")


class ApiWorker(QThread):
    """Run API requests in background thread."""
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, provider, messages, system=None):
        super().__init__()
        self.provider = provider
        self.messages = messages
        self.system = system

    def run(self):
        try:
            result = self.provider.chat(self.messages, self.system)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(f"Error: {str(e)}")


class GeoPilotDialog(QDialog):
    """Main chat dialog for GeoPilot."""

    def __init__(self, iface, plugin_dir):
        super().__init__(iface.mainWindow())
        self.iface = iface
        self.plugin_dir = plugin_dir
        self.settings = QSettings()
        self.conversation = []
        self.current_provider = None
        self.worker = None
        self.setup_ui()
        self.load_settings()

    def setup_ui(self):
        """Build the dialog UI."""
        self.setWindowTitle("GeoPilot - AI Geospatial Assistant")
        self.resize(900, 700)
        self.setMinimumSize(600, 400)

        layout = QVBoxLayout()

        # === Provider Selection ====
        top_layout = QHBoxLayout()
        top_layout.addWidget(QLabel("Model Provider:"))

        self.provider_combo = QComboBox()
        self.update_provider_list()
        self.provider_combo.setMinimumWidth(180)
        self.provider_combo.currentTextChanged.connect(self.on_provider_changed)
        top_layout.addWidget(self.provider_combo)

        top_layout.addWidget(QLabel("Model:"))
        self.model_combo = QComboBox()
        self.model_combo.setEditable(True)
        top_layout.addWidget(self.model_combo)
        top_layout.addStretch()
        layout.addLayout(top_layout)

        # API settings line
        api_layout = QHBoxLayout()
        api_layout.addWidget(QLabel("API Key:"))
        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.Password)
        api_layout.addWidget(self.api_key_input)

        api_layout.addWidget(QLabel("Base URL:"))
        self.base_url_input = QLineEdit()
        self.base_url_input.setPlaceholderText("Optional: custom endpoint URL")
        api_layout.addWidget(self.base_url_input)
        layout.addLayout(api_layout)

        # === Chat Area ====
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setStyleSheet("QTextEdit { background-color: #1e1e2e; color: #cdd6f4; font-family: Consolas; font-size: 11pt; }")
        layout.addWidget(self.chat_display, stretch=1)

        # === Input Area ====
        input_layout = QHBoxLayout()
        self.input_field = QTextEdit()
        self.input_field.setPlaceholderText("Describe your geospatial task in natural language...")
        self.input_field.setMaximumHeight(80)
        self.input_field.setStyleSheet("QTextEdit { font-size: 11pt; }")
        input_layout.addWidget(self.input_field, stretch=1)

        self.send_btn = QPushButton("Send")
        self.send_btn.setStyleSheet("QPushButton { background-color: #89b4fa; color: #1e1e2e; font-weight: bold; padding: 8px 16px; border-radius: 4px; } QPushButton:hover { background-color: #74c7ec; }")
        self.send_btn.clicked.connect(self.on_send)
        input_layout.addWidget(self.send_btn)

        self.clear_btn = QPushButton("Clear")
        self.clear_btn.clicked.connect(self.clear_chat)
        input_layout.addWidget(self.clear_btn)
        layout.addLayout(input_layout)

        # === Progress ====
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        layout.addWidget(self.progress)

        self.setLayout(layout)

        # Keyboard shortcut: Enter to send
        self.input_field.installEventFilter(self)

    def on_provider_changed(self, provider):
        """Update model list when provider changes."""
        self.model_combo.clear()
        try:
            from providers import list_providers
            registry = list_providers()
            entry = registry.get(provider, {})
            models = entry.get("models", ["default"])
            self.model_combo.addItems(models)
            self.model_combo.setCurrentIndex(0)
            # Update API key placeholder
            env_key = entry.get("env_key", "API_KEY") or "API_KEY"
            self.api_key_input.setPlaceholderText(f"Enter {env_key} (or set {env_key} env var)")
            # Update base URL placeholder
            default_url = entry.get("default_url", "")
            if default_url:
                self.base_url_input.setPlaceholderText(f"Default: {default_url}")
                self.base_url_input.setText("")
        except Exception:
            self.model_combo.addItems(["default"])

    def load_settings(self):
        """Load saved settings."""
        provider = self.settings.value("geopilot/provider", "openai")
        for i in range(self.provider_combo.count()):
            if self.provider_combo.itemData(i) == provider:
                self.provider_combo.setCurrentIndex(i)
                break

        api_key = self.settings.value("geopilot/api_key", "")
        if api_key: self.api_key_input.setText(api_key)

        base_url = self.settings.value("geopilot/base_url", "")
        if base_url: self.base_url_input.setText(base_url)

    def save_settings(self):
        """Save current settings."""
        self.settings.setValue("geopilot/provider", self.provider_combo.currentData() or self.provider_combo.currentText())
        self.settings.setValue("geopilot/api_key", self.api_key_input.text())
        self.settings.setValue("geopilot/base_url", self.base_url_input.text())

    def update_provider_list(self):
        """Populate provider list from registry."""
        try:
            from providers import list_providers
            registry = list_providers()
            for name, info in registry.items():
                display = info.get("display_name", name)
                self.provider_combo.addItem(f"{display} ({name})", name)
        except Exception:
            self.provider_combo.addItems(["openai", "anthropic", "ollama", "google", "deepseek"])

    def get_provider(self):
        """Get current API provider instance."""
        from providers import get_provider
        name = self.provider_combo.currentData()
        if not name:
            name = self.provider_combo.currentText().split("(")[-1].rstrip(")") if "(" in self.provider_combo.currentText() else self.provider_combo.currentText()
        model = self.model_combo.currentText()
        api_key = self.api_key_input.text().strip()
        base_url = self.base_url_input.text().strip() or None
        return get_provider(name, api_key=api_key, model=model, base_url=base_url)

    def add_message(self, role, content):
        """Add a message to the chat display."""
        self.conversation.append({"role": role, "content": content})

        esc = html.escape
        if role == "user":
            prefix = "<b style=\"color:#89b4fa\">You:</b><br>"
        else:
            prefix = "<b style=\"color:#a6e3a1\">GeoPilot:</b><br>"

        code_content = content.replace("\n", "<br>")
        self.chat_display.append(prefix + code_content + "<br><br>")
        self.chat_display.moveCursor(QTextCursor.End)

    def on_send(self):
        """Handle send button click."""
        text = self.input_field.toPlainText().strip()
        if not text:
            return

        self.save_settings()
        self.input_field.clear()
        self.add_message("user", text)

        # Get current layers as context
        layers = QgsProject.instance().layerTreeRoot().findLayers()
        context = f"Current layers ({len(layers)}):\n"
        for l in layers[:10]:
            layer = l.layer()
            context += f"  - {layer.name()} ({layer.type().__class__.__name__})\n"

        try:
            provider = self.get_provider()
        except Exception as e:
            self.add_message("assistant", f"Provider error: {str(e)}")
            return

        # Build messages
        messages = []
        if context:
            messages.append({"role": "system", "content": context})
        messages.extend(self.conversation[-20:])

        self.progress.setVisible(True)
        self.send_btn.setEnabled(False)

        self.worker = ApiWorker(provider, messages)
        self.worker.finished.connect(self.on_response)
        self.worker.error.connect(self.on_error)
        self.worker.start()

    def on_response(self, response):
        """Handle API response."""
        self.progress.setVisible(False)
        self.send_btn.setEnabled(True)
        self.add_message("assistant", response)

        # Execute any code blocks if user enabled auto-run
        self.execute_code_blocks(response)

    def on_error(self, error):
        """Handle API error."""
        self.progress.setVisible(False)
        self.send_btn.setEnabled(True)
        self.add_message("assistant", f"Error: {error}")

    def execute_code_blocks(self, response):
        """Parse and optionally execute Python code blocks."""
        import re
        blocks = re.findall(r"```python\n(.*?)\n```", response, re.DOTALL)
        for i, code in enumerate(blocks):
            try:
                exec(code, globals())
                self.chat_display.append(f"<i>Executed block {i+1}</i><br>")
            except Exception as e:
                self.chat_display.append(f"<i>Block {i+1} error: {e}</i><br>")

    def clear_chat(self):
        """Clear the chat history."""
        self.chat_display.clear()
        self.conversation = []

    def eventFilter(self, obj, event):
        if obj == self.input_field and event.type() == event.KeyPress:
            from qgis.PyQt.QtCore import QEvent
            if event.key() == Qt.Key_Return and not event.modifiers():
                self.on_send()
                return True
        return super().eventFilter(obj, event)
