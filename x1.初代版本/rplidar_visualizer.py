"""
RPLIDAR 实时可视化模块
使用matplotlib实现极坐标图显示
"""

import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np
from collections import deque
import threading

class RadarVisualizer:
    """雷达数据可视化类"""
    
    def __init__(self, max_distance=12.0, history_size=360):
        """
        初始化可视化
        
        Args:
            max_distance: 最大显示距离（米）
            history_size: 保留的历史数据点数量
        """
        self.max_distance = max_distance
        self.history_size = history_size
        
        # 数据存储
        self.angles = deque(maxlen=history_size)
        self.distances = deque(maxlen=history_size)
        self.lock = threading.Lock()
        
        # 创建图形
        self.fig = plt.figure(figsize=(10, 10))
        self.ax = self.fig.add_subplot(111, projection='polar')
        
        # 设置极坐标图
        self.ax.set_ylim(0, max_distance)
        self.ax.set_theta_zero_location('N')  # 0度在正上方
        self.ax.set_theta_direction(-1)  # 顺时针
        self.ax.set_title('RPLIDAR C1 实时扫描', fontproperties='SimHei', fontsize=14, pad=20)
        self.ax.grid(True)
        
        # 初始化散点图
        self.scatter = self.ax.scatter([], [], c='red', s=5, alpha=0.6)
        
        # 状态标签
        self.status_text = self.fig.text(0.02, 0.02, '', fontsize=10, 
                                         fontproperties='SimHei',
                                         verticalalignment='bottom')
        
        self.animation = None
        self.is_running = False
        
    def update_data(self, angle, distance):
        """
        更新数据点
        
        Args:
            angle: 角度（度）
            distance: 距离（米）
        """
        with self.lock:
            # 转换角度到弧度
            angle_rad = np.deg2rad(angle)
            self.angles.append(angle_rad)
            self.distances.append(distance)
    
    def _update_plot(self, frame):
        """更新绘图（动画回调函数）"""
        with self.lock:
            if len(self.angles) > 0:
                # 转换为numpy数组
                angles_array = np.array(self.angles)
                distances_array = np.array(self.distances)
                
                # 更新散点图
                self.scatter.set_offsets(np.c_[angles_array, distances_array])
                
                # 更新状态文本
                num_points = len(self.angles)
                avg_distance = np.mean(distances_array) if num_points > 0 else 0
                self.status_text.set_text(
                    f'数据点: {num_points} | 平均距离: {avg_distance:.2f}m'
                )
        
        return [self.scatter, self.status_text]
    
    def start(self, interval=50):
        """
        启动可视化
        
        Args:
            interval: 更新间隔（毫秒）
        """
        self.is_running = True
        
        # 创建动画（极坐标图不支持blit=True）
        self.animation = animation.FuncAnimation(
            self.fig, 
            self._update_plot,
            interval=interval,
            blit=False,
            cache_frame_data=False
        )
        
        print("可视化窗口已启动")
        plt.show()
    
    def close(self):
        """关闭可视化窗口"""
        self.is_running = False
        if self.animation:
            self.animation.event_source.stop()
        plt.close(self.fig)
        print("可视化窗口已关闭")


class TerminalPrinter:
    """终端打印类"""
    
    def __init__(self, print_interval=100):
        """
        初始化终端打印
        
        Args:
            print_interval: 打印间隔（每N个点打印一次）
        """
        self.print_interval = print_interval
        self.count = 0
        self.total_points = 0
        
    def print_point(self, angle, distance, quality):
        """
        打印数据点
        
        Args:
            angle: 角度（度）
            distance: 距离（米）
            quality: 质量值
        """
        self.count += 1
        self.total_points += 1
        
        # 每隔一定数量打印一次
        if self.count >= self.print_interval:
            print(f"[{self.total_points:6d}] 角度: {angle:6.2f}° | "
                  f"距离: {distance:6.3f}m | 质量: {quality:3d}")
            self.count = 0
    
    def print_summary(self):
        """打印统计信息"""
        print(f"\n总共接收数据点: {self.total_points}")

