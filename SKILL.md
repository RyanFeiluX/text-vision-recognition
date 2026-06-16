---
name: text-vision-recognition
description: 基于 Qwen VL（通义千问视觉模型）将图片/PDF转换为结构化Markdown。支持单张图片识别、PDF逐页渲染识别、批量目录处理。3个pip依赖，无需系统包（无需poppler-utils）。
version: 1.0.0
author: RyanFeiluX
license: MIT
metadata:
  hermes:
    tags: [pdf, ocr, qwen, vision, document, markdown, recognition]
    related_skills: [image-doc-reconstruction]
---

# 文本视觉识别 (text-vision-recognition)

## 概述

基于 **Qwen VL**（阿里云通义千问视觉语言模型）的图片/PDF文字提取工具。

### 核心能力

| 功能 | 说明 |
|:----|:-----|
| **单张图片识别** | JPG/PNG/BMP 等常见图片格式，直接调用 Qwen VL 进行视觉理解 |
| **PDF 文档识别** | PyMuPDF 渲染为图片后逐页识别，无需 poppler-utils |
| **批量目录处理** | 自动扫描目录中所有图片和PDF，批量输出Markdown |
| **自动缩放** | 超过2048像素的图片自动缩放，节省API流量 |
| **并行识别** | 多页PDF自动并行识别（默认4线程） |
| **自定义提示词** | 可通过 `--prompt` 针对特定场景定制识别要求 |
| **硬盘/设备标签专用** | 默认提示词包含设备标签识别优化 |

### 与百度OCR版的区别

| 维度 | Qwen VL 版（本技能） | 百度云OCR版 (image-doc-reconstruction) |
|:----|:----|:----|
| **依赖** | 3个pip包，无系统依赖 | 3个pip包，无系统依赖 |
| **识别原理** | 大模型视觉理解（上下文感知） | 传统OCR引擎（字符识别） |
| **强项** | 自然场景、复杂排版、设备标签、手写 | 小字体密集文档、表格、API免费额度 |
| **弱项** | 大段纯文字性价比不如OCR | 图片模糊/倾斜时效果差 |
| **费用** | 按Qwen VL API计费（约0.003元/张） | 百度OCR免费500次/天 |

## 前置准备

### 1. 获取 Qwen VL API Key

在 [阿里云百炼平台](https://bailian.console.aliyun.com/) 创建API Key。

### 2. 配置环境变量

```bash
# 方式一：Qwen专用变量（推荐）
export QWEN_API_KEY="your_dashscope_api_key"

# 方式二：使用已有的 DASHSCOPE_API_KEY（如果已有）
# 脚本会自动读取 DASHSCOPE_API_KEY 作为备选
```

如果使用 Hermes，添加到 `~/.hermes/.env`：

```bash
echo 'QWEN_API_KEY="your_dashscope_api_key"' >> ~/.hermes/.env
```

### 3. 安装依赖

仅需3个Python包：

```bash
pip install PyMuPDF Pillow openai
```

> **无需** poppler-utils、无需 PaddlePaddle、无需任何系统包！

### 4. 模型选择

| 模型 | 适用场景 | 费用 |
|:----|:---------|:----|
| `qwen-vl-plus`（默认） | 一般文档、清晰图片 | 性价比高 |
| `qwen-vl-max` | 复杂排版、低质量图片、设备标签 | 更强但更贵 |

## 使用方式

### 基本用法

```bash
# 单张图片（如硬盘照片、合同扫描件）
python scripts/qwen_ocr.py -i 硬盘照片.jpg -o 识别结果.md

# PDF 文档
python scripts/qwen_ocr.py -i 扫描件.pdf -o 输出文档.md

# 批量处理目录
python scripts/qwen_ocr.py -i ./照片目录/ -o ./输出目录/
```

### 通过便捷命令（推荐，安装后可用）

```bash
pdf2md-qwen -i 文档.pdf -o 输出.md
```

### 高级参数

```bash
# 使用更强模型
pdf2md-qwen -i 模糊扫描件.pdf -o 结果.md --model qwen-vl-max

# 自定义提示词
pdf2md-qwen -i 标签.jpg -o 信息.md --prompt "提取标签上的所有文字，包括品牌、型号、序列号"

# 提高PDF渲染清晰度
pdf2md-qwen -i 小字文档.pdf -o 结果.md --dpi 300

# 串行识别（节省API配额）
pdf2md-qwen -i 100页文档.pdf -o 结果.md --no-parallel
```

### 列出可用模型

```bash
pdf2md-qwen --list-models
```

## 处理流程

```
输入文件（图片/PDF/目录）
    ↓
PDF检测 ──是──→ PyMuPDF 渲染为图片（指定DPI）
              ↓
            （非PDF，直接使用原图）
    ↓
自动缩放（最长边≤2048px）
    ↓
Base64 编码
    ↓
调用 Qwen VL API（可并行）
    ↓
返回结构化 Markdown
    ↓
输出 .md 文件 ✓
```

## 应用场景

### 📸 现场拍照识别
- 设备铭牌/标签（硬盘、NVR、路由器等）
- 合同/文件拍照后提取文字
- 白板/黑板文字记录

### 📄 扫描件数字化
- 扫描版PDF转可编辑Markdown
- 无法复制文字的PDF提取
- 图片型合同/协议的文本化

### 📑 批量文档处理
- 发票/收据批量识别
- 历史档案数字化
- 设备巡检记录图片转文字

## 费用说明

Qwen VL API 按次计费（以阿里云百炼最新定价为准）：

- **qwen-vl-plus**: 约 0.003元/次（输入图片）
- **qwen-vl-max**: 约 0.008元/次

处理一本100页的文档约 0.3-0.8 元。

## 常见问题

### Q: 识别结果不准确怎么办？

A: 尝试——
1. 使用 `--model qwen-vl-max` 更强模型
2. 增加 DPI `--dpi 300`（PDF模式）
3. 确保源图片清晰、光线充足
4. 用 `--prompt` 指定具体场景（如"提取硬盘标签上的型号和序列号"）

### Q: 和百度OCR版 (image-doc-reconstruction) 怎么选？

A: 设备标签/铭牌、手写、复杂排版 → 用 Qwen VL 版；纯文字密集文档、表格 → 用百度OCR版。两个互补，可以都装。

### Q: 费用会不会很贵？

A: 一般使用非常便宜。识别一张图片约 0.3分钱（qwen-vl-plus），100张也才3毛钱。

### Q: API并发限制？

A: 默认4线程并行。如果遇到限流，请用 `--no-parallel` 降为串行。

## 代码示例

```python
# Python 中直接调用
import os
from openai import OpenAI

client = OpenAI(
    api_key=os.environ["QWEN_API_KEY"],
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
)

# Base64 编码图片
import base64
from PIL import Image

def encode_image(image_path):
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

image_data = encode_image("硬盘照片.jpg")

response = client.chat.completions.create(
    model="qwen-vl-plus",
    messages=[{
        "role": "user",
        "content": [
            {"type": "text", "text": "请提取图片中的所有文字，输出为Markdown格式"},
            {"type": "image_url", "image_url": {
                "url": f"data:image/jpeg;base64,{image_data}"
            }}
        ]
    }],
    temperature=0.1
)

print(response.choices[0].message.content)
```
