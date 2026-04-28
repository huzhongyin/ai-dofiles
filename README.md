# AI 环境配置同步

本仓库用于在多台电脑间同步 AI 工具链配置。

## 包含配置

- **Hermes**: skills、scripts、config.yaml、memories、learning-notes
- **Claude Code**: ~/.claude/ 配置
- **Kimi Code**: ~/.kimi/ 配置（排除 credentials、logs、sessions）
- **Codex**: ~/.codex/ 配置（排除 SQLite logs）

## A 电脟（首次推送）

如果尚未推送到 GitHub：

```bash
cd ~/ai-dotfiles
git push -u origin main
```

若推送失败（SSH 权限），请将以下公钥添加到 GitHub Settings -> SSH Keys：

```
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAICIiJSLsbGJjhFKrz4gyg8NV1nQqt6fKmGFPBesMP0uu huzy2 L43H4GT4X0
```

添加后重试推送即可。

## B/C 电脟（部署）

```bash
git clone git@github.com:huzhongyin/ai-dofiles.git ~/ai-dotfiles
cd ~/ai-dotfiles
./install.sh
```

`install.sh` 默认使用 symlink 模式，以后在 `~/ai-dotfiles` 内执行 `git pull` 即可更新全局配置。

若不想使用 symlink（比如某些工具不兼容），改用复制模式：

```bash
./install.sh --copy
```

## 更新配置

在任意电脟修改配置后：

```bash
cd ~/ai-dotfiles
git add .
git commit -m "update config"
git push
```

其他电脟更新：

```bash
cd ~/ai-dotfiles
git pull
```

symlink 模式下 `git pull` 后配置立即生效，无需重新运行 install.sh。
