/**
 * RPLIDAR雷达可视化模块
 * 
 * 使用方法：
 * 1. 引入Socket.IO: <script src="https://cdn.socket.io/4.5.4/socket.io.min.js"></script>
 * 2. 引入本模块: <script src="/static/rplidar-widget.js"></script>
 * 3. 创建容器: <div id="radar-container"></div>
 * 4. 初始化: const radar = new RPLidarWidget('radar-container', { ... });
 * 
 * @version 1.0.0
 * @author RPLIDAR Team
 */

class RPLidarWidget {
    /**
     * 创建雷达可视化组件
     * 
     * @param {string} containerId - 容器元素ID
     * @param {Object} options - 配置选项
     * @param {number} options.maxDistance - 最大显示距离（米），默认12
     * @param {number} options.width - Canvas宽度，默认650
     * @param {number} options.height - Canvas高度，默认650
     * @param {string} options.socketUrl - WebSocket服务器地址，默认当前地址
     * @param {boolean} options.showStats - 是否显示统计信息，默认true
     * @param {string} options.title - 标题文字，默认"RPLIDAR C1 实时扫描"
     * @param {string} options.pointColor - 数据点颜色，默认'rgba(255, 0, 0, 0.7)'
     * @param {number} options.pointSize - 数据点大小，默认2.5
     */
    constructor(containerId, options = {}) {
        // 配置参数
        this.options = {
            maxDistance: options.maxDistance || 12,
            width: options.width || 650,
            height: options.height || 650,
            socketUrl: options.socketUrl || '',
            showStats: options.showStats !== undefined ? options.showStats : true,
            title: options.title || 'RPLIDAR C1 实时扫描',
            pointColor: options.pointColor || 'rgba(255, 0, 0, 0.7)',
            pointSize: options.pointSize || 2.5,
            gridColor: options.gridColor || '#ddd',
            textColor: options.textColor || '#333',
            centerColor: options.centerColor || '#ff0000'
        };
        
        // 获取容器
        this.container = document.getElementById(containerId);
        if (!this.container) {
            throw new Error(`Container with id "${containerId}" not found`);
        }
        
        // 数据存储
        this.radarData = [];
        this.pendingUpdate = false;
        this.stats = null;
        
        // 初始化
        this._createElements();
        this._setupCanvas();
        this._connectWebSocket();
        this._startRendering();
    }
    
    /**
     * 创建DOM元素
     * @private
     */
    _createElements() {
        this.container.style.position = 'relative';
        this.container.style.display = 'flex';
        this.container.style.flexDirection = 'column';
        this.container.style.alignItems = 'center';
        
        // 创建Canvas
        this.canvas = document.createElement('canvas');
        this.canvas.width = this.options.width;
        this.canvas.height = this.options.height;
        this.canvas.style.border = '1px solid #ddd';
        this.canvas.style.borderRadius = '10px';
        this.canvas.style.background = '#fff';
        this.container.appendChild(this.canvas);
        
        // 创建统计信息面板（如果启用）
        if (this.options.showStats) {
            this.statsPanel = document.createElement('div');
            this.statsPanel.style.cssText = `
                margin-top: 15px;
                padding: 15px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border-radius: 10px;
                font-family: Arial, sans-serif;
                min-width: 400px;
                box-shadow: 0 5px 15px rgba(0,0,0,0.2);
            `;
            this.statsPanel.innerHTML = `
                <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; font-size: 12px;">
                    <div>
                        <div style="opacity: 0.8;">数据点数</div>
                        <div id="${containerId}-total-points" style="font-size: 18px; font-weight: bold;">0</div>
                    </div>
                    <div>
                        <div style="opacity: 0.8;">平均距离</div>
                        <div id="${containerId}-avg-distance" style="font-size: 18px; font-weight: bold;">0.00m</div>
                    </div>
                    <div>
                        <div style="opacity: 0.8;">运行时间</div>
                        <div id="${containerId}-uptime" style="font-size: 18px; font-weight: bold;">0s</div>
                    </div>
                </div>
            `;
            this.container.appendChild(this.statsPanel);
        }
    }
    
