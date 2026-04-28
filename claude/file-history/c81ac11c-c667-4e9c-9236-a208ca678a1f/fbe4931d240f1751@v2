# sourceFile (XPBleLocation) — 项目模块地图

**项目路径：** `/Users/xpeng/Desktop/workSpace/XPMotors_Harmony/submodule/PollingSDK/sourceFile`
**语言：** C++14
**构建系统：** CMake（输出静态库 `libXPBleLocation.a`）
**最后分析时间：** 2026-03-23 19:58:00
**分析状态：** 完整分析

---

## 🚀 公共入口

**外部调用入口类：** `XPBlePollingService`（`XPBlePollingService.hpp / .cpp`）

该类是整个 SDK 的唯一对外服务门面（Facade），平台层通过以下方式接入：

1. **构造：** `XPBlePollingService(vehicleTypeCode)` — 传入车型码（如 "FA"、"HA"）
2. **注入回调：** `setPlatformCallback(IPlatformCallback*)` — 平台实现回调接口
3. **生命周期：** `startService()` / `stopService()` / `systemWillTerminate()`
4. **数据驱动：** `predictWithRssi(jsonStr)` — 核心 RSSI 数据输入
5. **状态同步：** `updateVehicleState()` / `bleHardwareUpdate()` / `blePollingConfigIsChanged()` 等

**支持车型码：** `FA, HA, EA, DF, DG, EF`（定义于 `pollingSupportSet`）

---

## 🗂 模块结构

### 1. `XPBlePollingService`（顶层服务门面）
- **文件：** `XPBlePollingService.hpp/.cpp`、`XPBlePollingServiceHeader.h`
- **职责：** 协调 BLE 测距（XPBlelocationManager）和 Polling 决策（XPBlePollingManager），管理 BLE 连接状态、断连定时器、自标定
- **关键依赖：**
  - `XPBlePollingManager` — 上锁/解锁决策引擎
  - `XPBlelocationManager` — BLE 位置推断引擎
  - `IPlatformCallback` — 向上层平台发送指令的回调接口
  - `XPThread` — SDK 专用线程

---

### 2. `XPBlePolling/`（Polling 决策层）
- `XPBlePollingManager.hpp/.cpp` — Polling 管理器，派发到具体版本 Handler
- `XPBlePollingHandler.hpp/.cpp` — Handler 抽象基类
- `XPBlePollingHandlerV1.hpp/.cpp` — V1 版 Polling 决策实现
- `XPBlePollingHandlerV2.hpp/.cpp` — V2 版 Polling 决策实现
- `XPBlePollingHeader.h` — 命名空间 `POLLING`：
  - 所有枚举（`polling_action`、`polling_mode`、`polling_distance_level`、`vehicle_state`、各种门/锁/电源状态）
  - `Observable<T>` 模板——响应式属性，支持 addListener/removeListener/operator=
  - `polling_config`、`function_config` 配置结构体

---

### 3. `XPBleLocation/`（BLE 位置推断层）
- `XPBlelocationManager.hpp/.cpp` — 位置管理器，派发到具体版本 Inference
- `XPPredictInference.hpp/.cpp` — 推断抽象基类
- `XPPredictInferenceV1~V4.hpp/.cpp` — 4 个版本推断算法实现（RSSI → 距离 → 方向）
- `XPPredictModel.hpp/.cpp` — 模型基类
- `XPPredictModelV1~V4.hpp/.cpp` — 4 个版本数据模型
- `XPPredictInferenceHeader.h` — 命名空间 `RSSI`：
  - BLE 位置枚举（`ble_postion`：center/left_front/right_front/rear/back_left/back_right）
  - 方向枚举（`vehicle_direction`：12 个方向，含车内4个方位）
  - 核心算法：`calculateDistance(txPower, rssi, a, b, c)` — RSSI 转距离公式
  - 数据结构：`ble_rssi`、`ble_config_info`、`ble_cover_map`、`on_time_distance` 等
- `XPPredictModelHeader.h` — `ble_predict_result` 推断结果结构

---

### 4. `BaseTool/`（基础工具层）
- `LogHelper.h` — 日志协议（`LogProtocol`），供各层继承实现日志输出
- `ObjectFactory.h` — 对象工厂（泛型工厂，按 key 创建对象）
- `ReadWriteProperty.hpp` — 线程安全的读写属性封装
- `XPThread.hpp` — SDK 专用线程封装
- `Timer.h` — 定时器工具
- `XPBaseDefined.h` — 命名空间 `XPBase` 基础宏/类型定义

---

### 5. `IPlatformCallback/`（平台回调接口层）
- `IPlatformCallback.hpp` — 纯虚接口，平台层必须实现：
  - `sendPollingAction(polling_action)` — SDK 向平台发送解锁/闭锁等指令
  - 继承 `LogProtocol`（平台层提供日志实现）

---

### 6. `LocalResource/`（本地资源/阈值数据层）
- `XPBleLocationCoverMap.h` — BLE 覆盖图映射数据
- `XPPollingV1Threshold.h` — V1 Polling 阈值
- `XPPollingV2Threshold.h` — V2 Polling 阈值
- `XPSelfCalibrationPhoneThreshold.h` — 自标定手机阈值数据

---

### 7. `Tools/`（JSON 解析工具）
- `XPBlePollingConfigParser.hpp/.cpp` — Polling 配置 JSON 解析
- `XPBleLocationConfigParser.hpp/.cpp` — 位置配置 JSON 解析
- `XPBleRssiParser.hpp/.cpp` — RSSI 原始数据 JSON 解析
- `XPJsonParserHeader.h` — 解析器公共头
- `nlohmann/json.hpp` — 第三方 JSON 库（header-only，nlohmann/json v3.x）

---

### 8. 根目录独立文件
- `XPRssiModel.hpp/.cpp` — RSSI 数据模型（原始 RSSI 数据封装）
- `LogHelper.h`、`ObjectFactory.h` — 与 `BaseTool/` 中同名文件（根目录副本）

---

## 📐 架构关系图

```
平台层（iOS/HarmonyOS/Android）
    ↓ implements
IPlatformCallback  ←─────────────────────────────────┐
    ↑ callback                                        │
XPBlePollingService（服务门面）                        │
    ├── XPBlelocationManager（位置推断）                │
    │     └── XPPredictInferenceV1~V4                  │
    │           └── XPPredictModelV1~V4                │
    ├── XPBlePollingManager（Polling决策）              │
    │     └── XPBlePollingHandlerV1~V2                 │
    ├── IPlatformCallback* callback_ ──────────────────┘
    └── BaseTool（Logger/Thread/Timer/Factory）

数据流：
  predictWithRssi(json) → XPBleRssiParser → XPBlelocationManager → ble_predict_result
                                                                          ↓
                                              XPBlePollingManager（决策：解锁/闭锁/车内）
                                                                          ↓
                                              IPlatformCallback::sendPollingAction()
```

---

## 🔑 核心设计模式

| 模式 | 应用位置 |
|------|---------|
| Facade | `XPBlePollingService` 统一对外接口 |
| Strategy/版本化 | V1~V4 多版本 Inference/Handler，运行时按配置选择 |
| Observer | `Observable<T>` 响应式属性（车辆状态驱动 Polling 决策） |
| Factory | `ObjectFactory` 按 key 创建对象实例 |
| Template Method | `XPPredictInference` / `XPBlePollingHandler` 抽象基类 + 具体版本实现 |

---

## 💾 分析已保存
`~/.claude/analyses/sourceFile-a6d8e669/`
- `PROJECT_MAP.md`（完整模块地图）✅
- `INDEX.md`（项目索引，轻量扫描）