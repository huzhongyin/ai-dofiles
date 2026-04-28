# Submodule 精修 — constitution + CLAUDE.md + critical_constraints

## Context

6 个 submodule 的 constitution.md 和 CLAUDE.md 已在之前的 spec-coding-scaffold 过程中生成，内容质量较高。本轮精修聚焦：
1. deps.yml 补充 `critical_constraints` 和 `trigger_keywords` 字段（当前全部缺失）
2. Constitution 和 CLAUDE.md 细节对齐（版本号更新、minor 措辞调整）

## Tasks

### Task 1: 补充 deps.yml critical_constraints（6 个 submodule）

对每个 submodule 的 deps.yml，补充 trigger_keywords 和 critical_constraints：

**XPVehicleSDK** deps.yml:
- XPBLEDataProcessor: trigger_keywords [BLE, 蓝牙, 字节流, 数据解析], constraints → constitution.md#禁止事项
- XPMQTTLibrary: trigger_keywords [MQTT, 远程, 长连接], constraints → constitution.md#禁止事项
- XPCarControlCore: trigger_keywords [车控业务, 数字钥匙, 自动泊车], constraints → constitution.md#架构约束

**XPCarControlCore** deps.yml:
- XPMQTTLibrary: trigger_keywords [MQTT, 远程指令], constraints → constitution.md#禁止事项
- XPVehicleExt: trigger_keywords [车钥匙, BLEKey, 文件传输], constraints → constitution.md#依赖边界
- XPVehicleSDK: trigger_keywords [车控, BLE, 指令下发], constraints → constitution.md#车控指令流程 + #蓝牙安全

**XPCarBusiCH** deps.yml:
- XPCarControlCore: trigger_keywords [车控, 首页, 演示], constraints → constitution.md#架构约束

**XPMQTTLibrary** deps.yml:
- XPVehicleSDK: trigger_keywords [车控, 连接, 通道], constraints → constitution.md#依赖边界

**XPPollingSDK** deps.yml:
- XPVehicleSDK: trigger_keywords [轮询, 车态, RSSI], constraints → constitution.md#依赖边界

**XPVehicleExt** deps.yml:
- XPVehicleSDK: trigger_keywords [车控, BLE, 连接], constraints → constitution.md#禁止事项

**XPBLEDataProcessor** deps.yml:
- 无 depends_on（叶子模块），无需补充

### Task 2: Constitution 细节校准（minor）

快速扫描 6 个 constitution，确认：
- 版本号是否与 podspec 一致（XPCarControlCore 5.8.0, XPPollingSDK 3.1.0 等）
- 架构描述是否与实际代码结构匹配
- 禁止事项是否完整

### Task 3: 验证 + 提交

- 运行 deps-yml-lint.sh 确认无回归
- 各 submodule 内单独 git commit
- 主工程 spec-architecture-lint.sh 通过

## 文件列表
- `submodule/XPVehicleSDK/.ai-knowledge/deps.yml`
- `submodule/XPCarControlCore/.ai-knowledge/deps.yml`
- `submodule/XPCarBusiCH/.ai-knowledge/deps.yml`
- `submodule/XPMQTTLibrary/.ai-knowledge/deps.yml`
- `submodule/XPPollingSDK/.ai-knowledge/deps.yml`
- `submodule/XPVehicleExt/.ai-knowledge/deps.yml`
