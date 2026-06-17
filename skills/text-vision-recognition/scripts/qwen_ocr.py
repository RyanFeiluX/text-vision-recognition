#!/usr/bin/env python3
"""
Qwen VL 视觉识别引擎
将图片/PDF转换为结构化Markdown
使用阿里云通义千问 VL 模型进行视觉理解

无需 sudo 安装任何系统包，3个 pip 依赖即可运行：
  pip install PyMuPDF Pillow openai

使用方法：
  # 单张图片
  python qwen_ocr.py -i 照片.jpg -o 输出.md

  # PDF 文档
  python qwen_ocr.py -i 文档.pdf -o 输出.md

  # 批量处理目录
  python qwen_ocr.py -i 图片目录/ -o 输出目录/
"""

import os
import sys
import argparse
import base64
import logging
import time
import re
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Optional, Tuple

# ── 依赖检查 ──────────────────────────────────
try:
    from PIL import Image
    import fitz  # PyMuPDF
except ImportError:
    print("❌ 缺少依赖：PyMuPDF 或 Pillow")
    print("   请运行：pip install PyMuPDF Pillow")
    sys.exit(1)

try:
    from openai import OpenAI
except ImportError:
    print("❌ 缺少依赖：openai")
    print("   请运行：pip install openai")
    sys.exit(1)

# ── 日志 ──────────────────────────────────────
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════
#  配置
# ══════════════════════════════════════════════

DEFAULT_MODEL = "qwen-vl-plus"   # 性价比首选
# DEFAULT_MODEL = "qwen-vl-max"  # 更强但更贵

QWEN_API_BASE = os.environ.get(
    "QWEN_API_BASE",
    "https://dashscope.aliyuncs.com/compatible-mode/v1"
)
QWEN_API_KEY = os.environ.get("QWEN_API_KEY") or os.environ.get("DASHSCOPE_API_KEY")

MAX_WORKERS = 4       # 并行处理线程数
MAX_PIXELS = 2048     # 图片最长边缩放


# ══════════════════════════════════════════════
#  工具函数
# ══════════════════════════════════════════════

def _get_env(name: str) -> str:
    """从环境变量读取配置，带友好错误"""
    val = os.environ.get(name)
    if val:
        return val
    raise ValueError(
        f"❌ 未配置 {name}\n"
        f"   请将其添加到 ~/.hermes/.env 或 export 到当前环境\n"
        f"   格式：{name}=your_api_key_here"
    )


def encode_image(image: Image.Image, fmt: str = "JPEG", max_side: int = MAX_PIXELS) -> str:
    """将PIL图像缩放后编码为base64"""
    # 缩放至合理尺寸
    w, h = image.size
    if max(w, h) > max_side:
        ratio = max_side / max(w, h)
        image = image.resize((int(w * ratio), int(h * ratio)), Image.LANCZOS)

    buf = image.tobytes("jpeg", "RGB")
    return base64.b64encode(buf).decode("utf-8")


def encode_image_from_path(path: str, max_side: int = MAX_PIXELS) -> Tuple[str, str]:
    """读取图片文件，返回 (base64字符串, mime类型)"""
    img = Image.open(path)
    fmt = "JPEG"
    return encode_image(img, fmt, max_side), f"image/{fmt.lower()}"


def pdf_to_images(pdf_path: str, dpi: int = 200) -> List[Image.Image]:
    """用 PyMuPDF 将 PDF 每页渲染为 PIL 图像（无需 poppler-utils）"""
    doc = fitz.open(pdf_path)
    images = []
    for page_num in range(len(doc)):
        page = doc[page_num]
        # 用矩阵控制渲染分辨率
        mat = fitz.Matrix(dpi / 72, dpi / 72)
        pix = page.get_pixmap(matrix=mat)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        images.append(img)
        logger.info(f"  PDF 第 {page_num + 1}/{len(doc)} 页 → 图片 ({pix.width}×{pix.height})")
    doc.close()
    return images


# ══════════════════════════════════════════════
#  Qwen VL 调用
# ══════════════════════════════════════════════

