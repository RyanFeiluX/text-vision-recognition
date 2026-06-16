#!/bin/bash
# text-vision-recognition 一键安装脚本
# Qwen VL 版图片/PDF 文字识别工具
# 使用方法: curl -fsSL https://raw.githubusercontent.com/RyanFeiluX/text-vision-recognition/main/install.sh | bash

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  text-vision-recognition 安装程序     ║${NC}"
echo -e "${BLUE}║  Qwen VL 视觉识别工具                  ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
echo ""

# ── 检测系统 ──────────────────────────────────
OS="$(uname -s)"
case "$OS" in
    Linux*)   OS_TYPE="linux";;
    Darwin*)  OS_TYPE="macos";;
    *)        OS_TYPE="unknown";;
esac
echo -e "${YELLOW}检测到系统: $OS ($OS_TYPE)${NC}"

# ── 检测 Python ───────────────────────────────
PYTHON=""
for cmd in python3 python; do
    if command -v "$cmd" &> /dev/null; then
        PY_VERSION=$("$cmd" --version 2>&1 | grep -oP '\d+\.\d+')
        PY_MAJOR=$(echo "$PY_VERSION" | cut -d. -f1)
        if [ "$PY_MAJOR" -ge 3 ]; then
            PYTHON="$cmd"
            echo -e "${GREEN}✓ 检测到 Python: $("$cmd" --version)${NC}"
            break
        fi
    fi
done

if [ -z "$PYTHON" ]; then
    echo -e "${RED}❌ 未找到 Python 3，请先安装 Python 3.8+${NC}"
    echo "   推荐: sudo apt install python3 python3-pip  # Ubuntu/Debian"
    echo "          brew install python3                  # macOS"
    exit 1
fi

# ── 目标路径 ──────────────────────────────────
if [ -n "$HERMES_HOME" ]; then
    INSTALL_DIR="$HERMES_HOME/skills/productivity/text-vision-recognition"
    echo -e "${BLUE}检测到 Hermes 环境 → 安装到技能目录${NC}"
elif [ -d "$HOME/.hermes/skills" ]; then
    INSTALL_DIR="$HOME/.hermes/skills/productivity/text-vision-recognition"
    echo -e "${BLUE}检测到 ~/.hermes → 安装到 Hermes 技能目录${NC}"
else
    INSTALL_DIR="$HOME/.local/share/text-vision-recognition"
    echo -e "${BLUE}未检测到 Hermes → 安装到用户目录${NC}"
fi

echo -e "  目标: ${YELLOW}$INSTALL_DIR${NC}"

# ── 下载或复制 ────────────────────────────────
if [ -d "$(dirname "$0")/scripts" ] && [ -f "$(dirname "$0")/SKILL.md" ]; then
    # 本地安装（git clone 之后运行）
    SRC_DIR="$(cd "$(dirname "$0")" && pwd)"
    echo -e "${GREEN}✓ 检测到本地源码: $SRC_DIR${NC}"
    echo -e "安装中..."
    mkdir -p "$INSTALL_DIR"
    cp -r "$SRC_DIR/scripts" "$SRC_DIR/SKILL.md" "$SRC_DIR/requirements.txt" "$SRC_DIR/references" "$SRC_DIR/assets" "$INSTALL_DIR/" 2>/dev/null || true
else
    # 远程安装（curl | bash）
    REPO="https://github.com/RyanFeiluX/text-vision-recognition/archive/refs/heads/main.tar.gz"
    echo -e "下载中: ${YELLOW}${REPO}${NC}"
    TMP_DIR=$(mktemp -d)
    curl -fsSL "$REPO" | tar -xz -C "$TMP_DIR" --strip-components=1 2>/dev/null || {
        echo -e "${RED}❌ 下载失败，请检查网络连接${NC}"
        echo "   备选方案: git clone https://github.com/RyanFeiluX/text-vision-recognition.git"
        rm -rf "$TMP_DIR"
        exit 1
    }
    echo -e "${GREEN}✓ 下载成功${NC}"
    mkdir -p "$INSTALL_DIR"
    cp -r "$TMP_DIR/scripts" "$TMP_DIR/SKILL.md" "$TMP_DIR/requirements.txt" "$TMP_DIR/references" "$TMP_DIR/assets" "$INSTALL_DIR/" 2>/dev/null || true
    rm -rf "$TMP_DIR"
