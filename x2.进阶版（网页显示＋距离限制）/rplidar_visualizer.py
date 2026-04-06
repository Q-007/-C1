"""
RPLIDAR 数据管理模块
用于网页实时显示，移除matplotlib依赖
"""

from collections import deque
import threading
import time


class RadarDataManager:
    """雷达数据管理类（用于网页显示）"""
    
    def __init__(self, max_distance=12.0, history_size=360):
        """
        初始化数据管理器
        
        Args:
            max_distance: 最大显示距离（米）
            history_size: 保留的历史数据点数量
        """
        self.max_distance = max_distance
        self.history_size = history_size
        
        # 数据存储
        self.data_points = deque(maxlen=history_size)
        self.lock = threading.Lock()
        
        # 统计信息
        self.total_points = 0
        self.start_time = time.time()
        
    def update_data(self, angle, distance, quality):
        """
        更新数据点
        
        Args:
            angle: 角度（度）
            distance: 距离（米）
            quality: 质量值
        """
        with self.lock:
            self.data_points.append({
                'angle': angle,
                'distance': distance,
                'quality': quality,
                'timestamp': time.time()
            })
            self.total_points += 1
    
    def get_scan_data(self):
        """
        获取当前所有扫描数据（供WebSocket使用）
        
        Returns:
            list: 数据点列表
        """
        with self.lock:
            return list(self.data_points)
    
    def get_latest_point(self):
        """
        获取最新的数据点
        
        Returns:
            dict: 最新数据点，如果没有数据返回None
        """
        with self.lock:
            if len(self.data_points) > 0:
                return self.data_points[-1]
            return None
    
    def get_statistics(self):
        """
        获取统计信息
        
        Returns:
            dict: 统计信息
        """
        with self.lock:
            if len(self.data_points) == 0:
                return {
                    'total_points': self.total_points,
                    'current_points': 0,
                    'avg_distance': 0,
                    'min_distance': 0,
                    'max_distance': 0,
                    'uptime': time.time() - self.start_time
                }
            
            distances = [p['distance'] for p in self.data_points]
            return {
                'total_points': self.total_points,
                'current_points': len(self.data_points),
                'avg_distance': sum(distances) / len(distances),
                'min_distance': min(distances),
                'max_distance': max(distances),
                'uptime': time.time() - self.start_time
            }
    
    def clear(self):
        """清空所有数据"""
        with self.lock:
            self.data_points.clear()


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
