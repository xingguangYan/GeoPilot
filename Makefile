# GeoPilot QGIS Plugin Makefile

PLUGIN_NAME = GeoPilot
VERSION = 1.3.8
# Default QGIS plugin profile location on Windows; override on Linux/Mac:
#   make install PLUGIN_DIR=~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/GeoPilot
PLUGIN_DIR ?= $(HOME)/AppData/Roaming/QGIS/QGIS3/profiles/default/python/plugins/$(PLUGIN_NAME)

.PHONY: install deploy clean zip lint

install: clean
	rm -rf "$(PLUGIN_DIR)"
	mkdir -p "$(PLUGIN_DIR)"
	cp -r __init__.py geopilot.py geopilot_dialog.py metadata.txt LICENSE README.md "$(PLUGIN_DIR)/"
	cp -r providers scripts icons "$(PLUGIN_DIR)/"
	@echo "Plugin installed to $(PLUGIN_DIR). Restart QGIS to load."

zip: clean
	rm -f $(PLUGIN_NAME)-v$(VERSION).zip
	cd .. && zip -r $(PLUGIN_NAME)/$(PLUGIN_NAME)-v$(VERSION).zip $(PLUGIN_NAME) \
		-x '$(PLUGIN_NAME)/.git/*' \
		-x '$(PLUGIN_NAME)/__pycache__/*' \
		-x '$(PLUGIN_NAME)/**/__pycache__/*' \
		-x '$(PLUGIN_NAME)/*.zip'
	@echo "Created $(PLUGIN_NAME)-v$(VERSION).zip"

deploy: zip
	@echo "Upload $(PLUGIN_NAME)-v$(VERSION).zip to QGIS Plugin Manager or GitHub releases."

lint:
	@python3 -m py_compile $$(find . -name '*.py') && echo "All Python files compile cleanly."

clean:
	rm -rf __pycache__ .pytest_cache .mypy_cache .ruff_cache build dist
	find . -name '*.pyc' -delete
	find . -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null || true
