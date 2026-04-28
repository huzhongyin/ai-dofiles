#!/usr/bin/env bash
# ============================================================
# B/C 电脑执行：从 ai-dotfiles 仓库部署配置到当前电脑
# 支持 symlink模式（默认）或 copy 模式
# 使用: ./install.sh [--copy]
# ============================================================

set -euo pipefail

DOTFILES_DIR="$(cd "$(dirname "$0")" && pwd)"
MODE="${1:-symlink}"

backup_if_exists() {
    local target="$1"
    if [ -e "$target" ] || [ -L "$target" ]; then
        local backup="${target}.backup.$(date +%Y%m%d_%H%M%S)"
        echo "  备份: $target -> $backup"
        mv "$target" "$backup"
    fi
}

link_or_copy() {
    local src="$1"
    local dst="$2"
    if [ "$MODE" == "--copy" ]; then
        if [ -d "$src" ]; then
            cp -r "$src" "$dst"
        else
            cp "$src" "$dst"
        fi
        echo "  复制: $dst"
    else
        ln -sf "$src" "$dst"
        echo "  链接: $dst -> $src"
    fi
}

echo "=== 部署 AI 环境配置 ==="
echo "模式: $MODE"
echo "源目录: $DOTFILES_DIR"
echo ""

# --- Hermes ---
echo "[Hermes]"
mkdir -p "$HOME"/.hermes

for item in skills scripts memories learning-notes; do
    if [ -e "$DOTFILES_DIR/hermes/$item" ]; then
        backup_if_exists "$HOME"/.hermes/$item
        link_or_copy "$DOTFILES_DIR/hermes/$item" "$HOME"/.hermes/$item
    fi
done

if [ -f "$DOTFILES_DIR/hermes/config.yaml" ]; then
    backup_if_exists "$HOME"/.hermes/config.yaml
    link_or_copy "$DOTFILES_DIR/hermes/config.yaml" "$HOME"/.hermes/config.yaml
fi

# --- Claude ---
echo "[Claude]"
if [ -d "$DOTFILES_DIR/claude" ]; then
    backup_if_exists "$HOME"/.claude
    link_or_copy "$DOTFILES_DIR/claude" "$HOME"/.claude
fi
if [ -f "$DOTFILES_DIR/claude.json" ]; then
    backup_if_exists "$HOME"/.claude.json
    link_or_copy "$DOTFILES_DIR/claude.json" "$HOME"/.claude.json
fi

# --- Kimi ---
echo "[Kimi]"
if [ -d "$DOTFILES_DIR/kimi" ]; then
    backup_if_exists "$HOME"/.kimi
    link_or_copy "$DOTFILES_DIR/kimi" "$HOME"/.kimi
fi

# --- Codex ---
echo "[Codex]"
if [ -d "$DOTFILES_DIR/codex" ]; then
    backup_if_exists "$HOME"/.codex
    link_or_copy "$DOTFILES_DIR/codex" "$HOME"/.codex
fi

# --- Learn Claude Code ---
echo "[Learn Claude Code]"
if [ -d "$DOTFILES_DIR/learn-claude-code" ]; then
    backup_if_exists "$HOME"/.learn-claude-code
    link_or_copy "$DOTFILES_DIR/learn-claude-code" "$HOME"/.learn-claude-code
fi

echo ""
echo "✅ 部署完成。"
if [ "$MODE" != "--copy" ]; then
    echo "提示: 配置以 symlink 形式挂载，以后在 ai-dotfiles 目录执行 'git pull' 即可更新。"
else
    echo "提示: 配置已复制到本地，更新需重新运行 ./install.sh --copy"
fi