SYSTEM_PROMPT = """你是一个专业的文档识别助手。请仔细阅读图片中的所有文字，并完成以下任务：

1. **逐字提取**所有可见文字，不要遗漏
2. **保留原文排版结构**：识别标题层级（用#标记）、段落、列表、表格
3. **输出为Markdown格式**
4. 如果图片是**硬盘/设备标签**，请提取所有可见信息：品牌、型号、序列号、容量、规格等
5. 不要添加图片中没有的信息，不要编造内容"""


def ocr_image_with_qwen(
    client: OpenAI,
    image_data: str,
    image_type: str = "image/png",
    model: str = DEFAULT_MODEL,
    custom_prompt: Optional[str] = None,
) -> str:
    """调用 Qwen VL 识别一张图片"""
    prompt = custom_prompt or SYSTEM_PROMPT

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{image_type};base64,{image_data}"
                            }
                        }
                    ]
                }
            ],
            temperature=0.1,
            max_tokens=2048,
        )
        return response.choices[0].message.content.strip()

    except Exception as e:
        logger.error(f"Qwen VL 调用失败: {e}")
        return f"[识别失败: {e}]"


# ══════════════════════════════════════════════
#  主处理流程
# ══════════════════════════════════════════════

def process_single_image(
    client: OpenAI,
    image_path: str,
    model: str = DEFAULT_MODEL,
    prompt: Optional[str] = None,
) -> str:
    """处理单张图片"""
    logger.info(f"识别图片: {image_path}")
    img_data, img_type = encode_image_from_path(image_path)
    return ocr_image_with_qwen(client, img_data, img_type, model, prompt)


def process_pdf(
    client: OpenAI,
    pdf_path: str,
    model: str = DEFAULT_MODEL,
    dpi: int = 200,
    prompt: Optional[str] = None,
    parallel: bool = True,
) -> str:
    """处理 PDF 文档：逐页渲染并识别"""
    logger.info(f"渲染PDF: {pdf_path} (DPI={dpi})")
    images = pdf_to_images(pdf_path, dpi)

    if not images:
        return "[空文档]"

    results = [None] * len(images)

    if parallel and len(images) > 1:
        # 并行识别
        with ThreadPoolExecutor(max_workers=min(MAX_WORKERS, len(images))) as executor:
            futures = {}
            for i, img in enumerate(images):
                img_data = encode_image(img, "JPEG", MAX_PIXELS)
                future = executor.submit(
                    ocr_image_with_qwen, client, img_data, "image/jpeg", model, prompt
                )
                futures[future] = i

            for future in as_completed(futures):
                idx = futures[future]
                try:
                    results[idx] = future.result()
                except Exception as e:
                    results[idx] = f"[第{idx + 1}页识别失败: {e}]"
    else:
        # 串行识别
        for i, img in enumerate(images):
            logger.info(f"  识别第 {i + 1}/{len(images)} 页...")
            img_data = encode_image(img, "PNG", MAX_PIXELS)
            results[i] = ocr_image_with_qwen(client, img_data, "image/png", model, prompt)

    # 组装 Markdown
    md = f"# {Path(pdf_path).stem}\n\n"
    for i, text in enumerate(results):
        if i > 0:
            md += "\n\n---\n\n"
        md += text

    return md


def process_batch(
    client: OpenAI,
    input_dir: str,
    output_dir: str,
    model: str = DEFAULT_MODEL,
    dpi: int = 200,
    prompt: Optional[str] = None,
) -> List[str]:
    """批量处理目录中的所有图片/PDF"""
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # 收集所有支持的文件
    extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.pdf'}
    files = sorted([f for f in input_path.iterdir() if f.suffix.lower() in extensions])

    if not files:
        logger.warning(f"目录中没有支持的图片或PDF文件: {input_dir}")
        return []

    results = []
    for file_path in files:
        logger.info(f"处理: {file_path.name}")
        out_file = output_path / f"{file_path.stem}.md"

        if file_path.suffix.lower() == '.pdf':
            md = process_pdf(client, str(file_path), model, dpi, prompt, parallel=False)
        else:
            md = process_single_image(client, str(file_path), model, prompt)

        out_file.write_text(md, encoding='utf-8')
        results.append(str(out_file))
        logger.info(f"  → 已保存: {out_file}")

    return results


