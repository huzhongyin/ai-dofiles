# Polling解锁失败错误码10901分析报告

**诊断时间：** 2026-03-23 20:29
**日志文件：** com.xiaopeng.mycarinfoHarmony_V2.8.0_70_20260305.xlog.log
**发生时间：** 2026-03-05 07:34:52-07:34:53
**错误关键词：** polling解锁失败

---

## 🚨 问题概述

小鹏汽车Harmony应用在执行polling解锁操作时连续失败，车辆返回错误码`10901`，错误信息为"解锁失败"。

### 核心错误事件

```
[E][2026-03-05 +8.0 07:34:52.664] BLE [PollingUnlock]指令发送失败:
VehicleError<code=10901, channel=1, msg=解锁失败, desc=BLE 指令发送失败，code: 10901>
vcrId:1021000049

[E][2026-03-05 +8.0 07:34:53.202] BLE [PollingUnlock]指令发送失败:
VehicleError<code=10901, channel=1, msg=解锁失败, desc=BLE 指令发送失败，code: 10901>
vcrId:1029415906
```

---

## 🔍 问题分析

### 1. 错误特征

| 属性 | 值 |
|------|-----|
| **错误码** | 10901 |
| **发生频次** | 连续2次，间隔540ms |
| **通信通道** | BLE (蓝牙低功耗) |
| **指令类型** | PollingUnlock (polling解锁车门-不上电) |
| **车辆ID** | L1NNSGHB7PB013058 |

### 2. 系统状态验证

**✅ 蓝牙连接正常**
```log
[I] BLE State Changed: AVAILABLE
[I] 开始BLE认证流程
[I] 蓝牙已经可用
```

**✅ RSSI数据流正常**
```log
[I] parseRssiData: 088005BECFB8CC27, result: [{"name":"BLE","rssi":-66}...]
[I] predictWithRssi: [{"name":"BLE","rssi":-66}...]
```

**✅ 车态数据接收正常**
```log
[I] 收到车态数据: {"vin":"L1NNSGHB7PB013058","timestamp":1772667292612,"polling":{"tBox4GState":0}}
[I] 门锁状态： 1  // 车辆处于锁定状态
```

**✅ 认证令牌充足**
```log
[I] leftCertCount: 359  // 认证令牌数量正常
```

### 3. 关键调用链重建

```
应用层 KMPollingService_JS
    ↓
BLEConnection 指令发送流程
    ↓ (tBoxCommand=Polling解锁车门（不上电）)
车辆CAN总线
    ↓ (carControlResult: controlId=20, controlState=10901)
车控指令基类 → XP车控实例 → 应用层错误回调
```

### 4. 根因分析

**主要原因：车辆端拒绝执行解锁指令**

从CAN总线返回的`controlState=10901`表明：
- 车辆收到了解锁指令（controlId=20）
- 但车辆端执行失败，返回状态码10901
- 这不是通信问题，而是车辆端的业务逻辑拒绝

**可能的车辆端拒绝原因：**
1. **车辆状态不满足解锁条件**（如：引擎运行中、某些安全条件未满足）
2. **Polling模式状态机异常**（车辆端polling状态与预期不符）
3. **安全策略限制**（频繁操作保护、时间窗口限制等）
4. **车控ECU内部错误**（硬件或软件故障）

---

## 🛠 技术细节

### CAN总线事件详情

```json
{
    "type": "canEvent",
    "canEvent": {
        "eventType": "carControlResult",
        "controlId": 20,              // polling解锁指令
        "controlState": 10901         // 执行失败状态码
    }
}
```

### BLE通信链路

```
Mobile App → BLE → 车辆蓝牙模块 → CAN总线 → 车控ECU
                                            ↓
                   错误回传 ←←←←←←←←←←←←←← controlState=10901
```

### 时序分析

| 时间 | 事件 |
|------|------|
| 07:34:52.608 | 接收CAN事件：controlState=10901 |
| 07:34:52.659 | BLE waitForResponse检测到错误 |
| 07:34:52.664 | 指令执行失败，向应用层抛出错误 |
| 07:34:53.201 | 第二次尝试，再次失败 |

---

## 💡 解决建议

### 优先级1：数据收集

1. **收集更多错误码10901的案例**，分析是否存在模式
2. **记录车辆状态**：引擎状态、电子手刹、车门传感器等
3. **检查polling配置**：确认polling模式参数设置

### 优先级2：代码排查

1. **排查车辆端polling状态机**，确认10901错误码的具体含义
2. **检查解锁条件判断逻辑**，如车辆状态前置条件
3. **验证BLE认证状态**，虽然认证通过但可能存在权限问题

### 优先级3：容错优化

1. **增强错误码解释**：为10901提供更详细的用户友好提示
2. **重试策略优化**：当前540ms重试间隔可能过短
3. **状态同步机制**：解锁失败后同步车辆最新状态

---

## 📊 相关组件

**核心类：**
- `XPBlePollingHandlerV2` - polling决策引擎
- `XPBlePollingService` - BLE polling服务门面
- `BLEConnection` - BLE指令发送流程

**配置数据：**
- `leftCertCount: 359` - BLE认证令牌计数
- `polling.tBox4GState: 0` - 车辆polling状态

**关键日志标签：**
- `polling_action_unlock`, `PollingUnlock`, `carControlResult`

---

## 🏷️ 知识归档

**错误模式：** BLE polling解锁指令车辆端拒绝（错误码10901）
**设计影响：** 车辆端状态机或安全策略可能需要调整
**未解决问题：** 错误码10901的具体业务含义需要车辆端团队确认

---

*本报告基于日志分析生成，建议结合车辆端日志进一步确认根因。*