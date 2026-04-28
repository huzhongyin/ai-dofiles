# XPBleLocation 依赖图

**语言：** C++14
**构建系统：** CMake 3.10+
**输出：** 静态库 libXPBleLocation.a
**生成时间：** 2026-03-23 19:56

## 外部依赖

| 包名 | 版本 | 来源 | 用途标注 |
|-----|------|------|---------|
| nlohmann/json | 3.x | 内嵌头文件 | JSON解析 |
| C++ STL | C++14 | 系统标准库 | 基础数据结构和算法 |

## 内部模块依赖关系

```
XPBlePollingService → XPBlelocationManager, XPBlePollingManager, IPlatformCallback
XPBlelocationManager → XPPredictInferenceV1, XPPredictInferenceV2, XPPredictInferenceV3, XPPredictInferenceV4
XPBlePollingManager → XPBlePollingHandlerV1, XPBlePollingHandlerV2
XPPredictInferenceV1~V4 → XPPredictModelV1~V4
XPBlePollingHandlerV1~V2 → POLLING命名空间配置
XPBlePollingConfigParser → XPJsonParserHeader, nlohmann/json
XPBleLocationConfigParser → XPJsonParserHeader, nlohmann/json
XPBleRssiParser → XPJsonParserHeader, nlohmann/json
XPBlePollingService → LogHelper, ObjectFactory, Timer, XPThread
所有模块 → BaseTool/*（ReadWriteProperty, LogProtocol等）
```

## 模块层次结构

### 第1层：服务门面
- **XPBlePollingService** — 统一对外接口，协调位置检测和轮询决策

### 第2层：核心业务模块
- **XPBlelocationManager** — BLE位置推断管理器
- **XPBlePollingManager** — 轮询决策管理器

### 第3层：版本化算法实现
- **位置推断层：** XPPredictInferenceV1~V4（4个版本并存）
- **轮询处理层：** XPBlePollingHandlerV1~V2（2个版本并存）
- **数据模型层：** XPPredictModelV1~V4

### 第4层：配置解析与工具
- **配置解析器：** XPBlePollingConfigParser, XPBleLocationConfigParser, XPBleRssiParser
- **基础工具：** LogHelper, ObjectFactory, Timer, XPThread, ReadWriteProperty

### 第5层：平台抽象与资源
- **平台接口：** IPlatformCallback（纯虚接口，需平台实现）
- **静态资源：** LocalResource/（阈值配置数据）

## 依赖模式分析

### ✅ 良好设计模式
1. **分层清晰**: 服务 → 管理 → 版本实现 → 工具的清晰分层
2. **版本并存**: V1-V4算法版本可同时存在，支持A/B测试和逐步迁移
3. **接口抽象**: IPlatformCallback实现平台解耦
4. **工具复用**: BaseTool模块被所有上层模块复用

### ⚠️ 需关注的耦合
1. **版本管理**: 4个版本的InferenceV1~V4都直接依赖对应的ModelV1~V4
2. **配置依赖**: 多个Parser都依赖nlohmann/json，形成共同依赖点
3. **全局工具**: LogHelper等在根目录和BaseTool目录有重复

## ⚠️ 循环依赖

经检查未发现循环依赖。所有依赖关系为有向无环图（DAG）。

## 架构特点

1. **多版本共存策略**: 支持V1-V4多个算法版本同时编译，运行时按配置选择
2. **平台适配模式**: 通过IPlatformCallback纯虚接口实现跨平台支持
3. **配置驱动**: 大量使用JSON配置文件，支持运行时参数调整
4. **线程安全**: ReadWriteProperty提供线程安全的属性访问机制

## 分析说明

- **CMake构建**: 使用GLOB_RECURSE收集所有.cpp/.h文件，生成单一静态库
- **无外部包管理**: 除nlohmann/json内嵌头文件外，无其他第三方依赖
- **内部模块**: 通过#include依赖关系分析得出，共识别8个主要模块层次
- **版本策略**: 采用文件名后缀V1~V4区分算法版本，而非继承关系