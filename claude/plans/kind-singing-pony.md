# 并发安全优化：NSLock 替代 DispatchSemaphore

## Context

CarKeySessionAccesser 使用 `DispatchSemaphore(value: 1)` 作为互斥锁保护 `state` 属性。在 Swift Concurrency 的 Task.detached 上下文中，`semaphore.wait()` 会阻塞协作线程池的线程，可能导致线程饥饿或死锁，这也可能是线上 `EXC_BAD_ACCESS` 崩溃的间接原因。

## 方案

将 `DispatchSemaphore(value: 1)` 替换为 `NSLock`（或 `os_unfair_lock` 的封装），用 `lock()/unlock()` 替代 `wait()/signal()`。

### 为什么选 NSLock 而不是 os_unfair_lock

- `NSLock` 是 Foundation 类型，语义与当前 semaphore 一致
- 比 `os_unfair_lock` 更易用（不需要处理 C 指针语义），在非高频竞争场景性能足够
- `os_unfair_lock` 在 Swift 中使用有坑（struct 值语义 + 可能被 copy），需要封装为 class

### 修改文件

**`CarKeySessionAccesser.swift`**

1. `let semaphore = DispatchSemaphore(value: 1)` → `let lock = NSLock()`
2. `state` getter: `semaphore.wait()/signal()` → `lock.lock()/unlock()`
3. `state` setter: `semaphore.wait()/signal()` → `lock.lock()/unlock()`
4. 确保 setter 中所有路径都能 unlock（当前代码用 guard + return，需要在 return 前 signal → 改为 unlock）

**`CarKeyPassManager.swift`**

同样分析其 `semaphore` 使用情况，如果也是 DispatchSemaphore 做互斥，一并替换。

## 验证

- 编译通过
- 所有 lock/unlock 配对正确，无死锁路径
