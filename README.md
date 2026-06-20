# GeoPilot - AI Geospatial Assistant for QGIS

[![QGIS](https://img.shields.io/badge/QGIS-3.30+-41B95C)](https://qgis.org)
[![Python](https://img.shields.io/badge/Python-3.9+-blue)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)
[![GitHub](https://img.shields.io/badge/GitHub-Repo-181717?logo=github)](https://github.com/xingguangYan/GeoPilot)

---

**GeoPilot** is an AI-powered geospatial analysis assistant plugin for QGIS that enables natural-language geospatial data processing, remote sensing analysis, and SCI paper figure generation. Chat with AI in plain language to analyze geographic data, compute spectral indices, classify land cover, detect changes, and generate publication-ready figures.

## Features

- **Natural Language Interface**: Describe your geospatial task in plain language
- **20+ AI Model Providers**: OpenAI, Anthropic Claude, Google Gemini, DeepSeek, Moonshot (Kimi), Alibaba Qwen, Zhipu GLM, Baidu ERNIE, iFlytek Spark, 01.AI Yi, Mistral, Groq, Ollama (local), and more
- **QGIS Processing**: Access 747+ native algorithms through natural language
- **Remote Sensing**: 28+ spectral indices, land cover classification, change detection
- **SCI Figures**: Publication-ready Figure 1-8 with journal-specific formatting
- **Journal Matching**: Smart SCI journal recommendation with acceptance prediction
- **Spatial Statistics**: Hotspot (Getis-Ord Gi*), Moran I, LISA clustering
- **Workflow Automation**: 6 pre-built analysis pipelines

---

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [AI Provider Configuration](#ai-provider-configuration)
- [Usage Examples](#usage-examples)
- [API Reference](#api-reference)
- [Project Structure](#project-structure)
- [Development](#development)
- [FAQ](#faq)
- [License](#license)

---

## Installation

### Prerequisites

- QGIS 3.30 or higher
- Python 3.9+ (bundled with QGIS)
- Internet connection for API access

### Method 1: QGIS Plugin Manager (Recommended)

Once approved on the QGIS Plugin Repository:
```
1. Open QGIS
2. Go to Plugins > Manage and Install Plugins
3. Search for 'GeoPilot'
4. Click Install
```

### Method 2: Install from ZIP

```bash
# Download the latest GeoPilot.zip from GitHub Releases
# Then in QGIS:
1. Plugins > Manage and Install Plugins
2. Click 'Install from ZIP'
3. Select the downloaded GeoPilot.zip
```

### Method 3: Manual Installation (Development)

```bash
# Clone the repository
git clone https://github.com/xingguangYan/GeoPilot.git

# Create plugin directory in QGIS profile
mkdir -p "%APPDATA%/QGIS/QGIS3/profiles/default/python/plugins/GeoPilot"

# Copy files
xcopy /E /I GeoPilot "%APPDATA%/QGIS/QGIS3/profiles/default/python/plugins/GeoPilot/"

# Or use Makefile (if you have make)
make install

# Restart QGIS
```

---

## Quick Start

1. **Launch GeoPilot**: Click the GeoPilot icon in the toolbar, or go to `Plugins > GeoPilot`

2. **Configure AI Provider**:
   - Select your preferred AI model from the dropdown (OpenAI, DeepSeek, Moonshot, etc.)
   - Enter your API key
   - Select or type the model name

3. **Chat with GeoPilot**:
   - Type your geospatial task in natural language
   - GeoPilot will generate and explain the analysis
   - Python code blocks are automatically detected and executed

### Example Queries

| Category | Example Prompt |
|----------|---------------|
| Basic GIS | "Buffer the roads layer by 100 meters" |
| Remote Sensing | "Calculate NDVI from the current Landsat layer" |
| Classification | "Classify land cover using random forest with 5 classes" |
| Change Detection | "Detect urban expansion between 2015 and 2020" |
| Spatial Analysis | "Find hotspots of deforestation in the forest layer" |
| SCI Figure | "Generate a study area map for my paper" |
| Journal Match | "Recommend journals for my remote sensing paper" |
| Full Workflow | "Analyze urban expansion in Wuhan from 2010 to 2025" |

---

## AI Provider Configuration

GeoPilot supports 20+ AI model providers. Below is the complete configuration guide.

### OpenAI-Compatible Providers

Most providers use the OpenAI-compatible API format. Configure them with:
- **API Key**: Set via environment variable or enter in the dialog
- **Base URL**: The API endpoint (defaults shown below)
- **Model**: Select or type the model name

| Provider | Display Name | Env Variable | Default Base URL | Models |
|----------|-------------|--------------|-----------------|--------|
| openai | OpenAI | `OPENAI_API_KEY` | https://api.openai.com/v1 | gpt-4o, gpt-4o-mini, gpt-4-turbo, o1-mini, o1-preview |
| deepseek | DeepSeek | `DEEPSEEK_API_KEY` | https://api.deepseek.com/v1 | deepseek-chat, deepseek-reasoner, deepseek-v3, deepseek-r1 |
| moonshot | Moonshot / Kimi | `MOONSHOT_API_KEY` | https://api.moonshot.cn/v1 | moonshot-v1-8k, moonshot-v1-32k, moonshot-v1-128k |
| qwen | Alibaba Qwen / Tongyi | `QWEN_API_KEY` | https://dashscope.aliyuncs.com/compatible-mode/v1 | qwen-max, qwen-plus, qwen-turbo, qwen2.5-72b-instruct |
| zhipu | Zhipu AI / GLM | `ZHIPU_API_KEY` | https://open.bigmodel.cn/api/paas/v4 | glm-4-plus, glm-4, glm-4-flash, glm-4-air |
| yi | 01.AI Yi | `YI_API_KEY` | https://api.01.ai/v1 | yi-lightning, yi-medium, yi-large, yi-vision |
| mistral | Mistral AI | `MISTRAL_API_KEY` | https://api.mistral.ai/v1 | mistral-large-latest, mistral-small-latest, open-mistral-nemo |
| cohere | Cohere | `COHERE_API_KEY` | https://api.cohere.ai/v1 | command-r-plus, command-r, command-nightly |
| perplexity | Perplexity | `PERPLEXITY_API_KEY` | https://api.perplexity.ai | sonar-pro, sonar, sonar-reasoning |
| xai | xAI Grok | `XAI_API_KEY` | https://api.x.ai/v1 | grok-beta, grok-2, grok-2-vision |
| together | Together AI | `TOGETHER_API_KEY` | https://api.together.xyz/v1 | meta-llama-3.1-405b, mistralai/mixtral-8x22b |
| fireworks | Fireworks AI | `FIREWORKS_API_KEY` | https://api.fireworks.ai/inference/v1 | llama-v3p1-405b, qwen2p5-72b |
| groq | Groq | `GROQ_API_KEY` | https://api.groq.com/openai/v1 | llama3-70b-8192, mixtral-8x7b-32768, gemma2-9b-it |

### Native API Providers

These providers have unique API formats and require specific configuration:

#### Anthropic Claude
```bash
# Set environment variable
set ANTHROPIC_API_KEY=sk-ant-...
# Or enter directly in the GeoPilot dialog
```
- Models: claude-3-5-sonnet-20241022, claude-3-5-haiku-20241022, claude-3-opus-20240229
- API: https://api.anthropic.com/v1

#### Google Gemini
```bash
set GOOGLE_API_KEY=AIza...
```
- Models: gemini-1.5-pro, gemini-1.5-flash, gemini-1.5-flash-8b, gemini-2.0-flash-exp
- API: https://generativelanguage.googleapis.com/v1beta

#### Baidu ERNIE (Wenxin)
```bash
set BAIDU_API_KEY=your_api_key
set BAIDU_SECRET_KEY=your_secret_key
```
- Models: ernie-4.0-8k, ernie-3.5-8k, ernie-speed, ernie-lite
- Auth: OAuth 2.0 client_credentials flow

#### iFlytek Spark (Xunfei)
```bash
set SPARK_APP_ID=your_app_id
set SPARK_API_KEY=your_api_key
set SPARK_API_SECRET=your_api_secret
```
- Models: 4.0Ultra, 3.5, 3.0
- API: https://spark-api-open.xf-yun.com/v1

#### Ollama (Local)
```bash
# No API key needed. Just run Ollama locally:
ollama pull llama3.1
ollama serve
```
- Models: llama3.1, llama3, mistral, qwen2.5, deepseek-r1, codellama, gemma2, mixtral
- API: http://localhost:11434 (configurable)

### Custom OpenAI-Compatible Endpoint

You can use any OpenAI-compatible API by:
1. Selecting any OpenAI-compatible provider from the list
2. Setting the **Base URL** to your custom endpoint
3. Entering the corresponding API key

This works with self-hosted models (vLLM, TGI, SGLang), Azure OpenAI, and any proxy service.

---

## Usage Examples

### Example 1: Basic GIS Analysis

```python
# In the GeoPilot chat dialog, type:
"Create a 500-meter buffer around all roads and clip it with the study area boundary"

# GeoPilot will execute:
import processing
result = processing.run('native:buffer', {
    'INPUT': 'roads.shp',
    'DISTANCE': 500,
    'DISSOLVE': True,
    'OUTPUT': 'roads_buffer.shp'
})
result2 = processing.run('native:clip', {
    'INPUT': 'roads_buffer.shp',
    'OVERLAY': 'study_area.shp',
    'OUTPUT': 'roads_buffer_clipped.shp'
})
```

### Example 2: Remote Sensing Indices

```python
"Compute NDVI, NDWI, and NDBI from Landsat imagery and stack them"

from geoai_remote_sensing import RemoteSensing
import numpy as np

rs = RemoteSensing()
bands = {'B': blue, 'G': green, 'R': red, 'N': nir, 'S1': swir1}
ndvi = rs.compute_index(bands, 'NDVI')
ndwi = rs.compute_index(bands, 'MNDWI')
ndbi = rs.compute_index(bands, 'NDBI')
stack = np.stack([ndvi, ndwi, ndbi], axis=0)
```

### Example 3: Land Cover Classification

```python
"Classify land cover into 5 types using Random Forest"

from geoai_remote_sensing import RemoteSensing
rs = RemoteSensing()
metrics = rs.train(X_train, y_train, algorithm='rf',
    n_estimators=200, max_depth=15)
print(f'OA={metrics["accuracy"]:.3f}, Kappa={metrics["kappa"]:.3f}')
classified = rs.classify_raster(image_data, 'rf')
```

### Example 4: SCI Figure Generation

```python
"Generate a 4-panel land cover figure for my paper"

from geoai_sci_figure import SCIFigures
sf = SCIFigures(journal='Remote_Sensing')
sf.figure2_land_cover(
    lc_maps=[lc_2010, lc_2015, lc_2020, lc_2025],
    time_labels=['2010', '2015', '2020', '2025'],
    class_names=['Forest', 'Cropland', 'Built-up', 'Water', 'Bareland']
)
```

### Example 5: Journal Recommendation

```python
"Recommend SCI journals for my urban expansion paper"

from geoai_paper_agent import PaperSubmissionAgent
agent = PaperSubmissionAgent()
recs = agent.recommend(topic='urban expansion', target_if=5.0)
for tier, journals in recs.items():
    for j in journals:
        print(f'[{tier}] {j["name"]} (IF={j["if"]})')
```

---

## API Reference

### Scripts Module

| Module | Description | Key Classes |
|--------|-------------|-------------|
| `geoai_data_manager` | Geospatial data management | `DataManager` |
| `geoai_vector_analysis` | Vector spatial analysis | `VectorAnalysis` |
| `geoai_raster_analysis` | Raster/terrain analysis | `RasterAnalysis` |
| `geoai_remote_sensing` | Spectral indices, classification, change detection | `RemoteSensing` |
| `geoai_sci_figure` | SCI paper figure generation | `SCIFigures` |
| `geoai_paper_agent` | Journal recommendation, cover letter | `PaperSubmissionAgent` |
| `geoai_pipeline` | 6 pre-built analysis workflows | `GeoAIPipeline` |
| `geoai_report` | Research report generation | `ResearchReport` |
| `geoai_qgis_bootstrap` | QGIS Python bootstrap | `init_qgis()` |
| `geoai_gee_bridge` | Google Earth Engine integration | `init_ee()` |
| `geoai_env_setup` | Environment detection | `generate_env_report()` |

### Providers Module

| Function | Description |
|----------|-------------|
| `get_provider(name)` | Get a provider instance by name |
| `list_providers()` | List all registered providers with metadata |
| `register_provider(name, cls)` | Register a custom provider |

---

## Project Structure

```
GeoPilot/
+-- __init__.py              # QGIS plugin entry: classFactory()
+-- metadata.txt             # QGIS Plugin Manager metadata
+-- geopilot.py               # Main plugin class (menu, toolbar)
+-- geopilot_dialog.py        # Chat dialog UI
+-- providers/               # AI model provider system (20+ models)
|   +-- __init__.py          # Provider registry
|   +-- base.py              # Abstract base class
|   +-- openai_compat.py     # OpenAI + 13 compatible providers
|   +-- anthropic_provider.py # Anthropic Claude
|   +-- google_provider.py   # Google Gemini
|   +-- baidu_provider.py    # Baidu ERNIE
|   +-- spark_provider.py    # iFlytek Spark
|   +-- ollama_provider.py   # Local Ollama
+-- scripts/                 # GeoAI analysis engine (13 modules)
|   +-- geoai_data_manager.py
|   +-- geoai_vector_analysis.py
|   +-- geoai_raster_analysis.py
|   +-- geoai_remote_sensing.py
|   +-- geoai_sci_figure.py
|   +-- geoai_paper_agent.py
|   +-- geoai_pipeline.py
|   +-- geoai_report.py
|   +-- geoai_qgis_bootstrap.py
|   +-- geoai_gee_bridge.py
|   +-- geoai_env_setup.py
|   +-- geoai.py (CLI)
+-- icons/                   # Plugin icons
|   +-- icon.svg
|   +-- icon.png
+-- Makefile                 # Build automation
+-- README.md                # This file
+-- LICENSE                  # MIT license
+-- .gitignore
```

---

## Development

### Build and Install

```bash
make install    # Install plugin to QGIS profile
make zip        # Create distributable ZIP
make clean      # Remove cache files
```

### Adding a New AI Provider

1. Create a new file in `providers/` (or add to `openai_compat.py` if OpenAI-compatible)
2. Implement the `BaseProvider` interface with a `chat()` method
3. Register it in `providers/__init__.py` using `register_provider()`

```python
from .base import BaseProvider, register_provider

class MyProvider(BaseProvider):
    ENV_KEY = "MY_API_KEY"
    DEFAULT_URL = "https://api.myprovider.com/v1"
    def chat(self, messages, system_prompt=None, temperature=0.7, max_tokens=4096):
        # Implement your API call here
        pass

register_provider('myprovider', MyProvider,
    display_name='My Provider',
    models=['model-1', 'model-2'])
```

---

## FAQ

### Q: Do I need an internet connection?
A: Yes, for cloud-based AI providers. For offline use, set up Ollama locally.

### Q: Can I use GeoPilot without an API key?
A: Yes, use the Ollama provider with local models. No API key required.

### Q: Which Chinese AI providers are supported?
A: DeepSeek, Moonshot (Kimi), Alibaba Qwen (Tongyi), Zhipu GLM, Baidu ERNIE (Wenxin), iFlytek Spark (Xunfei), and 01.AI Yi.

### Q: How do I get an API key?

| Provider | Sign Up |
|----------|---------|
| OpenAI | https://platform.openai.com/api-keys |
| DeepSeek | https://platform.deepseek.com/api_keys |
| Moonshot | https://platform.moonshot.cn/console/api-keys |
| Qwen | https://bailian.console.aliyun.com/ |
| Zhipu | https://open.bigmodel.cn/usercenter/apikeys |
| Baidu | https://console.bce.baidu.com/qianfan/ |
| Spark | https://www.xfyun.cn/service/spark |
| Yi | https://platform.01.ai/api-keys |
| Anthropic | https://console.anthropic.com/ |
| Google | https://aistudio.google.com/apikey |

### Q: The plugin doesn't appear after installation?
A: Make sure you've restarted QGIS. Check if the plugin is enabled in Plugins > Manage and Install Plugins > Installed tab.

### Q: How do I uninstall?
A: Go to Plugins > Manage and Install Plugins > Installed, select GeoPilot, and click "Uninstall".

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Citation

If you use GeoPilot in your research, please cite:

```bibtex
@software{geopilot2026,
  author = {GeoPilot Team},
  title = {GeoPilot: AI-Powered Geospatial Analysis Assistant for QGIS},
  year = {2026},
  url = {https://github.com/xingguangYan/GeoPilot}
}
```
