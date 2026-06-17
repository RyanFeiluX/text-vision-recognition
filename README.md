# Text Vision Recognition — Qwen VL 版

> 基于阿里云通义千问（Qwen VL）视觉语言模型的图片/PDF文字提取工具。
> 3个pip依赖即可运行，无需任何系统包。

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/)
[![Hermes Skill](https://img.shields.io/badge/Hermes-Skill-8A2BE2)](https://hermes-agent.nousresearch.com/)

## 📸 它能做什么

| 场景 | 说明 |
|:----|:------|
| **拍设备标签** | 硬盘、NVR、路由器等铭牌 → 提取型号/序列号/规格 |
| **拍合同/文件** | 拍照后提取文字，输出结构化Markdown |
| **扫描件数字化** | 扫描版PDF → 可编辑Markdown |
| **批量文档处理** | 整个目录的图片/PDF一键处理 |

## ✨ 亮点

- **轻量** — 仅需 `pip install PyMuPDF Pillow openai`，3个依赖
- **无系统包** — 无需 poppler-utils、无需 PaddlePaddle、无需 sudo
- **大模型理解** — Qwen VL 上下文感知，不是简单OCR，能理解文档结构
- **支持图片+PDF** — 单张图片或PDF文档均可直接处理
- **批量处理** — 指定目录自动扫描所有支持的格式
- **设备标签优化** — 默认提示词针对设备铭牌/标签场景优化

## 🚀 快速开始

### 一分钟安装

```bash
pip install PyMuPDF Pillow openai
git clone https://github.com/RyanFeiluX/text-vision-recognition.git
cd text-vision-recognition
echo 'export QWEN_API_KEY="your_api_key_here"' >> ~/.bashrc
source ~/.bashrc
```

或者一键脚本：

```bash
curl -fsSL https://raw.githubusercontent.com/RyanFeiluX/text-vision-recognition/main/install.sh | bash
```

### 配置 API Key

获取方式：[阿里云百炼控制台](https://bailian.console.aliyun.com/) → API-KEY管理 → 创建API-KEY

```bash
export QWEN_API_KEY="sk-x...x
```

### 使用

```bash
# 识别一张硬盘照片
python scripts/qwen_ocr.py -i 硬盘照片.jpg -o 信息.md

# 转换PDF文档
python scripts/qwen_ocr.py -i 合同扫描件.pdf -o 合同.md

# 批量处理
python scripts/qwen_ocr.py -i ./图片/ -o ./输出/

# 安装快捷命令后
pdf2md-qwen -i 文档.pdf -o 输出.md
```

## 📦 安装为 Hermes 技能

如果使用 [Hermes Agent](https://hermes-agent.nousresearch.com/)，可以通过以下方式安装为技能：

### 方式一：GitHub tap 安装（推荐）

```bash
hermes skills tap add RyanFeiluX/text-vision-recognition
hermes skills install text-vision-recognition
```

### 方式二：直接 URL 安装

```bash
hermes skills install https://raw.githubusercontent.com/RyanFeiluX/text-vision-recognition/main/skills/text-vision-recognition/SKILL.md
```

### 方式三：手动安装

```bash
cp -r skills/text-vision-recognition ~/.hermes/skills/productivity/
pip install -r requirements.txt
```

### 方式四：一键脚本（自动检测 Hermes 环境）

```bash
curl -fsSL https://raw.githubusercontent.com/RyanFeiluX/text-vision-recognition/main/skills/text-vision-recognition/install.sh | bash
```

## 🔑 配置 API Key

在 `~/.hermes/.env` 中添加：

```ini
QWEN_API_KEY=your_api_key_here
```

## 🔧 高级用法

```bash
# 使用更强模型（复杂排版/模糊图片）
pdf2md-qwen -i 文档.pdf -o 结果.md --model qwen-vl-max

# 自定义提示词
pdf2md-qwen -i 标签.jpg -o 信息.md \
  --prompt "提取标签上的所有文字，包括品牌、型号、序列号"

# 提高PDF渲染清晰度
pdf2md-qwen -i 小字文档.pdf -o 结果.md --dpi 300

# 串行识别（节省API配额）
pdf2md-qwen -i 多页文档.pdf -o 结果.md --no-parallel
```

## 🔄 与百度OCR版对比

| | Qwen VL 版（本仓库） | 百度云OCR版 |
|:----|:----|:----|
| **原理** | 大模型视觉理解 | 传统OCR引擎 |
| **依赖** | 3个pip包 | 3个pip包 |
| **强项** | 设备标签、手写、复杂排版 | 小字体密集文档、表格 |
| **费用** | ~0.003元/张 | 免费500次/天 |
| **仓库** | 当前仓库 | [image-doc-reconstruction](https://github.com/RyanFeiluX/image-doc-reconstruction) |

两个工具互补，可以同时安装。**场景建议**：
- 拍摄的设备标签/铭牌 → **Qwen VL 版**
- 密集文字扫描件/合同 → **百度OCR版**
- 两者都装，看效果选

## 📁 项目结构

```
text-vision-recognition/
├── skills/
│   └── text-vision-recognition/    # Hermes 技能包
│       ├── SKILL.md                # 技能描述
│       ├── scripts/
│       │   ├── qwen_ocr.py         # 核心引擎（PDF + 图片处理）
│       │   └── pdf2md-qwen         # CLI 快捷命令
│       ├── references/
│       │   └── configuration.md    # API Key 配置指南
│       ├── assets/
│       │   └── templates/
│       └── install.sh              # 一键安装脚本
├── README.md             # 本文件
├── requirements.txt      # Python 依赖
└── .gitignore

## 🔑 环境变量

| 变量 | 必需 | 说明 |
|:----|:----|:------|
| `QWEN_API_KEY` | 是（二选一） | 阿里云百炼 API Key |
| `DASHSCOPE_API_KEY` | 是（二选一） | 备选变量名，脚本自动读取 |
| `QWEN_API_BASE` | 否 | API 基础地址（默认: dashscope.aliyuncs.com） |

## 📄 许可

MIT License
