# Traccar 火星版 - Home Assistant Traccar 服务器集成（中国定制版）

[![GitHub Release](https://img.shields.io/github/v/release/lambilly/ha_traccar?style=flat-square)](https://github.com/lambilly/ha_traccar/releases)
[![GitHub License](https://img.shields.io/github/license/lambilly/ha_traccar?style=flat-square)](LICENSE)
[![HACS Custom](https://img.shields.io/badge/HACS-Custom-orange.svg?style=flat-square)](https://hacs.xyz/)

一个为 Home Assistant 提供的 Traccar 服务器集成，支持实时设备跟踪、传感器监控和事件响应。  
**特别针对中国地区优化**：自动将 GCJ-02（火星坐标）转换为 WGS84 坐标，可直接用于 Home Assistant 区域判断。

> **注意**：
> - 本版本 Fork 自 [MagicStarTrace/ha_traccar](https://github.com/MagicStarTrace/ha_traccar)
> - 修复原版登录错误，采用标准用户名/密码认证，并将集成名称改为 **Traccar 火星版**

---

## 🚀 主要改进

- ✅ **集成名称改为“Traccar 火星版”**，更符合中国用户习惯
- ✅ **新增 WGS84 坐标跟踪器**：自动将 GCJ-02 坐标转换为 WGS84，可直接用于区域（Zone）判断
- ✅ **修复登录认证问题**：使用标准用户名/密码登录，兼容 Traccar 5.x+
- ✅ **优化 WebSocket 连接稳定性**

---

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

---

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

> 注：温度、总里程等传感器仅在设备上报对应数据时自动创建。

---

## 安装方法

### 通过 HACS 安装（推荐）

1. 在 HACS 中添加自定义存储库：`https://github.com/lambilly/ha_traccar/`
2. 搜索并安装 **Traccar 火星版**
3. 重启 Home Assistant

### 手动安装

1. 下载最新源码
2. 将 `ha_traccar` 文件夹复制到 `custom_components` 目录
3. 重启 Home Assistant

---

## 配置方法

### 使用用户名和密码登录

1. 在 Home Assistant 中添加集成，搜索 **Traccar 火星版**
2. 填写以下信息：
   - **主机**：Traccar 服务器地址（例如 `192.168.1.100`）
   - **端口**：默认 `8082`
   - **用户名**：Traccar 账号邮箱
   - **密码**：Traccar 账号密码
   - **启用 SSL**：根据服务器配置勾选（`https://`）
   - **验证 SSL 证书**：自签名证书可取消勾选
3. 提交后，集成将自动发现设备并创建实体

### 高级选项

在集成配置页面的「选项」中可以设置：

- **最大精度**：过滤精度低于指定值的位置数据（单位：米）
- **跳过精度过滤的属性**：某些属性不受精度过滤影响
- **自定义属性**：添加设备或位置中的自定义属性
- **监控事件**：选择需要在 Home Assistant 中触发的事件类型

---

## 坐标转换说明

| 坐标系 | 说明 | 使用场景 |
|--------|------|----------|
| **GCJ-02** | 中国境内使用的加密坐标系统（高德地图、腾讯地图） | 原始上报数据 |
| **WGS84** | 国际通用 GPS 坐标系统（Google 地图、Home Assistant 区域） | 转换后数据 |

- **转换逻辑**：自动判断是否在中国境内，境内自动转换，境外保持原样
- **WGS84 实体**：`device_tracker.{设备名}_wgs84` 的经纬度已转换，可直接用于 Zone 触发

---

## 兼容性

- **Traccar 服务器**：5.x 及以上
- **推荐 Docker 镜像**：[bg6rsh/traccar-amap:6.11](https://hub.docker.com/r/bg6rsh/traccar-amap)（已测试，内置高德地图适配）
- **Home Assistant**：2023.0.0 及以上

---

## 常见问题

### 1. 为什么有两个设备跟踪器？
- 原始跟踪器保留 GCJ-02 坐标，用于地图显示（如高德地图）
- WGS84 跟踪器提供转换后的坐标，用于 Home Assistant 的区域（Zone）自动化

### 2. 登录失败怎么办？
- 确认用户名/密码正确，且账号具有 API 访问权限（默认管理员账号即可）
- 检查 Traccar 服务器日志，查看具体拒绝原因
- 尝试在浏览器中访问 `http://服务器:8082/api/devices`，输入相同账号密码测试

### 3. 事件如何在自动化中使用？
- 事件名称格式：`traccar_{事件类型}`（例如 `traccar_device_moving`）
- 可在「开发者工具 → 事件」中监听查看具体数据

### 4. 坐标转换不生效？
- 确保设备上报的坐标在中国境内（境外不转换）
- 检查日志是否有转换相关错误

---

## 贡献与许可

- **项目地址**：[https://github.com/lambilly/ha_traccar](https://github.com/lambilly/ha_traccar)
- **原项目地址**：[https://github.com/MagicStarTrace/ha_traccar](https://github.com/MagicStarTrace/ha_traccar)
- **采用 MIT 许可证**

如果此集成对您有帮助，请给项目一个 ⭐ Star！