# ══════════════════════════════════════════════
#  主入口
# ══════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="Qwen VL 视觉识别 — 将图片/PDF转换为结构化Markdown",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 单张图片
  python qwen_ocr.py -i 硬盘照片.jpg -o 识别结果.md

  # PDF 文档
  python qwen_ocr.py -i 扫描件.pdf -o 输出.md

  # 指定 Qwen VL 模型
  python qwen_ocr.py -i 文档.pdf -o 输出.md --model qwen-vl-max

  # 批量处理目录
  python qwen_ocr.py -i ./图片目录/ -o ./输出目录/

  # 自定义提示词（用于特定场景）
  python qwen_ocr.py -i 标签.jpg -o 标签信息.md --prompt "提取标签上的所有文字"
        """
    )
    parser.add_argument("-i", "--input", required=True,
                        help="输入文件（图片/PDF）或目录（批量模式）")
    parser.add_argument("-o", "--output", default=None,
                        help="输出 .md 文件或目录（批量模式下默认与输入目录同名）")
    parser.add_argument("--model", default=DEFAULT_MODEL,
                        choices=["qwen-vl-plus", "qwen-vl-max"],
                        help=f"Qwen VL 模型（默认: {DEFAULT_MODEL}）")
    parser.add_argument("--dpi", type=int, default=200, choices=[150, 200, 250, 300],
                        help="PDF 渲染 DPI（默认: 200）")
    parser.add_argument("--prompt", default=None,
                        help="自定义识别提示词（覆盖默认）")
    parser.add_argument("--parallel", action="store_true", default=True,
                        help="并行识别多页（默认开启）")
    parser.add_argument("--no-parallel", action="store_false", dest="parallel",
                        help="串行识别（节省API配额）")
    parser.add_argument("--list-models", action="store_true",
                        help="列出推荐的 Qwen VL 模型")

    args = parser.parse_args()

    if args.list_models:
        print("推荐的 Qwen VL 模型：")
        print("  qwen-vl-plus  — 性价比首选，适合大部分文档识别")
        print("  qwen-vl-max   — 更强能力，适合复杂排版/低质量图片")
        print()
        print("更多模型请查阅：https://help.aliyun.com/zh/model-studio/")
        return

    # 检查 API Key
    if not QWEN_API_KEY:
        print("❌ 未配置 Qwen VL API Key")
        print("   请在 ~/.hermes/.env 中添加：")
        print("   QWEN_API_KEY=your_dashscope_api_key")
        print("   或：DASHSCOPE_API_KEY=your_dashscope_api_key")
        print("   获取地址：https://bailian.console.aliyun.com/")
        sys.exit(1)

    # 初始化客户端
    client = OpenAI(api_key=QWEN_API_KEY, base_url=QWEN_API_BASE)

    # 判断输入类型
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"❌ 输入不存在: {args.input}")
        sys.exit(1)

    start_time = time.time()

    if input_path.is_dir():
        # 批量模式
        output_dir = args.output or f"{args.input}_output"
        files = process_batch(client, str(input_path), output_dir, args.model, args.dpi, args.prompt)
        elapsed = time.time() - start_time
        print(f"\n✅ 批量处理完成！共 {len(files)} 个文件，耗时 {elapsed:.1f}秒")
        for f in files:
            print(f"   📄 {f}")

    elif input_path.suffix.lower() == '.pdf':
        # PDF 模式
        output_path = args.output or str(input_path.with_suffix('.md'))
        md = process_pdf(client, str(input_path), args.model, args.dpi, args.prompt, args.parallel)
        Path(output_path).write_text(md, encoding='utf-8')
        elapsed = time.time() - start_time
        print(f"\n✅ PDF 转换完成！耗时 {elapsed:.1f}秒")
        print(f"   📄 输入: {input_path}")
        print(f"   📄 输出: {output_path}")
        print(f"   📝 字符数: {len(md)}")

    else:
        # 单张图片模式
        output_path = args.output or str(input_path.with_suffix('.md'))
        text = process_single_image(client, str(input_path), args.model, args.prompt)
        Path(output_path).write_text(text, encoding='utf-8')
        elapsed = time.time() - start_time
        print(f"\n✅ 图片识别完成！耗时 {elapsed:.1f}秒")
        print(f"   📄 输入: {input_path}")
        print(f"   📄 输出: {output_path}")
        print(f"   📝 字符数: {len(text)}")


if __name__ == '__main__':
    main()
