"""
RPLIDAR C1 主程序（网页版）
整合驱动和网页显示，实现完整的雷达数据采集和网页可视化
"""

import threading
import signal
import sys
import time
from flask import Flask, render_template
from flask_socketio import SocketIO, emit
from rplidar_c1_driver import RPLidarC1
from rplidar_visualizer import RadarDataManager, TerminalPrinter


# 创建Flask应用
app = Flask(__name__)
app.config['SECRET_KEY'] = 'rplidar_c1_secret_key'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')


class RadarApplication:
    """雷达应用主类（网页版）"""
    
    def __init__(self, port=None, baudrate=None):
        """
        初始化应用
        
        Args:
            port: 串口号，None则自动检测
            baudrate: 波特率，None则自动检测
        """
        self.port = port
        self.baudrate = baudrate
        
        # 创建组件（自动检测模式）
        self.lidar = RPLidarC1(port=port, baudrate=baudrate)
        self.data_manager = RadarDataManager(max_distance=12.0)
        self.printer = TerminalPrinter(print_interval=100)
        
        # 控制标志
        self.running = False
        self.scan_thread = None
        self.broadcast_thread = None
        
        # 注册信号处理
        signal.signal(signal.SIGINT, self._signal_handler)
    
    def _signal_handler(self, sig, frame):
        """处理Ctrl+C信号"""
        print("\n\n接收到中断信号，正在安全退出...")
        self.stop()
        sys.exit(0)
    
    def start_scanning(self):
        """启动雷达扫描"""
        # 连接雷达
        if not self.lidar.connect():
            print("无法连接雷达，程序退出")
            return False
        
        # 尝试获取设备信息（可选，失败也继续）
        try:
            self.lidar.get_info()
        except Exception as e:
            print(f"获取设备信息失败: {e}")
        
        # 尝试获取健康状态（可选，失败也继续）
        try:
            self.lidar.get_health()
        except Exception as e:
            print(f"获取健康状态失败: {e}")
        
        # 启动扫描
        self.lidar.start_scan()
        
        # 启动数据处理线程
        self.running = True
        self.scan_thread = threading.Thread(target=self._scan_loop, daemon=True)
        self.scan_thread.start()
        
        # 启动数据广播线程
        self.broadcast_thread = threading.Thread(target=self._broadcast_loop, daemon=True)
        self.broadcast_thread.start()
        
        print("\n雷达扫描已启动...")
        print("终端将每100个点打印一次数据")
        print("请在浏览器中访问 http://localhost:5000 查看实时可视化")
        print("按 Ctrl+C 停止\n")
        
        return True
    
    def _scan_loop(self):
        """扫描数据循环（在独立线程中运行）"""
        try:
            for angle, distance, quality in self.lidar.read_scan_data():
                if not self.running:
                    break
                
                # 更新数据管理器
                self.data_manager.update_data(angle, distance, quality)
                
                # 终端打印
                self.printer.print_point(angle, distance, quality)
                
        except Exception as e:
            print(f"\n数据读取错误: {e}")
            self.running = False
    
    def _broadcast_loop(self):
        """WebSocket数据广播循环（优化版：定期全量发送）"""
        last_broadcast_time = time.time()
        
        while self.running:
            current_time = time.time()
            
            # 每100ms广播一次全量数据
            if current_time - last_broadcast_time >= 0.1:
                try:
                    # 获取所有扫描数据
                    all_points = self.data_manager.get_scan_data()
                    
                    # 发送全量数据（前端会自动处理显示）
                    if all_points:
                        socketio.emit('scan_data_full', {
                            'points': [
                                {
                                    'angle': p['angle'],
                                    'distance': p['distance'],
                                    'quality': p['quality']
                                } for p in all_points
                            ]
                        }, namespace='/')
                    
                    # 每秒发送一次统计信息
                    if int(current_time) != int(last_broadcast_time):
                        stats = self.data_manager.get_statistics()
                        socketio.emit('statistics', stats, namespace='/')
                    
                    last_broadcast_time = current_time
                    
                except Exception as e:
                    print(f"广播错误: {e}")
            
            time.sleep(0.02)  # 短暂休眠，避免占用过多CPU
    
    def stop(self):
        """停止应用"""
        if not self.running:
            return
        
        print("\n正在停止...")
        self.running = False
        
        # 等待线程结束
        if self.scan_thread and self.scan_thread.is_alive():
            self.scan_thread.join(timeout=2)
        
        if self.broadcast_thread and self.broadcast_thread.is_alive():
            self.broadcast_thread.join(timeout=2)
        
        # 停止雷达
        self.lidar.stop_scan()
        
        # 打印统计
        self.printer.print_summary()
        
        # 断开连接
        self.lidar.disconnect()
        
        print("\n雷达已安全停止")


# 全局雷达应用实例
radar_app = None


@app.route('/')
def index():
    """主页路由"""
    return render_template('index.html')


@socketio.on('connect')
def handle_connect():
    """客户端连接事件"""
    print(f"客户端已连接")
    
    # 发送当前所有数据点
    if radar_app and radar_app.running:
        all_data = radar_app.data_manager.get_scan_data()
        emit('init_data', {'points': all_data})


@socketio.on('disconnect')
def handle_disconnect():
    """客户端断开事件"""
    print(f"客户端已断开")


@socketio.on('request_stats')
def handle_stats_request():
    """客户端请求统计信息"""
    if radar_app and radar_app.running:
        stats = radar_app.data_manager.get_statistics()
        emit('statistics', stats)


def main():
    """主函数"""
    global radar_app
    
    # 配置参数
    # 方式1: 自动检测（推荐）- 设置为None
    PORT = None  # 自动检测串口
    BAUDRATE = None  # 自动检测波特率
    
    # 方式2: 手动指定（如果自动检测失败）
    # PORT = 'COM10'
    # BAUDRATE = 460800
    
    print("=" * 60)
    print("RPLIDAR C1 激光雷达驱动程序（网页版）")
    print("检测距离范围：12米")
    print("=" * 60)
    
    # 创建雷达应用
    try:
        radar_app = RadarApplication(port=PORT, baudrate=BAUDRATE)
        
        # 启动雷达扫描
        if radar_app.start_scanning():
            # 启动Flask服务器
            print("\n正在启动Web服务器...")
            print("=" * 60)
            socketio.run(app, host='0.0.0.0', port=5000, debug=False, use_reloader=False)
        else:
            print("雷达启动失败")
            
    except KeyboardInterrupt:
        print("\n程序被中断")
    except Exception as e:
        print(f"\n程序异常: {e}")
        print("\n提示: 如果自动检测失败，可以在main.py中手动指定串口和波特率")
        import traceback
        traceback.print_exc()
    finally:
        if radar_app:
            radar_app.stop()


if __name__ == "__main__":
    main()
