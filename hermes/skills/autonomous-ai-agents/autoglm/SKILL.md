---
name: autoglm
description: Open-AutoGLM 手机智能体框架 - 通过AI自动操作Android/鸿蒙/iOS手机完成各种任务
version: 1.0.0
author: 智谱AI
tags: [mobile-agent, android, harmonyos, ios, automation, vision-language-model]
related_skills: []
---

# AutoGLM 手机智能体框架

Open-AutoGLM 是一个开源的手机Agent框架，能让AI通过自然语言指令自动操作手机完成各种任务。

## 核心工作流程
1. 用户输入自然语言指令（如"打开小红书搜索美食攻略"）
2. 系统截取手机屏幕截图
3. 视觉语言模型（VLM）分析屏幕内容并输出下一步操作
4. ADB/HDC/iOS工具执行操作（点击、滑动、输入等）
5. 循环执行直到任务完成

## 快速开始（5分钟上手）

### 1. 环境准备
```bash
# 克隆项目
git clone https://github.com/zai-org/Open-AutoGLM.git
cd Open-AutoGLM

# 安装依赖
pip install -r requirements.txt
pip install -e .

# 检查ADB
adb version
```

### 2. 连接Android设备
```bash
# 连接手机并开启USB调试
adb devices

# 应该看到类似输出：
# List of devices attached
# XXXXXXXX    device
```

### 3. 获取API Key
访问 https://open.bigmodel.cn/ 注册并获取API Key。

### 4. 运行第一个任务
```bash
# 方法1：使用演示脚本
python demo_autoglm.py

# 方法2：直接运行
python main.py \
  --base-url https://open.bigmodel.cn/api/paas/v4 \
  --model "autoglm-phone" \
  --apikey "YOUR_API_KEY" \
  "打开微信查看消息"
```

### 5. 支持的任务示例
```bash
# 社交通讯
"打开微信查看消息"
"打开QQ查看好友动态"

# 电商购物
"打开淘宝搜索无线耳机"
"打开京东搜索手机"

# 美食外卖
"打开美团搜索附近的火锅店"
"打开饿了么搜索奶茶"

# 视频娱乐
"打开bilibili搜索Python教程"
"打开抖音刷视频"

# 生活服务
"打开小红书搜索美食攻略"
"打开高德地图导航到北京站"
```

## 设备配置要求

### Android设备
1. **开启开发者模式**：
   - 设置 → 关于手机 → 连续点击版本号7次
   
2. **开启USB调试**：
   - 设置 → 开发者选项 → USB调试
   
3. **安装ADB Keyboard**：
   ```bash
   # 下载APK
   wget https://github.com/senzhk/ADBKeyBoard/raw/master/ADBKeyboard.apk
   
   # 安装到手机
   adb install ADBKeyboard.apk
   
   # 启用输入法
   adb shell ime enable com.android.adbkeyboard/.AdbIME
   ```

### 鸿蒙设备
1. 开启USB调试和无线调试
2. 使用HDC工具：`hdc list targets`
3. 无需安装额外输入法

### iOS设备
1. 安装WebDriverAgent
2. 配置Xcode工程
3. 使用 `--device-type ios` 参数

## 常用命令

### 基础命令
```bash
# 交互模式
python main.py --base-url https://open.bigmodel.cn/api/paas/v4 --model "autoglm-phone" --apikey "YOUR_KEY"

# 单次任务
python main.py --base-url https://open.bigmodel.cn/api/paas/v4 --model "autoglm-phone" --apikey "YOUR_KEY" "打开淘宝搜索无线耳机"

# 列出支持的应用
python main.py --list-apps

# 检查模型部署
python scripts/check_deployment_cn.py --base-url https://open.bigmodel.cn/api/paas/v4 --model autoglm-phone --apikey YOUR_KEY
```

### 设备管理
```bash
# 列出已连接设备
python main.py --list-devices

# 连接远程设备
python main.py --connect 192.168.1.100:5555

# 启用TCP/IP调试
python main.py --enable-tcpip 5555
```

### 调试命令
```bash
# 详细模式
python main.py --base-url ... --model ... --apikey ... --verbose "任务描述"

# 英文模式
python main.py --lang en --base-url ... --model ... --apikey ... "Open Chrome"

# 指定最大步数
python main.py --max-steps 20 --base-url ... --model ... --apikey ... "任务描述"
```

## 核心操作指令

