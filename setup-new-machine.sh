#!/usr/bin/env bash
# ============================================================
# B/C 电脟一键部署脚本
# 功能：生成 SSH key → 配置 SSH config → 测试连接 → clone → 安装
# 使用：bash setup-new-machine.sh
# ============================================================

set -euo pipefail

REPO_HOST="github-huzhongyin"
REPO_URL="${REPO_HOST}:huzhongyin/ai-dofiles.git"
CLONE_DIR="${HOME}/ai-dofiles"
SSH_KEY="${HOME}/.ssh/id_huzhongyin_ed25519"
SSH_CONFIG="${HOME}/.ssh/config"

echo "=== AI 环境配置一键部署 ==="

# 1. 确保 .ssh 目录存在
mkdir -p "${HOME}/.ssh"
chmod 700 "${HOME}/.ssh"

# 2. 生成 SSH key（如果不存在）
if [ ! -f "${SSH_KEY}" ]; then
    echo "[1/5] 生成 SSH key..."
    ssh-keygen -t ed25519 -C "huzhongyin" -f "${SSH_KEY}" -N ""
    echo "✅ SSH key 已生成: ${SSH_KEY}"
else
    echo "[1/5] SSH key 已存在，跳过生成"
fi

# 3. 配置 SSH config
if [ ! -f "${SSH_CONFIG}" ] || ! grep -q "Host ${REPO_HOST}" "${SSH_CONFIG}" 2>/dev/null; then
    echo "[2/5] 配置 SSH config..."
    cat >> "${SSH_CONFIG}" << EOF

# huzhongyin GitHub 账户
Host ${REPO_HOST}
    HostName github.com
    User git
    IdentityFile ${SSH_KEY}
    IdentitiesOnly yes
EOF
    chmod 600 "${SSH_CONFIG}"
    echo "✅ SSH config 已更新"
else
    echo "[2/5] SSH config 已配置，跳过"
fi

# 4. 测试 SSH 连接
echo "[3/5] 测试 SSH 连接..."
if ssh -T -o StrictHostKeyChecking=accept-new "${REPO_HOST}" 2>&1 | grep -q "successfully authenticated"; then
    echo "✅ SSH 连接成功"
else
    echo "⚠️ SSH 连接失败"
    echo ""
    echo "请把以下公钥添加到 huzhongyin 的 GitHub Settings -> SSH Keys："
    echo ""
    cat "${SSH_KEY}.pub"
    echo ""
    echo "添加完成后，重新运行本脚本。"
    exit 1
fi

# 5. 克隆仓库
if [ -d "${CLONE_DIR}" ]; then
    echo "[4/5] 目录 ${CLONE_DIR} 已存在，跳过 clone"
else
    echo "[4/5] 克隆仓库..."
    git clone "${REPO_URL}" "${CLONE_DIR}"
    echo "✅ 克隆完成"
fi

# 6. 运行 install.sh
echo "[5/5] 部署配置..."
cd "${CLONE_DIR}"
./install.sh

echo ""
echo "🎉 部署完成！"
echo "以后更新配置：cd ${CLONE_DIR} && git pull"
