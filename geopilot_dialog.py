"""GeoPilot Chat Dialog - Natural-Language Geospatial Interface."""

import html
import os
import re
import traceback

from qgis.PyQt.QtCore import QEvent, QSettings, Qt, QThread, pyqtSignal
from qgis.PyQt.QtGui import QIcon, QTextCursor
from qgis.PyQt.QtWidgets import (
    QComboBox,
    QDialog,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QTextEdit,
    QToolButton,
    QVBoxLayout,
)

from qgis.core import QgsApplication, QgsMessageLog, QgsProject

PLUGIN_DIR = os.path.dirname(os.path.abspath(__file__))
SCRIPTS_DIR = os.path.join(PLUGIN_DIR, "scripts")

# Regex for extracting Python code blocks from an LLM response.
_CODE_BLOCK_RE = re.compile(r"```(?:python|py)?\s*\n(.*?)```", re.DOTALL | re.IGNORECASE)
_CODE_INLINE_RE = re.compile(r"`([^`]+)`")


class ApiWorker(QThread):
    """Run API requests in a background thread so the UI stays responsive."""

    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, provider, messages, system=None):
        super().__init__()
        self.provider = provider
        self.messages = messages
        self.system = system
        self._aborted = False

    def abort(self):
        self._aborted = True

    def run(self):
        try:
            result = self.provider.chat(self.messages, self.system)
            if self._aborted:
                return
            self.finished.emit(result)
        except Exception as e:  # pragma: no cover - defensive
            if not self._aborted:
                self.error.emit(f"Error: {e}")


