# GeoPilot - AI Geospatial Assistant for QGIS

[![QGIS](https://img.shields.io/badge/QGIS-3.30+-41B95C)](https://qgis.org)
[![Python](https://img.shields.io/badge/Python-3.12+-blue)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)
[![GitHub](https://img.shields.io/badge/GitHub-Repo-181717?logo=github)](https://github.com/xingguangYan/GeoPilot)
[![Release](https://img.shields.io/github/v/release/xingguangYan/GeoPilot?color=green)](https://github.com/xingguangYan/GeoPilot/releases)
[![Downloads](https://img.shields.io/github/downloads/xingguangYan/GeoPilot/total?color=blue)](https://github.com/xingguangYan/GeoPilot/releases)

---

**GeoPilot** is an AI-powered geospatial analysis assistant plugin for QGIS that lets you control QGIS through natural language. Tell GeoPilot what you want to do in plain Chinese or English — it will automatically generate and execute QGIS Python code to process data, run analyses, and create publication-ready figures.

> 🔥 **Key Innovation**: Unlike other AI plugins that only chat, GeoPilot **actually executes code in QGIS**. Your maps, buffers, NDVI, and classifications happen in real-time — no copy-pasting required.

---

## ✨ Features

### 🎯 Core Capabilities
- **Natural Language → QGIS Operations**: Describe tasks in plain language, GeoPilot executes them automatically
- **Auto Code Execution**: AI-generated Python code runs directly in QGIS — buffers, clips, NDVI, classifications all happen live
- **18 AI Providers**: OpenAI, DeepSeek, Moonshot, Qwen, Zhipu, Yi, Mistral, Cohere, Perplexity, xAI Grok, Together AI, Fireworks AI, Groq, Anthropic Claude, Google Gemini, Ollama (Local), Baidu ERNIE, iFlytek Spark
- **Smart Context Awareness**: Auto-detects current layers, CRS, fields, and available algorithms to inform the AI

### 🗺️ Geospatial Analysis
| Category | Capabilities |
|----------|-------------|
| **Vector Analysis** | Buffer, Clip, Union, Intersect, Dissolve, Spatial Join, Merge, Reproject, Field Calculator |
| **Raster Analysis** | Slope, Aspect, Hillshade, Contour, Raster Calculator, Reclassify, Polygonize |
| **Remote Sensing** | 28+ spectral indices (NDVI, EVI, SAVI, NDWI, MNDWI, NBR, etc.), Land Cover Classification, Change Detection |
| **Spatial Statistics** | Hotspot Analysis (Getis-Ord Gi\*), Moran\'s I, LISA, Kernel Density, Voronoi |
| **Network Analysis** | Shortest Path, Service Area |
| **SCI Figures** | Study Area Map, Land Cover, Accuracy Assessment, Change Detection, Spatial Pattern, Graphical Abstract |

### 🌐 Multi-Language Support
- **Chinese & English** interface and AI responses
- All Chinese AI providers natively supported (DeepSeek, Moonshot, Qwen, Zhipu, Baidu, Spark, Yi)

---

## 📦 Installation

### Prerequisites
- **QGIS 3.30+** (tested on 3.44.2)
- Internet connection (for cloud AI providers)
- API key for your chosen AI provider (except Ollama which runs locally)

### Quick Install (From Release ZIP)
```bash
1. Download GeoPilot-v1.1.0.zip from GitHub Releases
2. Open QGIS → Plugins → Manage and Install Plugins
3. Click "Install from ZIP" → Select the downloaded file
4. Restart QGIS
5. Enable GeoPilot in Plugins → Installed tab
```

### Manual Install
```bash
# Clone
git clone https://github.com/xingguangYan/GeoPilot.git

# Copy to QGIS plugins directory (Windows)
xcopy /E /I GeoPilot "%APPDATA%/QGIS/QGIS3/profiles/default/python/plugins/GeoPilot/"
```

---

## 🚀 Quick Start

### 1. Launch GeoPilot
Click the GeoPilot icon 🌐 in the QGIS toolbar, or go to `Plugins → GeoPilot → GeoPilot Chat`.

### 2. Configure Your AI Provider
Click **Provider Settings** (⚙) to expand settings:

```yaml
Provider: DeepSeek       # Select your preferred AI
Model: deepseek-chat     # Select model version
API Key: sk-...          # Enter your API key
Base URL: (leave default) # Most providers have pre-configured endpoints
```

### 3. Start Working!
Just type what you want in natural language. GeoPilot will:
1. Understand your request
2. Generate QGIS Python code
3. **Execute it automatically** in QGIS
4. Show results in the chat

### 💬 Example Prompts

| Category | Example |
|----------|---------|
| **Buffer** | `对道路图层做100米缓冲区` / "Buffer the roads layer by 100 meters" |
| **Clip** | `用研究区边界裁剪所有图层` / "Clip all layers by the study area boundary" |
| **NDVI** | `计算当前影像的NDVI并显示` / "Calculate NDVI from the current image" |
| **Classification** | `用随机森林做5类土地利用分类` / "Run Random Forest classification with 5 classes" |
| **Change Detection** | `检测2015到2020的城市扩张` / "Detect urban expansion from 2015 to 2020" |
| **Hotspot** | `分析犯罪数据的热点区域` / "Find crime hotspots in the point layer" |
| **Export Figure** | `生成研究区示意图，包含比例尺指北针` / "Create a study area map with scale bar and north arrow" |
| **Batch** | `对每个矢量图层按字段融合` / "Dissolve each vector layer by its name field" |

---

## 🔧 AI Provider Configuration

### Getting API Keys

| Provider | Get API Key | Best For |
|----------|-------------|----------|
| **OpenAI** | [platform.openai.com](https://platform.openai.com/api-keys) | General purpose, best quality |
| **DeepSeek** | [platform.deepseek.com](https://platform.deepseek.com/api_keys) | Cost-effective, Chinese support |
| **Moonshot/Kimi** | [platform.moonshot.cn](https://platform.moonshot.cn/console/api-keys) | Chinese, long context |
| **Qwen (Tongyi)** | [bailian.console.aliyun.com](https://bailian.console.aliyun.com/) | Chinese, Alibaba ecosystem |
| **Zhipu GLM** | [open.bigmodel.cn](https://open.bigmodel.cn/usercenter/apikeys) | Chinese, code generation |
| **Yi (01.AI)** | [platform.01.ai](https://platform.01.ai/api-keys) | Chinese, fast responses |
| **Anthropic Claude** | [console.anthropic.com](https://console.anthropic.com/) | Long context, analysis |
| **Google Gemini** | [aistudio.google.com](https://aistudio.google.com/apikey) | Free tier available |
| **Ollama (Local)** | No key needed (local) | Offline use, free |

### Supported Models

| Provider | Models |
|----------|--------|
| OpenAI | gpt-4o, gpt-4o-mini, gpt-4-turbo, o1, o1-mini, o3-mini, gpt-4.1 |
| DeepSeek | deepseek-chat, deepseek-reasoner, deepseek-v3, deepseek-r1, deepseek-v4-pro, deepseek-v4-flash |
| Moonshot | moonshot-v1-8k, moonshot-v1-32k, moonshot-v1-128k, moonshot-v1-auto |
| Qwen | qwen-max, qwen-plus, qwen-turbo, qwen-long, qwen2.5-72b-instruct |
| Zhipu | glm-4-plus, glm-4, glm-4-flash, glm-4-air, glm-4v-plus |
| Yi | yi-lightning, yi-medium, yi-large, yi-vision, yi-large-turbo |
| Mistral | mistral-large-latest, mistral-small-latest, codestral-latest |
| Anthropic | claude-sonnet-4-20250514, claude-3-5-sonnet-20241022, claude-3-5-haiku |
| Google | gemini-2.5-pro-exp-03-25, gemini-2.0-flash, gemini-1.5-pro |
| Ollama | llama3.3, llama3.1, mistral, qwen2.5, deepseek-r1, phi4 |
| Baidu | ernie-4.0-8k, ernie-3.5-8k, ernie-speed, ernie-lite |
| Spark | 4.0Ultra, 4.0, 3.5, 3.0 |
| xAI Grok | grok-beta, grok-2, grok-2-vision, grok-3 |
| Perplexity | sonar-pro, sonar, sonar-reasoning |
| Groq | llama-3.3-70b-versatile, mixtral-8x7b, gemma2-9b-it |
| Together AI | meta-llama-3.3-70b, deepseek-ai/DeepSeek-R1 |
| Fireworks AI | llama-v3p3-70b, qwen2p5-72b, deepseek-r1 |
| Cohere | command-r-plus, command-r7-12-2024, command-a-03-2025 |

---

## 🎨 GUI Overview

GeoPilot features a modern dark-theme chat interface:

```
┌─────────────────────────────────────────────┐
│  GeoPilot - AI Geospatial Assistant  [? Help] │
├─────────────────────────────────────────────┤
│  ⚙ Provider Settings (collapsible)          │
│  ┌─────────────────────────────────────┐    │
│  │ Provider: [DeepSeek ▼] Model: [.. ▼]│    │
│  │ API Key: [••••••••••••••••]        │    │
│  │ Base URL: [______________]          │    │
│  │ System Prompt: [______________]     │    │
│  └─────────────────────────────────────┘    │
├─────────────────────────────────────────────┤
│  💬 Welcome to GeoPilot!                    │
│  🌐 Your AI Geospatial Assistant             │
│                                             │
│  1. ⚙ Click Provider Settings to configure  │
│  2. 📝 Type your task in natural language    │
│  3. 🤖 GeoPilot executes code automatically  │
├─────────────────────────────────────────────┤
│  [Describe your task here...        ] [▶ Send] │
└─────────────────────────────────────────────┘
```

### Help Panel
Click **? Help** to reveal quick-prompt buttons for common tasks:
- 🌎 Study Area Analysis
- 🌿 Vegetation Analysis (NDVI)
- 🏙️ Land Cover Classification
- 📊 Change Detection
- 🌍 Spatial Pattern Analysis
- 📄 Export Research Report

---

## 🏗️ Project Architecture

```
GeoPilot/
├── __init__.py              # Plugin entry point (classFactory)
├── geopilot.py               # Main plugin class (menu, toolbar)
├── geopilot_dialog.py        # Chat dialog + auto-execution engine
├── metadata.txt              # QGIS plugin metadata
├── README.md                 # This file
├── LICENSE                   # MIT License
├── Makefile                  # Build automation
│
├── providers/                # 🧠 AI Provider System (18 providers)
│   ├── __init__.py           # Provider registry (all 18 registered)
│   ├── base.py               # BaseProvider, register_provider()
│   ├── openai_compat.py      # OpenAI + 13 compatible providers
│   ├── anthropic_provider.py # Anthropic Claude
│   ├── google_provider.py    # Google Gemini
│   ├── baidu_provider.py     # Baidu ERNIE (OAuth)
│   ├── spark_provider.py     # iFlytek Spark
│   └── ollama_provider.py    # Local Ollama
│
├── scripts/                  # ⚙️ GeoAI Analysis Engine
│   ├── geoai_data_manager.py    # Data I/O (Shapefile, GeoJSON, GPKG, etc.)
│   ├── geoai_vector_analysis.py # Buffer, Clip, Union, Spatial Join
│   ├── geoai_raster_analysis.py # GDAL, SAGA, GRASS raster ops
│   ├── geoai_remote_sensing.py  # 28 spectral indices, 8 classifiers
│   ├── geoai_sci_figure.py      # Figure 1-8, Graphical Abstract, Poster
│   ├── geoai_paper_agent.py     # Journal recommendation, Cover Letter
│   ├── geoai_pipeline.py        # 6 pre-built analysis workflows
│   ├── geoai_report.py          # Research report generator
│   ├── geoai_qgis_bootstrap.py  # QGIS environment initialization
│   ├── geoai_gee_bridge.py      # Google Earth Engine integration
│   ├── geoai_env_setup.py       # Environment detection
│   └── geoai.py                 # CLI interface
│
└── icons/                    # 🎨 Plugin icons
    ├── icon.png
    └── icon.svg
```

---

## 🧠 How Auto-Execution Works

The core innovation of GeoPilot is the **code execution pipeline**:

```mermaid
flowchart LR
    A[User: "Buffer by 100m"] --> B[AI generates Python code]
    B --> C[Code extracted from response]
    C --> D[QGIS exec\(\) runs the code]
    D --> E[Layer created, results shown]
    D --> F[iface.messageBar feedback]
```

1. **Context Gathering**: `build_qgis_context()` collects all layer info, CRS, fields, and available algorithms
2. **AI Processing**: The LLM generates QGIS Python code based on context and user request
3. **Code Extraction**: `exec_qgis_code()` extracts ```python blocks from the AI response
4. **Execution**: Code runs directly in QGIS via `exec()` with full QGIS API access
5. **Feedback**: Results (new layers, processing output, errors) are displayed in the chat

---

## 🧪 Scripts API Reference

The analysis engine in `scripts/` provides programmatic access to all GeoPilot capabilities:

| Module | Purpose | Key Functions |
|--------|---------|--------------|
| `geoai_vector_analysis` | Vector GIS operations | buffer_layer(), clip_layers(), spatial_join() |
| `geoai_raster_analysis` | Raster processing | calculate_slope(), reclassify_raster(), contour() |
| `geoai_remote_sensing` | Remote sensing | calculate_ndvi(), classify_landcover(), detect_change() |
| `geoai_sci_figure` | SCI figures | create_study_area_map(), create_classification_figure() |
| `geoai_paper_agent` | Journal matching | recommend_journal(), generate_cover_letter() |
| `geoai_pipeline` | Workflows | run_forest_disturbance(), run_urban_expansion() |
| `geoai_report` | Reports | generate_research_report(), generate_thesis_outline() |
| `geoai_qgis_bootstrap` | QGIS init | init_qgis() |
| `geoai_gee_bridge` | GEE integration | init_ee(), gee_export() |

---

## 🛠️ Development

### Build & Package
```bash
make install    # Install to QGIS profile
make zip        # Create distributable ZIP
make clean      # Remove __pycache__
```

### Adding a New Provider
```python
from .base import BaseProvider, register_provider

class MyProvider(BaseProvider):
    ENV_KEY = "MY_API_KEY"
    DEFAULT_URL = "https://api.example.com/v1"
    
    def chat(self, messages, system_prompt=None, temperature=0.7, max_tokens=4096):
        # Implement API call
        return response_text

register_provider('myprovider', MyProvider,
    display_name='My Provider',
    models=['model-1', 'model-2'],
    env_key='MY_API_KEY',
    default_url='https://api.example.com/v1')
```

---

## ❓ FAQ

**Q: Does GeoPilot actually execute code in QGIS?**
A: Yes! Unlike chat-only plugins, GeoPilot runs AI-generated Python code directly in QGIS using `exec()`. Results appear as new layers, processed data, and visual feedback.

**Q: Do I need internet?**
A: For cloud AI providers, yes. For offline use, install Ollama locally with models like `llama3.1` or `qwen2.5`.

**Q: Which provider is best for geospatial analysis?**
A: DeepSeek, Qwen, and Claude generally produce the best QGIS Python code. OpenAI GPT-4o is also excellent.

**Q: Can I use it without an API key?**
A: Yes! Use the Ollama provider with locally installed models — completely free and offline.

**Q: How do I get API keys?**
A: See the [Getting API Keys](#getting-api-keys) table above. Most providers offer free credits for new users.

---

## 📄 License

MIT License — see [LICENSE](LICENSE).

## 📝 Citation

```bibtex
@software{geopilot2026,
  author = {GeoPilot Team},
  title = {GeoPilot: AI-Powered Geospatial Analysis Assistant for QGIS},
  year = {2026},
  url = {https://github.com/xingguangYan/GeoPilot}
}
```

---

⭐ **If you find GeoPilot useful, please star the repo!**
