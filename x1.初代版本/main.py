"""
RPLIDAR C1 主程序
整合驱动和可视化，实现完整的雷达数据采集和显示
"""

import threading
import signal
import sys
import time
from rplidar_c1_driver import RPLidarC1
from rplidar_visualizer import RadarVisualizer, TerminalPrinter


class RadarApplication:
    """雷达应用主类"""
    
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
        self.visualizer = RadarVisualizer(max_distance=12.0)
        self.printer = TerminalPrinter(print_interval=100)
        
        # 控制标志
        self.running = False
        self.scan_thread = None
        
        # 注册信号处理
        signal.signal(signal.SIGINT, self._signal_handler)
    
    def _signal_handler(self, sig, frame):
        """处理Ctrl+C信号"""
        print("\n\n接收到中断信号，正在安全退出...")
        self.stop()
    
    def start(self):
        """启动应用"""
        # 连接雷达
        if not self.lidar.connect():
            print("无法连接雷达，程序退出")
            return
        
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
        
        print("\n开始数据采集...")
        print("终端将每100个点打印一次数据")
        print("同时显示实时可视化窗口")
        print("按 Ctrl+C 停止\n")
        
        # 启动可视化（阻塞主线程）
        try:
            self.visualizer.start(interval=50)
        except KeyboardInterrupt:
            pass
        finally:
            self.stop()
    
    def _scan_loop(self):
        """扫描数据循环（在独立线程中运行）"""
        try:
            for angle, distance, quality in self.lidar.read_scan_data():
                if not self.running:
                    break
                
                # 更新可视化
                self.visualizer.update_data(angle, distance)
                
                # 终端打印
                self.printer.print_point(angle, distance, quality)
                
        except Exception as e:
            print(f"\n数据读取错误: {e}")
            self.running = False
    
    def stop(self):
        """停止应用"""
        if not self.running:
            return
        
        print("\n正在停止...")
        self.running = False
        
        # 等待扫描线程结束
        if self.scan_thread and self.scan_thread.is_alive():
            self.scan_thread.join(timeout=2)
        
        # 停止雷达
        self.lidar.stop_scan()
        
        # 打印统计
        self.printer.print_summary()
        
        # 断开连接
        self.lidar.disconnect()
        
        # 关闭可视化
        self.visualizer.close()
        
        print("\n程序已安全退出")
        sys.exit(0)


def main():
    """主函数"""
    # 配置参数
    # 方式1: 自动检测（推荐）- 设置为None
    PORT = None  # 自动检测串口
    BAUDRATE = None  # 自动检测波特率
    
    # 方式2: 手动指定（如果自动检测失败）
    # PORT = 'COM10'
    # BAUDRATE = 460800
    
    print("=" * 60)
    print("RPLIDAR C1 激光雷达驱动程序")
    print("=" * 60)
    
    # 创建并启动应用
    try:
        app = RadarApplication(port=PORT, baudrate=BAUDRATE)
        app.start()
    except Exception as e:
        print(f"\n程序异常: {e}")
        print("\n提示: 如果自动检测失败，可以在main.py中手动指定串口和波特率")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