class GeoPilotDialog(QDialog):
    """Main chat dialog for GeoPilot."""

    PROMPT_EXAMPLES = [
        (
            "\U0001f5fa 研究区分析",
            "Create Figure 1: Study area map showing the location with satellite imagery, administrative boundaries, scale bar, north arrow, and legend.",
        ),
        (
            "\U0001f33f 植被分析",
            "Calculate NDVI from the current multispectral raster and create a time series chart.",
        ),
        (
            "\U0001f3d4 土地利用",
            "Run land cover classification on the current image using Random Forest with 100 trees and 5 classes.",
        ),
        (
            "\U0001f4ca 变化检测",
            "Perform change detection between 2020 and 2025 imagery and create a change map figure.",
        ),
        (
            "\U0001f30d 空间格局",
            "Calculate and visualize the spatial pattern (Moran's I, LISA) for the current vector layer.",
        ),
        (
            "\U0001f4c4 导出报告",
            "Generate a complete research report with all methods, results, and SCI-style figures.",
        ),
    ]

    SYSTEM_PROMPT_DEFAULT = (
        "You are GeoPilot, an AI assistant that controls QGIS through Python code.\n\n"
        "CRITICAL: Respond with executable QGIS Python code inside a ```python ... ``` fenced block. "
        "The code will be shown to the user for confirmation before execution. Keep code concise and "
        "safe — never call os.system, subprocess, shutil.rmtree, open(..., 'w'), or delete user data "
        "without explicit request.\n\n"
        "Key APIs:\n"
        "- QgsProject.instance().mapLayers() -> dict of loaded layers\n"
        "- QgsProject.instance().addMapLayer(layer)\n"
        "- processing.run('native:buffer', {...}) for Processing algorithms\n"
        "- iface.messageBar().pushMessage(...) for user-facing messages\n\n"
        "After the code block, briefly explain in the user's language what the code does and any "
        "inputs/outputs the user should know about."
    )

    def __init__(self, iface, plugin_dir):
        super().__init__(iface.mainWindow())
        self.iface = iface
        self.plugin_dir = plugin_dir
        self.settings = QSettings()
        self.conversation = []
        self.worker = None
        self.help_visible = False
        self._pending_code_blocks = []
        self._code_confirm_required = True

        self.setup_ui()
        self.load_settings()
        self.show_welcome()

    # ------------------------------------------------------------------ UI --

    def setup_ui(self):
        """Build the dialog UI."""
        self.setWindowTitle("GeoPilot - AI Geospatial Assistant")
        self.resize(960, 760)
        self.setMinimumSize(700, 500)

        self.setStyleSheet(
            """
            QDialog { background-color: #1e1e2e; }
            QLabel { color: #cdd6f4; font-size: 10pt; }
            QGroupBox { color: #89b4fa; font-weight: bold; border: 1px solid #313244; border-radius: 6px; margin-top: 10px; padding-top: 16px; }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; }
            QComboBox { background-color: #313244; color: #cdd6f4; border: 1px solid #45475a; border-radius: 4px; padding: 4px 8px; }
            QComboBox:hover { border-color: #89b4fa; }
            QComboBox QAbstractItemView { background-color: #313244; color: #cdd6f4; selection-background-color: #45475a; }
            QLineEdit { background-color: #313244; color: #cdd6f4; border: 1px solid #45475a; border-radius: 4px; padding: 4px 8px; }
            QLineEdit:hover { border-color: #89b4fa; }
            QPushButton { background-color: #313244; color: #cdd6f4; border: 1px solid #45475a; border-radius: 4px; padding: 6px 14px; }
            QPushButton:hover { background-color: #45475a; border-color: #89b4fa; }
            QProgressBar { background-color: #313244; border: none; border-radius: 4px; height: 6px; text-align: center; }
            QProgressBar::chunk { background-color: #89b4fa; border-radius: 4px; }
            QTextEdit { background-color: #1e1e2e; color: #cdd6f4; border: 1px solid #313244; border-radius: 4px; font-family: Consolas, 'Courier New', monospace; font-size: 11pt; }
            QScrollBar:vertical { background-color: #1e1e2e; width: 8px; }
            QScrollBar::handle:vertical { background-color: #45475a; border-radius: 4px; min-height: 20px; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
            QCheckBox { color: #cdd6f4; }
            """
        )

        main_layout = QVBoxLayout()
        main_layout.setSpacing(6)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # HEADER
        header = QHBoxLayout()
        title_label = QLabel(
            "<b style='color:#89b4fa;font-size:14pt;'>GeoPilot</b>  "
            "<span style='color:#6c7086;font-size:9pt;'>AI Geospatial Assistant</span>"
        )
        header.addWidget(title_label)
        header.addStretch()

        self.help_btn = QToolButton()
        self.help_btn.setText("\u2753 Help")
        self.help_btn.setCheckable(True)
        self.help_btn.setChecked(False)
        self.help_btn.toggled.connect(self.toggle_help)
        self.help_btn.setStyleSheet(
            "QToolButton { background-color: #313244; color: #a6e3a1; border: 1px solid #45475a;"
            " border-radius: 4px; padding: 4px 12px; }"
            " QToolButton:hover { border-color: #a6e3a1; }"
            " QToolButton:checked { background-color: #45475a; }"
        )
        header.addWidget(self.help_btn)
        main_layout.addLayout(header)

        # HELP PANEL
        self.help_panel = QFrame()
        self.help_panel.setStyleSheet(
            "QFrame { background-color: #181825; border: 1px solid #313244; border-radius: 6px; padding: 8px; }"
        )
        help_layout = QVBoxLayout(self.help_panel)
        help_layout.setSpacing(4)
        help_title = QLabel(
            "<b style='color:#a6e3a1;'>\U0001f916 Quick Prompt Examples</b> "
            "<span style='color:#6c7086;'>- Click to auto-fill</span>"
        )
        help_layout.addWidget(help_title)

        row1 = QHBoxLayout()
        row2 = QHBoxLayout()
        for i, (icon, prompt) in enumerate(self.PROMPT_EXAMPLES):
            short = icon + " " + prompt.split(":")[0]
            btn = QPushButton(short)
            btn.setToolTip(prompt[:120] + "..." if len(prompt) > 120 else prompt)
            btn.setStyleSheet(
                "QPushButton { background-color: #313244; color: #a6e3a1; border: 1px solid #45475a;"
                " border-radius: 4px; padding: 6px 10px; font-size: 9pt; text-align: left; }"
                " QPushButton:hover { background-color: #45475a; border-color: #a6e3a1; }"
            )
            btn.clicked.connect(lambda checked, p=prompt: self.fill_prompt(p))
            (row1 if i < 4 else row2).addWidget(btn)
        help_layout.addLayout(row1)
        help_layout.addLayout(row2)

        tips = QLabel(
            "<span style='color:#6c7086;font-size:9pt;'>\U0001f4a1 Tip: Describe your task naturally. "
            "GeoPilot can process vectors, rasters, run analyses, and generate SCI figures.</span>"
        )
        help_layout.addWidget(tips)
        self.help_panel.setVisible(False)
        main_layout.addWidget(self.help_panel)

        # PROVIDER SETTINGS
        settings_group = QGroupBox("\u2699 Provider Settings")
        settings_group.setCheckable(True)
        settings_group.setChecked(False)
        settings_layout = QVBoxLayout(settings_group)

        prov_row = QHBoxLayout()
        prov_row.addWidget(QLabel("Provider:"))
        self.provider_combo = QComboBox()
        self.update_provider_list()
        self.provider_combo.setMinimumWidth(180)
        self.provider_combo.currentTextChanged.connect(self.on_provider_changed)
        prov_row.addWidget(self.provider_combo)
        prov_row.addSpacing(10)
        prov_row.addWidget(QLabel("Model:"))
        self.model_combo = QComboBox()
        self.model_combo.setEditable(True)
        self.model_combo.setMinimumWidth(200)
        prov_row.addWidget(self.model_combo)
        prov_row.addStretch()
        settings_layout.addLayout(prov_row)

        api_row = QHBoxLayout()
        api_row.addWidget(QLabel("API Key:"))
        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.Password)
        self.api_key_input.setPlaceholderText("Enter your API key...")
        api_row.addWidget(self.api_key_input)
        api_row.addSpacing(10)
        api_row.addWidget(QLabel("Base URL:"))
        self.base_url_input = QLineEdit()
        self.base_url_input.setPlaceholderText("Custom endpoint (optional)")
        api_row.addWidget(self.base_url_input)
        settings_layout.addLayout(api_row)

        sys_row = QHBoxLayout()
        sys_row.addWidget(QLabel("System Prompt:"))
        self.sys_prompt_input = QLineEdit()
        self.sys_prompt_input.setPlaceholderText("Custom system prompt (optional)")
        sys_row.addWidget(self.sys_prompt_input)
        settings_layout.addLayout(sys_row)

        # Safety toggle
        from qgis.PyQt.QtWidgets import QCheckBox

        self.auto_exec_check = QCheckBox("Auto-execute generated code (disable to confirm before running)")
        self.auto_exec_check.setChecked(False)
        self.auto_exec_check.setStyleSheet("QCheckBox { color: #f9e2af; font-size: 9pt; }")
        settings_layout.addWidget(self.auto_exec_check)

        main_layout.addWidget(settings_group)

        # CHAT
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        main_layout.addWidget(self.chat_display, stretch=1)

        # INPUT
        input_frame = QFrame()
        input_frame.setStyleSheet(
            "QFrame { background-color: #181825; border: 1px solid #313244; border-radius: 6px; padding: 4px; }"
        )
        input_layout_inner = QVBoxLayout(input_frame)
        input_layout_inner.setSpacing(4)
        input_layout_inner.setContentsMargins(4, 4, 4, 4)

        self.input_field = QTextEdit()
        self.input_field.setPlaceholderText("Describe your geospatial task\ne.g. Calculate NDVI on the active raster")
        self.input_field.setMaximumHeight(70)
        self.input_field.setStyleSheet(
            "QTextEdit { background-color: #1e1e2e; border: 1px solid #313244; border-radius: 4px; padding: 6px;"
            " font-size: 11pt; } QTextEdit:focus { border-color: #89b4fa; }"
        )
        input_layout_inner.addWidget(self.input_field)

        btn_row = QHBoxLayout()
        self.send_btn = QPushButton("\u25b6 Send")
        self.send_btn.setStyleSheet(
            "QPushButton { background-color: #89b4fa; color: #1e1e2e; font-weight: bold; padding: 8px 24px;"
            " border-radius: 4px; font-size: 11pt; }"
            " QPushButton:hover { background-color: #74c7ec; }"
            " QPushButton:disabled { background-color: #45475a; color: #6c7086; }"
        )
        self.send_btn.clicked.connect(self.on_send)
        btn_row.addWidget(self.send_btn)

        self.clear_btn = QPushButton("\U0001f9f9 Clear")
        self.clear_btn.setStyleSheet(
            "QPushButton { background-color: #313244; color: #f38ba8; padding: 8px 16px; border-radius: 4px; }"
            " QPushButton:hover { background-color: #45475a; }"
        )
        self.clear_btn.clicked.connect(self.clear_chat)
        btn_row.addWidget(self.clear_btn)

        self.stop_btn = QPushButton("\u23f9 Stop")
        self.stop_btn.setStyleSheet(
            "QPushButton { background-color: #313244; color: #fab387; padding: 8px 16px; border-radius: 4px; }"
            " QPushButton:hover { background-color: #45475a; }"
        )
        self.stop_btn.clicked.connect(self.on_stop)
        self.stop_btn.setEnabled(False)
        btn_row.addWidget(self.stop_btn)

        btn_row.addStretch()
        status_label = QLabel(
            "<span style='color:#6c7086;font-size:9pt;'>Enter to send  |  Shift+Enter for new line</span>"
        )
        btn_row.addWidget(status_label)
        input_layout_inner.addLayout(btn_row)
        main_layout.addWidget(input_frame)

        # PROGRESS
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        self.progress.setMaximumHeight(4)
        main_layout.addWidget(self.progress)

        self.setLayout(main_layout)
        self.input_field.installEventFilter(self)

    # --------------------------------------------------------------- slots --

    def toggle_help(self, checked):
        self.help_panel.setVisible(checked)

    def fill_prompt(self, prompt):
        self.input_field.setPlainText(prompt)

    def show_welcome(self):
        welcome = (
            '<div style="text-align:center;padding:30px;">'
            '<h2 style="color:#89b4fa;">\U0001f30d Welcome to GeoPilot</h2>'
            '<p style="color:#a6e3a1;font-size:11pt;">Your AI Geospatial Analysis Assistant for QGIS</p>'
            '<hr style="border-color:#313244;width:60%;">'
            '<p style="color:#6c7086;font-size:10pt;">'
            "1. \u2699 Click <b>Provider Settings</b> to configure your AI model<br>"
            "2. \U0001f4dd Type your task in natural language<br>"
            "3. \U0001f916 GeoPilot will generate QGIS Python code for you to review<br>"
            "4. \u2705 Run the code safely from the chat<br>"
            "5. \u2753 Click <b>Help</b> for example prompts"
            "</p>"
            '<p style="color:#585b70;font-size:9pt;">'
            "Supports 18 AI providers \u2022 Vector &amp; Raster Analysis \u2022 Remote Sensing \u2022 SCI Figures"
            "</p></div>"
        )
        self.chat_display.setHtml(welcome)

    def on_provider_changed(self, provider_text):
        self.model_combo.clear()
        try:
            from .providers import list_providers

            registry = list_providers()
            name = provider_text
            if "(" in provider_text:
                name = provider_text.split("(")[-1].rstrip(")")
            entry = registry.get(name, {})
            models = entry.get("models", ["default"])
            for m in models:
                self.model_combo.addItem(m)
            if models:
                self.model_combo.setCurrentIndex(0)
        except Exception:
            self.model_combo.addItems(["gpt-4o", "gpt-4o-mini"])

    # ---------------------------------------------------------- settings --

    def load_settings(self):
        provider = self.settings.value("geopilot/provider", "")
        if provider:
            idx = self.provider_combo.findData(provider)
            if idx >= 0:
                self.provider_combo.setCurrentIndex(idx)

        model = self.settings.value("geopilot/model", "")
        if model:
            idx = self.model_combo.findText(model)
            if idx >= 0:
                self.model_combo.setCurrentIndex(idx)
            else:
                self.model_combo.setCurrentText(model)

        # API keys are stored in QSettings under a dedicated prefix; note that
        # QSettings stores data in the user profile (not encrypted). We keep the
        # value obfuscated with a trivial XOR so it is not visible in plaintext
        # to casual snooping of the settings file.
        api_key = _str_decode(self.settings.value("geopilot/api_key", ""))
        if api_key:
            self.api_key_input.setText(api_key)
        base_url = self.settings.value("geopilot/base_url", "")
        if base_url:
            self.base_url_input.setText(base_url)
        sys_prompt = self.settings.value("geopilot/system_prompt", "")
        if sys_prompt:
            self.sys_prompt_input.setText(sys_prompt)
        self.auto_exec_check.setChecked(
            self.settings.value("geopilot/auto_exec", "false").lower() == "true"
        )

    def save_settings(self):
        self.settings.setValue(
            "geopilot/provider",
            self.provider_combo.currentData() or self.provider_combo.currentText(),
        )
        self.settings.setValue("geopilot/model", self.model_combo.currentText())
        self.settings.setValue("geopilot/api_key", _str_encode(self.api_key_input.text()))
        self.settings.setValue("geopilot/base_url", self.base_url_input.text())
        self.settings.setValue("geopilot/system_prompt", self.sys_prompt_input.text())
        self.settings.setValue(
            "geopilot/auto_exec", "true" if self.auto_exec_check.isChecked() else "false"
        )

    def update_provider_list(self):
        try:
            from .providers import list_providers

            for name, info in list_providers().items():
                display = info.get("display_name", name)
                self.provider_combo.addItem(f"{display} ({name})", name)
        except Exception:
            self.provider_combo.addItems(["openai", "anthropic", "ollama", "google", "deepseek"])

    def get_provider(self):
        from .providers import get_provider

        name = self.provider_combo.currentData()
        if not name:
            current = self.provider_combo.currentText()
            name = current.split("(")[-1].rstrip(")") if "(" in current else current
        model = self.model_combo.currentText()
        api_key = self.api_key_input.text().strip()
        base_url = self.base_url_input.text().strip() or None
        return get_provider(name, api_key=api_key, model=model, base_url=base_url)

    # ----------------------------------------------------------- chat log --

    def add_message(self, role, content):
        self.conversation.append({"role": role, "content": content})
        if role == "user":
            prefix = (
                "<div style='background-color:#313244;border-radius:6px;padding:8px 12px;margin:4px 0;'>"
                "<b style='color:#89b4fa;'>\U0001f464 You</b><br>"
            )
        else:
            prefix = (
                "<div style='background-color:#181825;border-radius:6px;padding:8px 12px;margin:4px 0;'>"
                "<b style='color:#a6e3a1;'>\U0001f916 GeoPilot</b><br>"
            )
        escaped = html.escape(content).replace("\n", "<br>")
        escaped = _CODE_BLOCK_RE.sub(
            r"<pre style='background-color:#11111b;color:#cdd6f4;padding:8px;border-radius:4px;"
            r"font-size:10pt;white-space:pre-wrap;'><code>\1</code></pre>",
            escaped,
        )
        escaped = _CODE_INLINE_RE.sub(
            r"<code style='background-color:#11111b;color:#fab387;padding:1px 4px;border-radius:2px;'>\1</code>",
            escaped,
        )
        self.chat_display.append(prefix + escaped + "</div>")
        self.chat_display.moveCursor(QTextCursor.End)

    # ------------------------------------------------------------ context --

    def build_qgis_context(self):
        info = []
        try:
            layers = QgsProject.instance().layerTreeRoot().findLayers()
            info.append(f"Layers in project: {len(layers)}")
            for layer_node in layers[:15]:
                layer = layer_node.layer()
                try:
                    crs = layer.crs().authid()
                except Exception:
                    crs = "?"
                try:
                    extent = layer.extent().toString()
                except Exception:
                    extent = "?"
                try:
                    fc = layer.featureCount()
                except Exception:
                    fc = "?"
                info.append(
                    f"  [{layer.name()}] type={layer.type().__class__.__name__} CRS={crs} features={fc} extent={extent}"
                )
                if hasattr(layer, "fields"):
                    try:
                        fields = [f.name() for f in layer.fields()]
                        if fields:
                            info.append(f"    Fields: {', '.join(fields[:12])}")
                    except Exception:
                        pass

            reg = QgsApplication.processingRegistry()
            common = [
                "native:buffer",
                "native:clip",
                "native:union",
                "native:intersection",
                "native:dissolve",
                "native:mergevectorlayers",
                "native:reprojectlayer",
                "native:extractbyexpression",
                "native:fieldcalculator",
                "native:rastercalc",
                "native:slope",
                "native:aspect",
                "native:hillshade",
                "native:contour",
                "native:polygonize",
                "native:creategrid",
                "native:printlayouttoimage",
                "native:createconstantraster",
                "native:savefeatures",
                "native:joinattributesbylocation",
                "native:createspatialindex",
            ]
            avail = [a for a in common if a in reg.algorithms()]
            info.append(f"Available common algs: {len(avail)} -> {', '.join(avail)}")
            proj = QgsProject.instance()
            info.append(f"Project: {proj.fileName() or 'unsaved'} CRS: {proj.crs().authid()}")
        except Exception as e:
            info.append(f"Context err: {e}")
        return "\n".join(info)

    # ---------------------------------------------------------- send flow -

    def on_send(self):
        text = self.input_field.toPlainText().strip()
        if not text:
            return
        self.save_settings()
        self.input_field.clear()
        self.add_message("user", text)

        try:
            provider = self.get_provider()
        except Exception as e:
            self.add_message("assistant", f"\u274c Provider error: {e}")
            return

        sys_prompt = self.sys_prompt_input.text().strip() or self.SYSTEM_PROMPT_DEFAULT

        # Build messages: system prompt, then recent conversation (last 12 turns = 24 msgs).
        # We inject a fresh context snapshot into the latest user message so the model
        # always sees current layer state; we keep history so multi-turn works.
        history = [m for m in self.conversation[:-1] if m.get("role") in ("user", "assistant")][-20:]
        context = self.build_qgis_context()
        enriched_user = f"QGIS STATE:\n{context}\n\nUSER REQUEST: {text}"
        messages = [{"role": "system", "content": sys_prompt}] + history + [
            {"role": "user", "content": enriched_user}
        ]

        self._set_running(True)
        self.worker = ApiWorker(provider, messages[1:], system=sys_prompt)
        self.worker.finished.connect(self.on_response)
        self.worker.error.connect(self.on_error)
        self.worker.finished.connect(lambda _: self._set_running(False))
        self.worker.error.connect(lambda _: self._set_running(False))
        self.worker.start()

    def on_stop(self):
        if self.worker and self.worker.isRunning():
            self.worker.abort()
            self.worker.quit()
            self.worker.wait(1000)
        self._set_running(False)
        self.add_message("assistant", "\u23f9 Stopped.")

    def _set_running(self, running):
        self.progress.setVisible(running)
        self.progress.setRange(0, 0 if running else 100)
        self.send_btn.setEnabled(not running)
        self.stop_btn.setEnabled(running)

    def on_response(self, response):
        self.add_message("assistant", response)
        blocks = _CODE_BLOCK_RE.findall(response)
        if blocks:
            self._pending_code_blocks = blocks
            if self.auto_exec_check.isChecked():
                self.exec_qgis_code(blocks)
            else:
                self._offer_code_execution(blocks)

    def on_error(self, error):
        self.add_message("assistant", f"\u274c {error}")

    def clear_chat(self):
        self.chat_display.clear()
        self.conversation = []
        self.show_welcome()

    # ------------------------------------------------------ code execution -

    def _offer_code_execution(self, blocks):
        """Ask the user before running AI-generated code."""
        count = len(blocks)
        preview = blocks[0].strip().splitlines()[0] if blocks else ""
        msg = QMessageBox(self)
        msg.setWindowTitle("Run generated code?")
        msg.setIcon(QMessageBox.Warning)
        msg.setText(
            f"GeoPilot generated {count} Python code block(s).\n"
            f"First line: <b>{html.escape(preview[:120])}</b>\n\n"
            "Review the code in the chat above before running. Running arbitrary code "
            "can modify your project or files on disk."
        )
        run_btn = msg.addButton("Run code", QMessageBox.AcceptRole)
        skip_btn = msg.addButton("Do not run", QMessageBox.RejectRole)
        always_btn = msg.addButton("Always run (not recommended)", QMessageBox.ActionRole)
        msg.setDefaultButton(skip_btn)
        msg.exec_()
        clicked = msg.clickedButton()
        if clicked == run_btn:
            self.exec_qgis_code(blocks)
        elif clicked == always_btn:
            self.auto_exec_check.setChecked(True)
            self.save_settings()
            self.exec_qgis_code(blocks)
        else:
            self.add_message("assistant", "\u23f8 Code execution skipped by user.")

    def exec_qgis_code(self, code_blocks):
        """Execute Python code blocks with a restrained namespace."""
        # Guard against catastrophic patterns. This is not a sandbox — it is a
        # last-resort safety net for obviously destructive calls.
        forbidden = [
            (r"os\.system\s*\(", "os.system("),
            (r"subprocess\.", "subprocess"),
            (r"shutil\.rmtree\s*\(", "shutil.rmtree("),
            (r"\beval\s*\(", "eval("),
            (r"__import__\s*\(\s*['\"]subprocess", "__import__('subprocess'"),
        ]
        for i, code in enumerate(code_blocks):
            for pat, name in forbidden:
                if re.search(pat, code):
                    self.add_message(
                        "assistant",
                        f"\u26d4 Block {i + 1} refused: contains blocked call <code>{name}</code>. "
                        "Edit your request and retry, or run the code manually in the QGIS Python console.",
                    )
                    return

        # Prepare execution namespace
        try:
            from qgis import processing
            from qgis.core import (
                QgsApplication,
                QgsFeature,
                QgsField,
                QgsFields,
                QgsGeometry,
                QgsMessageLog,
                QgsProcessingFeedback,
                QgsProject,
                QgsRasterLayer,
                QgsVectorLayer,
            )
        except Exception as e:
            self.add_message("assistant", f"\u274c QGIS import error: {e}")
            return

        exec_locals = {
            "iface": self.iface,
            "QgsProject": QgsProject,
            "QgsVectorLayer": QgsVectorLayer,
            "QgsRasterLayer": QgsRasterLayer,
            "QgsMessageLog": QgsMessageLog,
            "QgsProcessingFeedback": QgsProcessingFeedback,
            "QgsFeature": QgsFeature,
            "QgsGeometry": QgsGeometry,
            "QgsField": QgsField,
            "QgsFields": QgsFields,
            "QgsApplication": QgsApplication,
            "processing": processing,
        }

        # Replace builtins.print for the duration of exec using a context manager
        # pattern so we don't clobber it across threads if something goes wrong.
        import builtins
        import io

        for i, code in enumerate(code_blocks):
            output_buf = io.StringIO()

            def _print(*args, sep=" ", end="\n", **_kw):
                output_buf.write(sep.join(str(a) for a in args) + end)

            saved_print = builtins.print
            builtins.print = _print
            try:
                exec(compile(code, f"<geopilot-block-{i + 1}>", "exec"), exec_locals, exec_locals)  # nosec - user-confirmed
            except Exception:
                tb = traceback.format_exc()
                self.add_message(
                    "assistant",
                    f"\u274c Block {i + 1} error:\n```\n{tb[-800:]}\n```",
                )
            else:
                out = output_buf.getvalue().strip()
                msg = out if out else "Executed successfully."
                self.add_message("assistant", f"\u2705 Block {i + 1}: {msg}")
                if self.iface:
                    try:
                        self.iface.messageBar().pushMessage(
                            "GeoPilot", f"Block {i + 1} executed", level=0, duration=3
                        )
                    except Exception:
                        pass
                QgsMessageLog.logMessage(
                    f"GeoPilot executed block {i + 1}:\n{code[-500:]}", "GeoPilot", level=0
                )
            finally:
                builtins.print = saved_print

    # ----------------------------------------------------------- events --

    def eventFilter(self, obj, event):
        if obj == self.input_field and event.type() == QEvent.KeyPress:
            if event.key() == Qt.Key_Return and not (event.modifiers() & Qt.ShiftModifier):
                self.on_send()
                return True
        return super().eventFilter(obj, event)

    def closeEvent(self, event):
        self.save_settings()
        if self.worker and self.worker.isRunning():
            self.worker.abort()
            self.worker.quit()
            self.worker.wait(2000)
        super().closeEvent(event)


# ---------------------------------------------------------------- helpers --


def _str_encode(s: str) -> str:
    """Trivially XOR a string so it isn't stored as plaintext in QSettings.

    This is NOT cryptographically secure — it just prevents a casual glance at the
    settings file from revealing API keys.
    """
    if not s:
        return ""
    key = "GeoPilot!"
    out = bytearray()
    for i, ch in enumerate(s.encode("utf-8")):
        out.append(ch ^ ord(key[i % len(key)]))
    return out.hex()


def _str_decode(s: str) -> str:
    if not s:
        return ""
    try:
        raw = bytes.fromhex(s)
    except ValueError:
        # Backward compat: older versions stored plaintext
        return s
    key = "GeoPilot!"
    out = bytearray()
    for i, ch in enumerate(raw):
        out.append(ch ^ ord(key[i % len(key)]))
    try:
        return out.decode("utf-8")
    except UnicodeDecodeError:
        return ""
