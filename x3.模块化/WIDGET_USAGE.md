# RPLidar Widget 模块使用说明

## 📦 简介

RPLidar Widget 是一个独立的JavaScript模块，可以轻松地将RPLIDAR雷达可视化功能集成到任何网页中。

## ✨ 特性

- 🎯 **即插即用**：只需几行代码即可集成
- 🎨 **高度可定制**：支持自定义颜色、大小、样式
- 📊 **实时统计**：可选的统计信息面板
- 🔌 **WebSocket支持**：自动连接和重连
- 📱 **响应式设计**：支持移动端显示
- 🚀 **高性能**：使用Canvas 2D和requestAnimationFrame优化

## 🚀 快速开始

### 1. 基础使用

```html
<!DOCTYPE html>
<html>
<head>
    <title>雷达示例</title>
</head>
<body>
    <!-- 容器 -->
    <div id="my-radar"></div>

    <!-- 引入Socket.IO -->
    <script src="https://cdn.socket.io/4.5.4/socket.io.min.js"></script>
    
    <!-- 引入RPLidar模块 -->
    <script src="/static/rplidar-widget.js"></script>
    
    <!-- 初始化 -->
    <script>
        const radar = new RPLidarWidget('my-radar', {
            maxDistance: 12,
            showStats: true
        });
    </script>
</body>
</html>
```

### 2. 完整配置示例

```javascript
const radar = new RPLidarWidget('container-id', {
    // 基础配置
    maxDistance: 12,              // 最大显示距离（米）
    width: 650,                   // Canvas宽度（像素）
    height: 650,                  // Canvas高度（像素）
    socketUrl: '',                // WebSocket服务器地址（空字符串=当前地址）
    
    // 显示配置
    showStats: true,              // 是否显示统计信息
    title: 'RPLIDAR C1 实时扫描', // 标题文字
    
    // 样式配置
    pointColor: 'rgba(255, 0, 0, 0.7)',  // 数据点颜色
    pointSize: 2.5,                       // 数据点大小
    gridColor: '#ddd',                    // 网格颜色
    textColor: '#333',                    // 文字颜色
    centerColor: '#ff0000',               // 中心点颜色
    
    // 回调函数
    onConnect: function() {
        console.log('雷达已连接');
    },
    onDisconnect: function() {
        console.log('雷达已断开');
    }
});
```

## 📖 API文档

### 构造函数

```javascript
new RPLidarWidget(containerId, options)
```

**参数**：
- `containerId` (string): 容器元素的ID
- `options` (Object): 配置选项（见上方完整配置）

### 方法

#### updateOptions(options)

动态更新配置。

```javascript
radar.updateOptions({
    maxDistance: 6,
    pointColor: 'rgba(0, 255, 0, 0.7)'
});
```

#### destroy()

销毁组件，断开WebSocket连接，清空DOM。

```javascript
radar.destroy();
```

## 🎨 样式自定义

### 方法1：使用内置配置

```javascript
const radar = new RPLidarWidget('radar', {
    pointColor: 'rgba(0, 255, 0, 0.7)',  // 绿色数据点
    gridColor: '#cccccc',                 // 浅灰色网格
    textColor: '#000000'                  // 黑色文字
});
```

### 方法2：使用CSS（可选）

```html
<link rel="stylesheet" href="/static/rplidar-widget.css">
```

然后自定义样式：

```css
.rplidar-container {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}
```

## 📊 高级用法

### 多雷达显示

```html
<div id="radar-1"></div>
<div id="radar-2"></div>

<script>
    // 主雷达
    const radar1 = new RPLidarWidget('radar-1', {
        maxDistance: 12,
        title: '主雷达'
    });
    
    // 辅助雷达
    const radar2 = new RPLidarWidget('radar-2', {
        maxDistance: 6,
        width: 400,
        height: 400,
        title: '辅助雷达',
        pointColor: 'rgba(0, 255, 0, 0.7)'
    });
</script>
```

### 动态控制

```javascript
// 改变显示距离
document.getElementById('distance-slider').addEventListener('input', function(e) {
    radar.updateOptions({ maxDistance: parseInt(e.target.value) });
});

// 改变颜色
function changeColor(color) {
    radar.updateOptions({ pointColor: color });
}

// 切换统计显示（需要重新创建组件）
```

### 嵌入到其他框架

#### React示例

```jsx
import React, { useEffect, useRef } from 'react';

function RadarComponent() {
    const containerRef = useRef(null);
    const radarRef = useRef(null);
    
    useEffect(() => {
        // 创建雷达
        radarRef.current = new window.RPLidarWidget(containerRef.current.id, {
            maxDistance: 12,
            showStats: true
        });
        
        // 清理
        return () => {
            if (radarRef.current) {
                radarRef.current.destroy();
            }
        };
    }, []);
    
    return <div id="radar-container" ref={containerRef}></div>;
}
```

#### Vue示例

```vue
<template>
    <div id="radar-container"></div>
</template>

<script>
export default {
    data() {
        return {
            radar: null
        };
    },
    mounted() {
        this.radar = new window.RPLidarWidget('radar-container', {
            maxDistance: 12,
            showStats: true
        });
    },
    beforeDestroy() {
        if (this.radar) {
            this.radar.destroy();
        }
    }
}
</script>
```

## 🔧 配置选项详解

| 选项 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `maxDistance` | number | 12 | 最大显示距离（米） |
| `width` | number | 650 | Canvas宽度（像素） |
| `height` | number | 650 | Canvas高度（像素） |
| `socketUrl` | string | '' | WebSocket服务器URL |
| `showStats` | boolean | true | 是否显示统计信息 |
| `title` | string | 'RPLIDAR C1 实时扫描' | 标题文字 |
| `pointColor` | string | 'rgba(255, 0, 0, 0.7)' | 数据点颜色 |
| `pointSize` | number | 2.5 | 数据点大小 |
| `gridColor` | string | '#ddd' | 网格线颜色 |
| `textColor` | string | '#333' | 文字颜色 |
| `centerColor` | string | '#ff0000' | 中心点颜色 |
| `onConnect` | function | null | 连接成功回调 |
| `onDisconnect` | function | null | 断开连接回调 |

## 📡 WebSocket事件

模块会自动监听以下WebSocket事件：

| 事件 | 数据格式 | 说明 |
|------|---------|------|
| `connect` | - | 连接成功 |
| `disconnect` | - | 连接断开 |
| `init_data` | `{points: [...]}` | 初始化数据 |
| `scan_data_full` | `{points: [...]}` | 全量扫描数据 |
| `statistics` | `{total_points, avg_distance, ...}` | 统计信息 |

数据点格式：
```javascript
{
    angle: 90.5,      // 角度（度）
    distance: 1.234,  // 距离（米）
    quality: 45       // 质量值（0-63）
}
```

## 🎯 示例页面

### 基础示例
访问：`http://localhost:5000/`

### 高级示例
访问：`http://localhost:5000/advanced`

## 🐛 故障排除

### 问题1：雷达不显示

**解决方案**：
1. 确认Socket.IO已正确加载
2. 检查容器ID是否正确
3. 打开浏览器控制台查看错误信息

### 问题2：数据不更新

**解决方案**：
1. 检查WebSocket连接状态
2. 确认服务器正在运行
3. 查看控制台网络请求

### 问题3：样式不正确

**解决方案**：
1. 检查CSS文件路径
2. 使用浏览器开发工具检查元素样式
3. 尝试直接使用内联样式

## 📄 许可证

本项目仅供学习和研究使用。

---

**版本**：1.0.0  
**更新日期**：2025-10-28  
**作者**：RPLIDAR Team