| 操作 | 格式 | 说明 |
|------|------|------|
| Launch | `do(action="Launch", app="xxx")` | 启动应用 |
| Tap | `do(action="Tap", element=[x,y])` | 点击坐标（0-999归一化） |
| Type | `do(action="Type", text="xxx")` | 输入文本 |
| Swipe | `do(action="Swipe", start=[x1,y1], end=[x2,y2])` | 滑动操作 |
| Back | `do(action="Back")` | 返回上一页 |
| Home | `do(action="Home")` | 回到桌面 |
| Long Press | `do(action="Long Press", element=[x,y])` | 长按 |
| Double Tap | `do(action="Double Tap", element=[x,y])` | 双击 |
| Wait | `do(action="Wait", duration="x seconds")` | 等待加载 |
| Take_over | `do(action="Take_over", message="xxx")` | 请求人工接管 |
| finish | `finish(message="xxx")` | 结束任务 |

## 环境变量配置

| 变量 | 描述 | 默认值 |
|------|------|--------|
| `PHONE_AGENT_BASE_URL` | 模型API地址 | `http://localhost:8000/v1` |
| `PHONE_AGENT_MODEL` | 模型名称 | `autoglm-phone-9b` |
| `PHONE_AGENT_API_KEY` | API密钥 | `EMPTY` |
| `PHONE_AGENT_MAX_STEPS` | 最大步数 | `100` |
| `PHONE_AGENT_DEVICE_ID` | 设备ID | (自动检测) |
| `PHONE_AGENT_DEVICE_TYPE` | 设备类型 | `adb` |
| `PHONE_AGENT_LANG` | 语言 | `cn` |

## Python API

### 基础使用
```python
from phone_agent import PhoneAgent
from phone_agent.model import ModelConfig
from phone_agent.agent import AgentConfig

# 配置模型
model_config = ModelConfig(
    base_url="https://open.bigmodel.cn/api/paas/v4",
    model_name="autoglm-phone",
    api_key="YOUR_API_KEY",
    temperature=0.1,
)

# 配置Agent
agent_config = AgentConfig(
    max_steps=50,
    verbose=True,
    lang="cn",
)

# 创建Agent
agent = PhoneAgent(
    model_config=model_config,
    agent_config=agent_config,
)

# 执行任务
result = agent.run("打开淘宝搜索无线耳机")
print(result)
```

### 自定义回调
```python
def my_confirmation(message: str) -> bool:
    """敏感操作确认回调"""
    return input(f"确认执行 {message}？(y/n): ").lower() == "y"

def my_takeover(message: str) -> None:
    """人工接管回调"""
    print(f"请手动完成: {message}")
    input("完成后按回车继续...")

agent = PhoneAgent(
    confirmation_callback=my_confirmation,
    takeover_callback=my_takeover,
)
```

## 故障排除

### 设备未找到
```bash
adb kill-server
adb start-server
adb devices
```

### 能打开应用但无法点击
开启「USB调试(安全设置)」

### 文本输入不工作
确保ADB Keyboard已安装并启用

### 截图黑屏
敏感页面（支付/银行类应用），系统会自动处理

### API连接失败
1. 检查API Key是否正确
2. 检查网络连接
3. 检查Base URL是否正确

## 项目结构

```
Open-AutoGLM/
├── main.py                    # 命令行入口
├── phone_agent/               # 核心包
│   ├── __init__.py            # 导出PhoneAgent、IOSPhoneAgent
│   ├── agent.py               # Android/鸿蒙Agent
│   ├── agent_ios.py           # iOS Agent
│   ├── device_factory.py      # 设备工厂
│   ├── actions/               # 操作处理
│   ├── adb/                   # Android设备控制
│   ├── hdc/                   # 鸿蒙设备控制
│   ├── xctest/                # iOS设备控制
│   ├── config/                # 配置
│   └── model/                 # 模型客户端
├── scripts/                   # 工具脚本
├── examples/                  # 使用示例
├── docs/                      # 文档
└── resources/                 # 资源文件
```

## 相关链接

- GitHub仓库：https://github.com/zai-org/Open-AutoGLM
- 智谱BigModel文档：https://docs.bigmodel.cn/cn/api/introduction
- ModelScope模型：https://modelscope.cn/models/ZhipuAI/AutoGLM-Phone-9B
- ADB Keyboard：https://github.com/senzhk/ADBKeyBoard