# 迁移计划：XPBleHeartbeatAlive 系统状态监控 → XPVehicleSDK

## Context

`XPBleHeartbeatAlive`（ObjC，位于 XPCarControlCore）包含一个 5 秒 GCD 定时器，承担两类职责：
1. **心跳发送** — 已在 XPVehicleSDK 的 `XiaopengBLEConnection+Heartbeat.swift` 中实现
2. **系统状态监控** — 定时器延迟检测（>7s 视为异常）、后台保活时长统计（含唤醒/休眠分段）

用户要求：**仅迁移第 2 部分**（统计系统状态和后台保活累计持续时间的逻辑）到 XPVehicleSDK。

---

## 迁移范围

### ✅ 迁移
| ObjC 逻辑 | 对应位置 |
|-----------|---------|
| 定时器延迟检测（`timerDiff > kBleHeartInterval + 2`）→ B069 埋点 | `initTimerConfig` 定时器 block |
| 后台保活时长统计（`backgroundTimeBegin` / `backgroundBatteryLevel`）| `enterBackground` / `becomeActive` |
| 唤醒/休眠分段追踪（`XPAliveTimeDuration`）| `startRecord` / `stopRecord` / `updateTimer` |
| 系统健康日志（电量、App 状态） | 定时器 block 中的 `DLogTagInfo` |

### ❌ 不迁移
| ObjC 逻辑 | 原因 |
|-----------|------|
| 心跳发送 `sendHeartbeat` | 已在 XPVehicleSDK `Heartbeat.swift` 实现 |
| 蓝牙设备切换 `getNexAvailableBleName` | 已在 SDK 实现 |
| CPU/内存指标 | 需 `task_info()` 等受限 API，SDK 无对应依赖，仅保留电量 |

---

## 架构设计

```
┌─ XiaopengBLEConnection+Heartbeat.swift (已有 5s Timer) ─┐
│  checkIfNeedSendHeartbeat()                              │
│  ＋ keepAliveMonitor.onHeartbeatTick()  ← 新增一行       │
└──────────────────────────┬───────────────────────────────┘
                           ↓ 每 5s
┌─ BLEKeepAliveMonitor.swift (新文件) ─────────────────────┐
│  • detectTimerLag()      → B069 埋点                     │
│  • logSystemHealth()     → 电量 + App 状态日志           │
│  • timeDuration.tick()   → 分段追踪                      │
│                                                          │
│  订阅 AppRunState.$isInBackground:                       │
│    true  → handleEnterBackground()                       │
│    false → handleBecomeActive() → 报告后台统计           │
│  订阅 .ApplicationWillSuspended:                         │
│    → handleWillSuspend() → 关闭当前唤醒段                │
└──────────────────────────┬───────────────────────────────┘
                           ↓
┌─ BLEAliveTimeDuration.swift (新文件) ────────────────────┐
│  XPAliveTimeDuration 的 Swift 移植                       │
│  • startRecord() / stopRecord() / updateTimer()          │
│  • 唤醒/休眠分段数组 heartbeatTimeSections                │
│  • >15s 间隔 = 休眠分段边界                               │
│  • 统计报表: totalAliveDuration / totalSuspendDuration    │
└─────────────────────────────────────────────────────────┘
```

---

## 文件清单

### 新建文件 (2个)

#### 1. `BLEAliveTimeDuration.swift`
- **路径**: `XPVehicleSDK/VehicleControl/Core/VehicleConnection/BLEConnection/BLEAliveTimeDuration.swift`
- **职责**: `XPAliveTimeDuration` 的 Swift 等价实现
- **关键逻辑**:
  - `startRecord()`: 初始化 `backgroundTimeBegin` 和 `heartbeatTimeSections` 数组，首元素 = 当前时间
  - `stopRecord()`: 清空数组和时间戳
  - `updateTimer()`: 检测间隔 >15s → 记录休眠边界（pair: 上次时间 + 当前时间）
  - `totalAliveDuration()`: 遍历 sections 数组，偶数索引为段起点、奇数为段终点，求和
  - `totalSuspendDuration()`: 计算休眠段总时长
  - 保留 ObjC 原始的数组 pair 逻辑（偶数=唤醒起点，奇数=休眠起点），日志格式化方法一并移植

#### 2. `BLEKeepAliveMonitor.swift`
- **路径**: `XPVehicleSDK/VehicleControl/Core/VehicleConnection/BLEConnection/BLEKeepAliveMonitor.swift`
- **职责**: 系统状态监控协调器
- **依赖**:
  - `AppRunState.shared.$isInBackground` — 前后台切换（已有 Combine publisher）
  - `.ApplicationWillSuspended` 通知 — 即将挂起（`ApplicationState.swift` 已发送）
  - `BLEAliveTimeDuration` — 唤醒/休眠分段
  - `Statistics.writeBulkEvent()` — 埋点（SDK 已有）