    /**
     * 设置Canvas参数
     * @private
     */
    _setupCanvas() {
        this.ctx = this.canvas.getContext('2d');
        this.centerX = this.canvas.width / 2;
        this.centerY = this.canvas.height / 2;
        this.radius = Math.min(this.centerX, this.centerY) - 50;
        
        // 初始绘制
        this._drawPolarGrid();
    }
    
    /**
     * 绘制极坐标网格
     * @private
     */
    _drawPolarGrid() {
        const ctx = this.ctx;
        ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        ctx.imageSmoothingEnabled = true;
        
        // 绘制标题
        ctx.fillStyle = this.options.textColor;
        ctx.font = 'bold 18px "Microsoft YaHei", "SimHei", Arial, sans-serif';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(this.options.title, this.centerX, 25);
        
        // 绘制同心圆
        ctx.strokeStyle = this.options.gridColor;
        ctx.lineWidth = 1;
        ctx.fillStyle = '#666';
        ctx.font = '12px Arial, sans-serif';
        ctx.textAlign = 'left';
        ctx.textBaseline = 'middle';
        
        const maxDist = this.options.maxDistance;
        const circleCount = Math.min(maxDist, 12);
        const step = maxDist <= 6 ? 1 : 2;
        
        for (let dist = step; dist <= circleCount; dist += step) {
            const r = (dist / maxDist) * this.radius;
            ctx.beginPath();
            ctx.arc(this.centerX, this.centerY, r, 0, Math.PI * 2);
            ctx.stroke();
            ctx.fillText(dist.toString(), this.centerX + r + 8, this.centerY);
        }
        
        // 绘制角度线
        ctx.strokeStyle = this.options.gridColor;
        ctx.fillStyle = this.options.textColor;
        ctx.font = '13px Arial, sans-serif';
        
        const angles = [0, 45, 90, 135, 180, 225, 270, 315];
        const labels = ['0°', '45°', '90°', '135°', '180°', '225°', '270°', '315°'];
        
        angles.forEach((angle, index) => {
            const rad = (angle - 90) * Math.PI / 180;
            const x = this.centerX + Math.cos(rad) * this.radius;
            const y = this.centerY + Math.sin(rad) * this.radius;
            
            ctx.beginPath();
            ctx.moveTo(this.centerX, this.centerY);
            ctx.lineTo(x, y);
            ctx.stroke();
            
            const labelX = this.centerX + Math.cos(rad) * (this.radius + 25);
            const labelY = this.centerY + Math.sin(rad) * (this.radius + 25);
            
            if (angle === 0 || angle === 180) {
                ctx.textAlign = 'center';
            } else if (angle > 0 && angle < 180) {
                ctx.textAlign = 'left';
            } else {
                ctx.textAlign = 'right';
            }
            
            if (angle === 90 || angle === 270) {
                ctx.textBaseline = 'middle';
            } else if (angle > 90 && angle < 270) {
                ctx.textBaseline = 'top';
            } else {
                ctx.textBaseline = 'bottom';
            }
            
            ctx.fillText(labels[index], labelX, labelY);
        });
        
        // 绘制中心点
        ctx.fillStyle = this.options.centerColor;
        ctx.beginPath();
        ctx.arc(this.centerX, this.centerY, 4, 0, Math.PI * 2);
        ctx.fill();
    }
    
    /**
     * 绘制雷达数据点
     * @private
     */
    _drawRadarPoints(points) {
        const ctx = this.ctx;
        ctx.fillStyle = this.options.pointColor;
        
        points.forEach(point => {
            const angle = point.angle;
            const distance = point.distance;
            
            const rad = (angle - 90) * Math.PI / 180;
            const r = (distance / this.options.maxDistance) * this.radius;
            const x = this.centerX + Math.cos(rad) * r;
            const y = this.centerY + Math.sin(rad) * r;
            
            ctx.beginPath();
            ctx.arc(x, y, this.options.pointSize, 0, Math.PI * 2);
            ctx.fill();
        });
    }
    