fi

# ── 安装 Python 依赖 ──────────────────────────
echo -e ""
echo -e "${YELLOW}安装 Python 依赖...${NC}"
if [ -f "$INSTALL_DIR/requirements.txt" ]; then
    $PYTHON -m pip install -r "$INSTALL_DIR/requirements.txt" -q 2>/dev/null || {
        echo -e "${YELLOW}⚠ pip 安装失败，尝试逐包安装...${NC}"
        $PYTHON -m pip install PyMuPDF Pillow openai -q
    }
    echo -e "${GREEN}✓ 依赖安装完成${NC}"
fi

# ── 安装快捷命令 ─────────────────────────────
BIN_DIR="$HOME/.local/bin"
mkdir -p "$BIN_DIR"
CMD_PATH="$BIN_DIR/pdf2md-qwen"
cat > "$CMD_PATH" << 'CMDEOF'
#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "$(readlink -f "$0")")" && pwd)"

# 尝试多个可能的位置
for DIR in \
    "$HOME/.hermes/skills/productivity/text-vision-recognition" \
    "$HOME/.local/share/text-vision-recognition"; do
    if [ -f "$DIR/scripts/qwen_ocr.py" ]; then
        exec python3 "$DIR/scripts/qwen_ocr.py" "$@"
    fi
done

# 若都找不到，尝试从脚本自身位置推断
PARENT_DIR="$(dirname "$SCRIPT_DIR")"
if [ -f "$PARENT_DIR/scripts/qwen_ocr.py" ]; then
    exec python3 "$PARENT_DIR/scripts/qwen_ocr.py" "$@"
fi

echo "❌ 错误：找不到 qwen_ocr.py，请重新运行安装脚本"
exit 1
CMDEOF
chmod +x "$CMD_PATH"
echo -e "${GREEN}✓ 快捷命令已安装: $CMD_PATH${NC}"

# ── 检测 PATH ─────────────────────────────────
if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
    echo -e ""
    echo -e "${YELLOW}⚠ 提示: $HOME/.local/bin 不在 PATH 中${NC}"
    echo "   运行以下命令添加到当前会话："
    echo "   export PATH=\"\$HOME/.local/bin:\$PATH\""
    echo "   或添加到 ~/.bashrc 以永久生效："
    echo "   echo 'export PATH=\"\$HOME/.local/bin:\$PATH\"' >> ~/.bashrc"
fi

# ── 配置提示 ──────────────────────────────────
echo -e ""
echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  ✅ 安装完成！                         ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
echo ""
echo -e "下一步配置 Qwen API Key："
echo ""
echo -e "  1. 在 ${YELLOW}阿里云百炼平台${NC} 创建 API Key"
echo -e "     https://bailian.console.aliyun.com/"
echo ""
echo -e "  2. 配置环境变量："
echo -e "     ${GREEN}echo 'QWEN_API_KEY=\"your..y\"' >> ~/.hermes/.env${NC}"
echo -e "     或: ${GREEN}export QWEN_API_KEY=\"your..y\"${NC}"
echo ""
echo -e "使用方式："
echo ""
echo -e "  ${GREEN}pdf2md-qwen -i 照片.jpg -o 输出.md${NC}"
echo -e "  ${GREEN}pdf2md-qwen -i 文档.pdf -o 输出.md${NC}"
echo -e "  ${GREEN}pdf2md-qwen -i ./图片目录/ -o ./输出目录/${NC}"
echo ""
echo -e "帮助：${GREEN}pdf2md-qwen --help${NC}"
echo ""
