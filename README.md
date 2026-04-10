# Traccar 火星版 - Home Assistant Traccar 服务器集成（中国定制版）

一个为 Home Assistant 提供的 Traccar 服务器集成，支持实时设备跟踪、传感器监控和事件响应。  
**特别针对中国地区优化**：自动将 GCJ-02（火星坐标）转换为 WGS84 坐标，可直接用于 Home Assistant 区域判断。

> **注意**：
-  本版本Fork自 https://github.com/MagicStarTrace/ha_traccar 
-  由于其版本登录错误，基于原版改进登录方式（TOKEN)，并将集成名称改为 **Traccar 火星版**，支持 API Token 认证（推荐）。

## 🚀 主要改进

- ✅ **集成名称改为“Traccar 火星版”**，更符合中国用户习惯
- ✅ **新增 WGS84 坐标跟踪器**：自动将 GCJ-02 坐标转换为 WGS84，可直接用于区域（Zone）判断
- ✅ **支持 API Token 认证**（官方推荐，无需修改库，兼容性最好）

## 功能特性

### 🚗 实时设备跟踪
- GPS 定位跟踪，实时更新设备位置
- **双坐标系统**：同时提供 GCJ-02（原始）和 WGS84（转换后）坐标
- **智能坐标转换**：自动检测中国境内坐标并转换，境外保持原样
- 位置准确性监控（GPS 精度）
- 地址反向解析

### 📊 丰富的传感器支持
- 电池电量（百分比）
- 充电状态检测
- 运动检测
- 在线/离线状态
- 速度（km/h）、海拔（m）、行驶方向（°）
- 温度、总里程（需设备支持）

### 🌍 地理围栏
- 自动检测进出地理围栏
- 支持多个围栏同时监控

### ⚡ 实时事件
- WebSocket 连接，即时推送设备状态变化
- 支持上线/离线、移动/停止、围栏进出、超速、点火、报警等事件

## 支持的实体

每个设备自动创建以下实体（以设备名 `MyCar` 为例）：

| 实体类型 | 实体 ID | 名称 | 说明 |
|---------|--------|------|------|
| 设备跟踪器 | `device_tracker.mycar` | MyCar | 标准 GCJ-02 坐标 |
| 设备跟踪器 | `device_tracker.mycar_wgs84` | MyCar WGS84 | **转换后的 WGS84 坐标**，可用于区域判断 |
| 传感器 | `sensor.mycar_battery` | 电池 | 电量百分比 |
| 传感器 | `sensor.mycar_speed` | 速度 | km/h |
| 传感器 | `sensor.mycar_altitude` | 海拔 | 米 |
| 传感器 | `sensor.mycar_course` | 方向 | 度 |
| 传感器 | `sensor.mycar_address` | 地址 | 当前位置地址 |
| 传感器 | `sensor.mycar_geofence` | 地理围栏 | 当前围栏名称 |
| 二进制传感器 | `binary_sensor.mycar_motion` | 运动 | 是否移动 |
| 二进制传感器 | `binary_sensor.mycar_status` | 在线 | 设备在线状态 |
| 二进制传感器 | `binary_sensor.mycar_charging` | 充电 | 充电状态 |

## 安装方法

### 通过 HACS 安装（推荐）

1. 在 HACS 中添加自定义存储库：https://github.com/lambilly/ha_traccar/
2. 搜索并安装 **Traccar 火星版**
3. 重启 Home Assistant

### 手动安装

1. 下载最新源码
2. 将 `ha_traccar` 文件夹复制到 `custom_components` 目录
3. 重启 Home Assistant

## 配置方法

### 推荐方式：使用 API Token（最稳定）

1. 登录 Traccar Web 界面 → 设置 → 个人 → **API Token** → 生成一个 token（建议永不过期）
2. 在 Home Assistant 中添加集成：
- 主机：Traccar 服务器地址
- 端口：默认 8082
- **API Token**：粘贴生成的 token
- SSL 和验证按需勾选

## 高级选项
### 在集成配置页面的 选项 中可以设置：
1. 最大精度：过滤精度低于指定值的位置数据（米）
2. 跳过精度过滤的属性：某些属性不受精度过滤影响
3. 自定义属性：添加设备或位置中的自定义属性
4. 事件：选择需要在 Home Assistant 中触发的事件类型

### 坐标转换说明
1. GCJ-02（火星坐标）：中国境内使用的加密坐标系统（高德、腾讯地图）
2. WGS84：国际通用 GPS 坐标系统（Google 地图、Home Assistant 区域）
3. 转换逻辑：自动判断是否在中国境内，境内自动转换，境外保持原样
4. WGS84 实体：device_tracker.{设备名}_wgs84 的经纬度已转换，可直接用于 Zone 触发

## 兼容性
1. Traccar 服务器：5.x 及以上（推荐使用支持 API Token 的版本）
2. 推荐 Docker 镜像：bg6rsh/traccar-amap:5.8（已测试）
3. Home Assistant：2023.0.0 及以上

## 贡献与许可
- 项目地址：https://github.com/lambilly/ha_traccar
- 原项目地址：https://github.com/MagicStarTrace/ha_traccar

## 采用 MIT 许可证

### 如果此集成对您有帮助，请给项目一个 ⭐ Star ！