    /**
     * 连接WebSocket
     * @private
     */
    _connectWebSocket() {
        if (typeof io === 'undefined') {
            console.error('Socket.IO not loaded. Please include socket.io.min.js');
            return;
        }
        
        this.socket = io(this.options.socketUrl);
        
        this.socket.on('connect', () => {
            console.log('[RPLidar] WebSocket connected');
            this._onConnect();
        });
        
        this.socket.on('disconnect', () => {
            console.log('[RPLidar] WebSocket disconnected');
            this._onDisconnect();
        });
        
        this.socket.on('init_data', (data) => {
            this.radarData = data.points;
            this._requestUpdate();
        });
        
        this.socket.on('scan_data_full', (data) => {
            this.radarData = data.points;
            this._requestUpdate();
        });
        
        this.socket.on('statistics', (stats) => {
            this.stats = stats;
            this._updateStats();
        });
    }
    
    /**
     * 连接成功回调
     * @private
     */
    _onConnect() {
        if (this.options.onConnect) {
            this.options.onConnect();
        }
    }
    
    /**
     * 断开连接回调
     * @private
     */
    _onDisconnect() {
        if (this.options.onDisconnect) {
            this.options.onDisconnect();
        }
    }
    
    /**
     * 请求更新
     * @private
     */
    _requestUpdate() {
        if (!this.pendingUpdate) {
            this.pendingUpdate = true;
            requestAnimationFrame(() => this._update());
        }
    }
    
    /**
     * 更新显示
     * @private
     */
    _update() {
        this.pendingUpdate = false;
        this._drawPolarGrid();
        this._drawRadarPoints(this.radarData);
    }
    
    /**
     * 更新统计信息
     * @private
     */
    _updateStats() {
        if (!this.options.showStats || !this.stats) return;
        
        const containerId = this.container.id;
        const totalPointsEl = document.getElementById(`${containerId}-total-points`);
        const avgDistanceEl = document.getElementById(`${containerId}-avg-distance`);
        const uptimeEl = document.getElementById(`${containerId}-uptime`);
        
        if (totalPointsEl) {
            totalPointsEl.textContent = this.stats.total_points.toLocaleString();
        }
        
        if (avgDistanceEl) {
            avgDistanceEl.textContent = this.stats.avg_distance.toFixed(3) + 'm';
        }
        
        if (uptimeEl) {
            const uptime = Math.floor(this.stats.uptime);
            const hours = Math.floor(uptime / 3600);
            const minutes = Math.floor((uptime % 3600) / 60);
            const seconds = uptime % 60;
            
            let uptimeStr = '';
            if (hours > 0) {
                uptimeStr = `${hours}h ${minutes}m ${seconds}s`;
            } else if (minutes > 0) {
                uptimeStr = `${minutes}m ${seconds}s`;
            } else {
                uptimeStr = `${seconds}s`;
            }
            
            uptimeEl.textContent = uptimeStr;
        }
    }
    
    /**
     * 启动渲染循环
     * @private
     */
    _startRendering() {
        // 初始绘制
        this._drawPolarGrid();
    }
    
    /**
     * 销毁组件
     */
    destroy() {
        if (this.socket) {
            this.socket.disconnect();
        }
        this.container.innerHTML = '';
    }
    
    /**
     * 更新配置
     * @param {Object} options - 新的配置选项
     */
    updateOptions(options) {
        Object.assign(this.options, options);
        this._drawPolarGrid();
        this._drawRadarPoints(this.radarData);
    }
}

// 导出到全局
if (typeof window !== 'undefined') {
    window.RPLidarWidget = RPLidarWidget;
}

