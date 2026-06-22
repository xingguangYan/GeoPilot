"""GeoPilot Chat Dialog - Natural-Language Geospatial Interface"""

import os
import html
import traceback

from qgis.PyQt.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QTextEdit,
    QPushButton,
    QComboBox,
    QLabel,
    QLineEdit,
    QGroupBox,
    QProgressBar,
    QFrame,
    QToolButton,
)

from qgis.PyQt.QtGui import QTextCursor

from qgis.PyQt.QtCore import Qt, QThread, pyqtSignal, QSettings

from qgis.core import QgsProject, QgsMessageLog

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

    PROMPT_EXAMPLES = [
        (
            "\U0001f5fa 研究区分析",
            "Create Figure 1: Study area map showing the location with satellite imagery, administrative boundaries, scale bar, north arrow, and legend.",
        ),
        ("\U0001f33f 植被分析", "Calculate NDVI from the current multispectral raster and create a time series chart."),
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

    SYSTEM_PROMPT_DEFAULT = """You are GeoPilot, an AI assistant that directly controls QGIS through Python code.

CRITICAL: You must respond with executable QGIS Python code. Your code WILL be executed automatically.

Key APIs:

- QgsProject.instance().mapLayers() - access layers

- QgsProject.instance().addMapLayer(layer) - add layers

- processing.run("native:buffer", {...}) - run algorithms

- iface.messageBar().pushMessage() - show messages to user

Output format:

```python

# Your QGIS Python code here

```

After code, explain briefly what was done. Use user's language."""

    def __init__(self, iface, plugin_dir):

        super().__init__(iface.mainWindow())

        self.iface = iface

        self.plugin_dir = plugin_dir

        self.settings = QSettings()

        self.conversation = []

        self.current_provider = None

        self.worker = None

        self.help_visible = False

        self.setup_ui()

        self.load_settings()

        self.show_welcome()

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

            QTextEdit { background-color: #1e1e2e; color: #cdd6f4; border: 1px solid #313244; border-radius: 4px; font-family: Consolas; font-size: 11pt; }

            QScrollBar:vertical { background-color: #1e1e2e; width: 8px; }

            QScrollBar::handle:vertical { background-color: #45475a; border-radius: 4px; min-height: 20px; }

            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }

        """
        )

        main_layout = QVBoxLayout()

        main_layout.setSpacing(6)

        main_layout.setContentsMargins(10, 10, 10, 10)

        # ========== HEADER ==========

        header = QHBoxLayout()

        title_label = QLabel(
            "<b style='color:#89b4fa;font-size:14pt;'>GeoPilot</b>  <span style='color:#6c7086;font-size:9pt;'>AI Geospatial Assistant</span>"
        )

        header.addWidget(title_label)

        header.addStretch()

        self.help_btn = QToolButton()

        self.help_btn.setText("\u2753 Help")

        self.help_btn.setCheckable(True)

        self.help_btn.setChecked(False)

        self.help_btn.toggled.connect(self.toggle_help)

        self.help_btn.setStyleSheet(
            "QToolButton { background-color: #313244; color: #a6e3a1; border: 1px solid #45475a; border-radius: 4px; padding: 4px 12px; } QToolButton:hover { border-color: #a6e3a1; } QToolButton:checked { background-color: #45475a; }"
        )

        header.addWidget(self.help_btn)

        main_layout.addLayout(header)

        # ========== HELP PANEL (collapsible) ==========

        self.help_panel = QFrame()

        self.help_panel.setStyleSheet(
            "QFrame { background-color: #181825; border: 1px solid #313244; border-radius: 6px; padding: 8px; }"
        )

        help_layout = QVBoxLayout(self.help_panel)

        help_layout.setSpacing(4)

        help_title = QLabel(
            "<b style='color:#a6e3a1;'>\U0001f916 Quick Prompt Examples</b> <span style='color:#6c7086;'>- Click to auto-fill</span>"
        )

        help_layout.addWidget(help_title)

        # Prompt suggestion buttons in a grid

        btn_grid = QHBoxLayout()

        btn_grid.setSpacing(4)

        row1 = QHBoxLayout()

        row2 = QHBoxLayout()

        for i, (icon, prompt) in enumerate(self.PROMPT_EXAMPLES):

            btn = QPushButton(f"{icon} {prompt.split(':')[0]}")

            btn.setToolTip(prompt[:80] + "..." if len(prompt) > 80 else prompt)

            btn.setStyleSheet(
                "QPushButton { background-color: #313244; color: #a6e3a1; border: 1px solid #45475a; border-radius: 4px; padding: 6px 10px; font-size: 9pt; text-align: left; } QPushButton:hover { background-color: #45475a; border-color: #a6e3a1; }"
            )

            btn.clicked.connect(lambda checked, p=prompt: self.fill_prompt(p))

            if i < 4:

                row1.addWidget(btn)

            else:

                row2.addWidget(btn)

        btn_grid.addLayout(row1)

        help_layout.addLayout(btn_grid)

        help_layout.addLayout(row2)

        # Tips text

        tips = QLabel(
            "<span style='color:#6c7086;font-size:9pt;'>\U0001f4a1 Tip: Describe your task naturally. GeoPilot can process vectors, rasters, run analyses, and generate SCI figures.</span>"
        )

        help_layout.addWidget(tips)

        self.help_panel.setVisible(False)

        main_layout.addWidget(self.help_panel)

        # ========== PROVIDER SETTINGS ==========

        settings_group = QGroupBox("\u2699 Provider Settings")

        settings_group.setCheckable(True)

        settings_group.setChecked(False)

        settings_group.setStyleSheet(settings_group.styleSheet() + "QGroupBox { font-size: 10pt; }")

        settings_layout = QVBoxLayout(settings_group)

        # Provider + Model row

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

        # API Key + Base URL

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

        # System prompt

        sys_row = QHBoxLayout()

        sys_row.addWidget(QLabel("System Prompt:"))

        self.sys_prompt_input = QLineEdit()

        self.sys_prompt_input.setPlaceholderText("Custom system prompt (optional)")

        sys_row.addWidget(self.sys_prompt_input)

        settings_layout.addLayout(sys_row)

        main_layout.addWidget(settings_group)

        # ========== CHAT DISPLAY ==========

        self.chat_display = QTextEdit()

        self.chat_display.setReadOnly(True)

        main_layout.addWidget(self.chat_display, stretch=1)

        # ========== INPUT AREA ==========

        input_frame = QFrame()

        input_frame.setStyleSheet(
            "QFrame { background-color: #181825; border: 1px solid #313244; border-radius: 6px; padding: 4px; }"
        )

        input_layout_inner = QVBoxLayout(input_frame)

        input_layout_inner.setSpacing(4)

        input_layout_inner.setContentsMargins(4, 4, 4, 4)

        self.input_field = QTextEdit()

        self.input_field.setPlaceholderText("Describe your geospatial task\ne.g. Calculate NDVI")

        self.input_field.setMaximumHeight(70)

        self.input_field.setStyleSheet(
            "QTextEdit { background-color: #1e1e2e; border: 1px solid #313244; border-radius: 4px; padding: 6px; font-size: 11pt; } QTextEdit:focus { border-color: #89b4fa; }"
        )

        input_layout_inner.addWidget(self.input_field)

        btn_row = QHBoxLayout()

        self.send_btn = QPushButton("\u25b6 Send")

        self.send_btn.setStyleSheet(
            "QPushButton { background-color: #89b4fa; color: #1e1e2e; font-weight: bold; padding: 8px 24px; border-radius: 4px; font-size: 11pt; } QPushButton:hover { background-color: #74c7ec; } QPushButton:disabled { background-color: #45475a; color: #6c7086; }"
        )

        self.send_btn.clicked.connect(self.on_send)

        btn_row.addWidget(self.send_btn)

        self.clear_btn = QPushButton("\U0001f9f9 Clear")

        self.clear_btn.setStyleSheet(
            "QPushButton { background-color: #313244; color: #f38ba8; padding: 8px 16px; border-radius: 4px; } QPushButton:hover { background-color: #45475a; }"
        )

        self.clear_btn.clicked.connect(self.clear_chat)

        btn_row.addWidget(self.clear_btn)

        btn_row.addStretch()

        status_label = QLabel(
            "<span style='color:#6c7086;font-size:9pt;'>Enter to send  |  Shift+Enter for new line</span>"
        )

        btn_row.addWidget(status_label)

        input_layout_inner.addLayout(btn_row)

        main_layout.addWidget(input_frame)

        # ========== PROGRESS BAR ==========

        self.progress = QProgressBar()

        self.progress.setVisible(False)

        self.progress.setMaximumHeight(4)

        main_layout.addWidget(self.progress)

        self.setLayout(main_layout)

        # Keyboard shortcut: Enter to send

        self.input_field.installEventFilter(self)

    def toggle_help(self, checked):
        """Toggle help panel visibility."""

        self.help_panel.setVisible(checked)

    def fill_prompt(self, prompt):
        """Fill input field with example prompt."""

        self.input_field.setPlainText(prompt)

    def show_welcome(self):
        """Show welcome message."""

        welcome = (
            '<div style="text-align:center;padding:30px;">'
            '<h2 style="color:#89b4fa;">\U0001f30d Welcome to GeoPilot</h2>'
            '<p style="color:#a6e3a1;font-size:11pt;">Your AI Geospatial Analysis Assistant for QGIS</p>'
            '<hr style="border-color:#313244;width:60%;">'
            '<p style="color:#6c7086;font-size:10pt;">'
            "1. \u2699 Click <b>Provider Settings</b> to configure your AI model<br>"
            "2. \U0001f4dd Type your task in natural language<br>"
            "3. \U0001f916 GeoPilot will analyze, process, and generate results<br>"
            "4. \u2753 Click <b>Help</b> for example prompts"
            "</p>"
            '<p style="color:#585b70;font-size:9pt;">'
            "Supports 18 AI providers \u2022 Vector & Raster Analysis \u2022 Remote Sensing \u2022 SCI Figures"
            "</p></div>"
        )

        self.chat_display.setHtml(welcome)

    def on_provider_changed(self, provider_text):
        """Update model list when provider changes."""

        self.model_combo.clear()

        try:

            from .providers import list_providers

            registry = list_providers()

            # Extract provider name from display text

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

    def load_settings(self):
        """Load saved settings."""

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

        api_key = self.settings.value("geopilot/api_key", "")

        if api_key:

            self.api_key_input.setText(api_key)

        base_url = self.settings.value("geopilot/base_url", "")

        if base_url:

            self.base_url_input.setText(base_url)

        sys_prompt = self.settings.value("geopilot/system_prompt", "")

        if sys_prompt:

            self.sys_prompt_input.setText(sys_prompt)

    def save_settings(self):
        """Save current settings."""

        self.settings.setValue(
            "geopilot/provider", self.provider_combo.currentData() or self.provider_combo.currentText()
        )

        self.settings.setValue("geopilot/model", self.model_combo.currentText())

        self.settings.setValue("geopilot/api_key", self.api_key_input.text())

        self.settings.setValue("geopilot/base_url", self.base_url_input.text())

        self.settings.setValue("geopilot/system_prompt", self.sys_prompt_input.text())

    def update_provider_list(self):
        """Populate provider list from registry."""

        try:

            registry = list_providers()

            for name, info in registry.items():

                display = info.get("display_name", name)

                self.provider_combo.addItem(f"{display} ({name})", name)

        except Exception:

            self.provider_combo.addItems(["openai", "anthropic", "ollama", "google", "deepseek"])

    def get_provider(self):
        """Get current API provider instance."""

        from .providers import get_provider

        name = self.provider_combo.currentData()

        if not name:

            name = (
                self.provider_combo.currentText().split("(")[-1].rstrip(")")
                if "(" in self.provider_combo.currentText()
                else self.provider_combo.currentText()
            )

        model = self.model_combo.currentText()

        api_key = self.api_key_input.text().strip()

        base_url = self.base_url_input.text().strip() or None

        return get_provider(name, api_key=api_key, model=model, base_url=base_url)

    def add_message(self, role, content):
        """Add a message to the chat display."""

        self.conversation.append({"role": role, "content": content})

        if role == "user":

            prefix = "<div style='background-color:#313244;border-radius:6px;padding:8px 12px;margin:4px 0;'><b style='color:#89b4fa;'>\U0001f464 You</b><br>"

        else:

            prefix = "<div style='background-color:#181825;border-radius:6px;padding:8px 12px;margin:4px 0;'><b style='color:#a6e3a1;'>\U0001f916 GeoPilot</b><br>"

        escaped = html.escape(content).replace("\n", "<br>")

        # Format code blocks

        escaped = re.sub(
            r"```(\w*)\n(.*?)\n```",
            r"<pre style='background-color:#11111b;color:#cdd6f4;padding:8px;border-radius:4px;font-size:10pt;'><code>\2</code></pre>",
            escaped,
            flags=re.DOTALL,
        )

        escaped = re.sub(
            r"`([^`]+)`",
            r"<code style='background-color:#11111b;color:#fab387;padding:1px 4px;border-radius:2px;'>\1</code>",
            escaped,
        )

        self.chat_display.append(prefix + escaped + "</div>")

        self.chat_display.moveCursor(QTextCursor.End)

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
                    _ = layer.extent().toString()

                except Exception:
                    ext = "?"

                try:
                    fc = layer.featureCount()

                except Exception:
                    fc = "?"

                info.append(f"  [{layer.name()}] type={layer.type().__class__.__name__} CRS={crs} features={fc}")

                if hasattr(layer, "fields"):

                    fields = [f.name() for f in layer.fields()]

                    if fields:
                        info.append(f"    Fields: {', '.join(fields[:12])}")

            from qgis.core import QgsApplication

            reg = QgsApplication.processingRegistry()

            common = [
                "native:buffer",
                "native:clip",
                "native:union",
                "native:intersect",
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
                "native:reclassifybylayer",
                "native:polygonize",
                "native:creategrid",
                "native:printlayouttoimage",
                "native:createconstantraster",
                "native:savefeatures",
                "native:joinattributesbylocation",
                "native:createspatialindex",
            ]

            avail = [a for a in common if a in reg.algorithms()]

            info.append(f"Available algs: {len(avail)} -> {', '.join(avail)}")

            proj = QgsProject.instance()

            info.append(f"Project: {proj.fileName() or 'unsaved'} CRS: {proj.crs().authid()}")

        except Exception as e:

            info.append(f"Context err: {e}")

        return chr(10).join(info)

    def on_send(self):

        text = self.input_field.toPlainText().strip()

        if not text:

            return

        self.save_settings()

        self.input_field.clear()

        self.add_message("user", text)

        context = self.build_qgis_context()

        try:

            provider = self.get_provider()

        except Exception as e:

            self.add_message("assistant", f"\u274c Provider error: {str(e)}")

            return

        sys_prompt = self.sys_prompt_input.text().strip() or self.SYSTEM_PROMPT_DEFAULT

        messages = [{"role": "system", "content": sys_prompt}]

        if context:

            messages.append({"role": "user", "content": f"QGIS STATE:\n{context}\n\nUSER REQUEST: {text}"})

        else:

            messages.extend(self.conversation[-20:])

        self.progress.setVisible(True)

        self.progress.setRange(0, 0)

        self.send_btn.setEnabled(False)

        self.worker = ApiWorker(provider, messages)

        self.worker.finished.connect(self.on_response)

        self.worker.error.connect(self.on_error)

        self.worker.start()

    def on_response(self, response):

        self.progress.setVisible(False)

        self.send_btn.setEnabled(True)

        self.add_message("assistant", response)

        blocks = re.findall(r"```python\n(.*?)\n```", response, re.DOTALL)

        if blocks:

            self.exec_qgis_code(blocks)

    def exec_qgis_code(self, code_blocks):

        for i, code in enumerate(code_blocks):

            try:

                # Capture print output

                import builtins

                orig_print = builtins.print

                output = []

                builtins.print = lambda *a, **k: output.append(" ".join(str(x) for x in a))

                exec_locals = {
                    "iface": self.iface,
                    "output": output,
                }

                # Add QGIS modules

                try:

                    from qgis.core import QgsVectorLayer, QgsRasterLayer, QgsProcessingFeedback

                    exec_locals["QgsProject"] = QgsProject

                    exec_locals["QgsVectorLayer"] = QgsVectorLayer

                    exec_locals["QgsRasterLayer"] = QgsRasterLayer

                    exec_locals["QgsMessageLog"] = QgsMessageLog

                    exec_locals["QgsProcessingFeedback"] = QgsProcessingFeedback

                    exec_locals["QgsFeature"] = __import__("qgis.core", fromlist=["QgsFeature"]).QgsFeature

                    exec_locals["QgsGeometry"] = __import__("qgis.core", fromlist=["QgsGeometry"]).QgsGeometry

                    exec_locals["QgsField"] = __import__("qgis.core", fromlist=["QgsField"]).QgsField

                    exec_locals["QgsFields"] = __import__("qgis.core", fromlist=["QgsFields"]).QgsFields

                    from qgis import processing

                    exec_locals["processing"] = processing

                    exec_locals["QgsApplication"] = QgsApplication

                except Exception as e:

                    output.append(f"QGIS import err: {e}")

                exec(code, exec_locals)  # nosec

                builtins.print = orig_print

                msg = "\n".join(output) if output else "Executed successfully."

                self.add_message("assistant", f"\u2705 Block {i + 1}: {msg}")

                if self.iface:

                    try:

                        self.iface.messageBar().pushMessage("GeoPilot", f"Block {i + 1} executed", level=0, duration=3)

                    except Exception:

                        pass

            except Exception as e:

                tb = traceback.format_exc()

                self.add_message("assistant", f"\u274c Block {i + 1}: {str(e)}\n```\n{tb[-500:]}\n```")

    def on_error(self, error):
        """Handle API error."""

        self.progress.setVisible(False)

        self.send_btn.setEnabled(True)

        self.add_message("assistant", f"\u274c {error}")

    def clear_chat(self):
        """Clear the chat history."""

        self.chat_display.clear()

        self.conversation = []

        self.show_welcome()

    def eventFilter(self, obj, event):

        if obj == self.input_field and event.type() == event.KeyPress:

            if event.key() == Qt.Key_Return and not event.modifiers():

                self.on_send()

                return True

        return super().eventFilter(obj, event)