- **关键逻辑**:
  - `onHeartbeatTick()`: 由外部心跳定时器调用，执行延迟检测 + 分段 tick + 健康日志
  - `detectTimerLag()`: 对比 `lastTickTime`，间隔 >7s → `Statistics.writeBulkEvent(event: "B069", ...)`
  - `handleEnterBackground()`: 记录 `backgroundBeginTime` + `backgroundBattery`，调用 `timeDuration.startRecord()`
  - `handleBecomeActive()`: 计算后台时长、电量消耗、唤醒时长，调用 `timeDuration.stopRecord()`，埋点
  - `handleWillSuspend()`: 重置 `lastTickTime` 和系统状态快照（对应 ObjC `willSuppend` 方法）

### 修改文件 (1个)

#### 3. `XiaopengBLEConnection+Heartbeat.swift`
- **路径**: `XPVehicleSDK/VehicleControl/Core/VehicleConnection/BLEConnection/XiaopengBLEConnection+Heartbeat.swift`
- **改动量**: 新增 ~3 行
- **具体改动**:
  - 在 `checkIfNeedSendHeartbeat()` 方法中，增加调用 `keepAliveMonitor.onHeartbeatTick()`
  - 注意：无论是否需要发送心跳（`isNeedsHeartbeat`），系统状态监控都应该执行

#### 4. `XiaopengBLEConnection.swift`
- **路径**: `XPVehicleSDK/VehicleControl/Core/VehicleConnection/BLEConnection/XiaopengBLEConnection.swift`
- **改动量**: 新增 1 行属性声明
- **具体改动**:
  - 添加 `lazy var keepAliveMonitor = BLEKeepAliveMonitor()` 属性（避免使用 `objc_setAssociatedObject`，直接在主类声明更清晰）

---

## 关键设计决策

### 1. 复用现有 5s 心跳定时器 vs 独立定时器
**选择**: 复用现有定时器
- 定时器延迟检测必须检测的是**同一个定时器**的延迟，独立定时器无法检测心跳定时器的真实调度情况
- 避免两个 5s 定时器同时运行的资源浪费

### 2. 生命周期事件来源
**选择**: `AppRunState.$isInBackground` + `.ApplicationWillSuspended` 通知
- `AppRunState` 已经在响应 `ApplicationState` 的状态变化，直接订阅 `$isInBackground` 即可覆盖 `enterBackground` / `becomeActive`
- `.ApplicationWillSuspended` 已由 `ApplicationState` 在 `backgroundTimeRemaining < 5` 时发送，完美对应 ObjC 的 `willSuppend`

### 3. 属性存储方式
**选择**: 直接在 `XiaopengBLEConnection` 类中声明 lazy var
- 比 `objc_setAssociatedObject` 更 Swift-idiomatic
- `XiaopengBLEConnection.swift` 是普通 class（非 extension），可以直接添加属性

### 4. 埋点方式
**选择**: 使用 SDK 已有的 `Statistics.writeBulkEvent(event:module:data:)`
- SDK 中已有完整的 Statistics 代理体系（`StatisticsProtocol` → `ProxyManger.shared.statisticsProxy`）
- ObjC 的 `[XPTrackHelper trackType:6 event:@"B069" ...]` 对应 SDK 的精卫埋点 `writeBulkEvent`
- module 使用 `"P00004"` 保持与 ObjC 一致

### 5. tick 调用位置
**选择**: 在 `checkIfNeedSendHeartbeat()` 中调用，**放在心跳判断之前**
- ObjC 原始逻辑中，系统状态监控与 `isStart` 无关，定时器 block 中总是先做延迟检测和日志记录
- 只有心跳发送受 `isStart` 控制
- 因此 `onHeartbeatTick()` 应无条件执行

---

## 实现步骤

### Step 1: 创建 `BLEAliveTimeDuration.swift`
忠实移植 `XPAliveTimeDuration` 的核心逻辑：
- `heartbeatTimeSections: [CFAbsoluteTime]` 数组
- `startRecord()` / `stopRecord()` / `updateTimer()`
- `totalAliveDuration()` / `totalSuspendDuration()`
- 日志格式化辅助方法

### Step 2: 创建 `BLEKeepAliveMonitor.swift`
- 初始化时订阅 `AppRunState.$isInBackground` 和 `.ApplicationWillSuspended`
- 实现 `onHeartbeatTick()` / `handleEnterBackground()` / `handleBecomeActive()` / `handleWillSuspend()`
- 使用 `Statistics.writeBulkEvent` 发送 B069 和后台统计埋点

### Step 3: 修改 `XiaopengBLEConnection.swift`
- 添加 `lazy var keepAliveMonitor = BLEKeepAliveMonitor()` 属性

### Step 4: 修改 `XiaopengBLEConnection+Heartbeat.swift`
- 在 `checkIfNeedSendHeartbeat()` 开头添加 `keepAliveMonitor.onHeartbeatTick()`

---

## 验证方式

1. **编译验证**: `xcodebuild build` 确认无编译错误
2. **日志验证**: 运行后检查以下日志输出:
   - `[BLEKeepAliveMonitor] Enter background, battery: XX%`
   - `[BLEKeepAliveMonitor] Health — battery: XX%, appState: XX`
   - `[BLEKeepAliveMonitor] Timer lag detected` (模拟断点暂停 >7s 可触发)
   - `[BLEKeepAliveMonitor] BecomeActive — backgroundDuration: Xs, awakeTime: Xs`
3. **埋点验证**: 确认 B069 事件参数格式与 ObjC 一致
