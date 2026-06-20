# GeoPilot QGIS Plugin Makefile

PLUGIN_NAME = GeoPilot
PLUGIN_DIR = $(HOME)/AppData/Roaming/QGIS/QGIS3/profiles/default/python/plugins/$(PLUGIN_NAME)

.PHONY: install deploy clean zip

install:
	rm -rf $(PLUGIN_DIR)
	mkdir -p $(PLUGIN_DIR)
	cp -r * $(PLUGIN_DIR)
	echo 'Plugin installed. Restart QGIS to load.'

zip:
	rm -f $(PLUGIN_NAME).zip
	cd .. && zip -r $(PLUGIN_NAME).zip $(PLUGIN_NAME)/ -x '$(PLUGIN_NAME)/__pycache__/*' -x '$(PLUGIN_NAME)/.git/*'
	mv ../$(PLUGIN_NAME).zip .
	echo 'Created $(PLUGIN_NAME).zip'

deploy: zip
	echo 'Upload $(PLUGIN_NAME).zip to QGIS Plugin Manager or install from ZIP'

clean:
	rm -rf __pycache__ .pytest_cache
	find . -name '*.pyc' -delete
	find . -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null || true
