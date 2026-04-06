"""
RPLIDAR C1 驱动程序
基于RPLIDAR协议v2.8实现
"""

import serial
import serial.tools.list_ports
import struct
import time

class RPLidarC1:
    """RPLIDAR C1 激光雷达驱动类"""
    
    # 命令定义
    CMD_STOP = 0x25
    CMD_RESET = 0x40
    CMD_SCAN = 0x20
    CMD_FORCE_SCAN = 0x21
    CMD_GET_INFO = 0x50
    CMD_GET_HEALTH = 0x52
    
    # 响应类型
    RESP_MEASUREMENT = 0x81
    RESP_DESCRIPTOR = 0xA5
    
    # C1专用波特率
    SUPPORTED_BAUDRATES = [460800]  # C1固定使用460800
    
    @staticmethod
    def auto_detect():
        """
        自动检测RPLIDAR设备的串口和波特率
        
        Returns:
            (port, baudrate) 元组，如果未找到返回 (None, None)
        """
        print("\n=== 自动检测RPLIDAR设备 ===")
        
        # 列出所有可用串口
        ports = list(serial.tools.list_ports.comports())
        print(f"\n找到 {len(ports)} 个串口设备:")
        
        for port in ports:
            # 跳过蓝牙串口
            if '蓝牙' in port.description or 'Bluetooth' in port.description.upper():
                continue
            
            print(f"  - {port.device}: {port.description}")
        
        # 尝试每个串口
        for port_info in ports:
            # 跳过蓝牙设备
            if '蓝牙' in port_info.description or 'Bluetooth' in port_info.description.upper():
                continue
            
            port = port_info.device
            print(f"\n正在测试 {port}...")
            
            # 尝试不同波特率
            for baudrate in RPLidarC1.SUPPORTED_BAUDRATES:
                ser = None
                try:
                    # 尝试连接
                    ser = serial.Serial(
                        port=port,
                        baudrate=baudrate,
                        timeout=0.5,
                        parity=serial.PARITY_NONE,
                        stopbits=serial.STOPBITS_ONE,
                        bytesize=serial.EIGHTBITS
                    )
                    time.sleep(0.2)
                    ser.reset_input_buffer()
                    
                    # 发送STOP命令
                    ser.write(bytes([0xA5, 0x25]))
                    time.sleep(0.1)
                    ser.reset_input_buffer()
                    
                    # 发送SCAN命令
                    ser.write(bytes([0xA5, 0x20]))
                    time.sleep(0.2)
                    
                    # 检查响应
                    data = ser.read(20)
                    
                    # 验证是否是RPLIDAR响应（A5 5A开头）
                    if len(data) >= 7 and data[0] == 0xA5 and data[1] == 0x5A:
                        print(f"  [OK] 找到RPLIDAR! 波特率: {baudrate}")
                        print(f"    响应: {data[:7].hex()}")
                        
                        # 发送停止命令
                        ser.write(bytes([0xA5, 0x25]))
                        ser.close()
                        
                        print(f"\n=== 检测成功 ===")
                        print(f"串口: {port}")
                        print(f"波特率: {baudrate}")
                        print("=" * 40)
                        
                        return (port, baudrate)
                    
                    ser.close()
                    
                except Exception as e:
                    # 忽略连接失败，继续尝试
                    if ser and ser.is_open:
                        ser.close()
                    pass
        
        print("\n⚠ 未找到RPLIDAR设备")
        print("请检查:")
        print("  1. 雷达是否已连接")
        print("  2. USB驱动是否已安装")
        print("  3. 雷达LED是否亮起")
        return (None, None)
    
    def __init__(self, port=None, baudrate=None, timeout=1):
        """
        初始化雷达驱动
        
        Args:
            port: 串口号，None则自动检测
            baudrate: 波特率，None则自动检测
            timeout: 超时时间（秒）
        """
        # 如果未指定端口或波特率，自动检测
        if port is None or baudrate is None:
            detected_port, detected_baudrate = self.auto_detect()
            if detected_port is None:
                raise Exception("未找到RPLIDAR设备，请手动指定串口和波特率")
            
            self.port = port if port is not None else detected_port
            self.baudrate = baudrate if baudrate is not None else detected_baudrate
        else:
            self.port = port
            self.baudrate = baudrate
        
        self.timeout = timeout
        self.serial = None
        self.is_scanning = False
        
    def connect(self):
        """连接雷达"""
        try:
            self.serial = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=self.timeout,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                bytesize=serial.EIGHTBITS
            )
            time.sleep(0.5)  # 等待串口稳定
            print(f"成功连接到雷达: {self.port}, 波特率: {self.baudrate}")
            
            # 清空缓冲区
            self.serial.reset_input_buffer()
            self.serial.reset_output_buffer()
            
            return True
        except Exception as e:
            print(f"连接失败: {e}")
            return False
    
    def disconnect(self):
        """断开连接"""
        if self.is_scanning:
            self.stop_scan()
        
        if self.serial and self.serial.is_open:
            self.serial.close()
            print("雷达连接已断开")
    
    def _send_command(self, cmd, payload=None):
        """
        发送命令到雷达
        
        Args:
            cmd: 命令字节
            payload: 可选的payload数据
        """
        if not self.serial or not self.serial.is_open:
            raise Exception("串口未连接")
        
        # 构建命令：起始标志 + 命令字节
        command = bytes([0xA5, cmd])
        
        if payload:
            command += payload
        
        self.serial.write(command)
        time.sleep(0.01)  # 短暂延迟
    
    def stop_scan(self):
        """停止扫描"""
        print("停止扫描...")
        self._send_command(self.CMD_STOP)
        self.is_scanning = False
        time.sleep(0.1)
        # 清空缓冲区
        self.serial.reset_input_buffer()
    
    def start_scan(self):
        """启动标准扫描模式"""
        print("启动扫描...")
        self.serial.reset_input_buffer()
        self._send_command(self.CMD_SCAN)
        self.is_scanning = True
        time.sleep(0.2)  # 增加等待时间
        
        # 读取响应描述符（7字节）
        descriptor = self.serial.read(7)
        if len(descriptor) == 7:
            # 验证响应描述符
            if descriptor[0] == 0xA5 and descriptor[1] == 0x5A:
                data_type = descriptor[6]
                print(f"扫描已启动，数据类型: 0x{data_type:02X}")
            else:
                print(f"警告: 响应描述符格式不正确: {descriptor.hex()}")
        else:
            print(f"警告: 未收到完整的响应描述符，只收到{len(descriptor)}字节")
            # 即使没有收到响应描述符，也尝试继续（某些设备可能不返回）
            if len(descriptor) == 0:
                print("尝试直接读取扫描数据...")
    
    def get_info(self):
        """获取设备信息"""
        self.serial.reset_input_buffer()
        self._send_command(self.CMD_GET_INFO)
        time.sleep(0.2)  # 增加等待时间
        
        # 读取响应描述符（7字节）
        descriptor = self.serial.read(7)
        if len(descriptor) < 7:
            print(f"未收到设备信息响应（收到{len(descriptor)}字节）")
            self.serial.reset_input_buffer()
            return None
        
        # 读取信息数据（20字节）
        info_data = self.serial.read(20)
        if len(info_data) == 20:
            model = info_data[0]
            firmware_minor = info_data[1]
            firmware_major = info_data[2]
            hardware = info_data[3]
            serial_number = info_data[4:20].hex().upper()
            
            print(f"\n=== 设备信息 ===")
            print(f"型号: {model}")
            print(f"固件版本: {firmware_major}.{firmware_minor}")
            print(f"硬件版本: {hardware}")
            print(f"序列号: {serial_number}")
            print("================\n")
            
            return {
                'model': model,
                'firmware': f"{firmware_major}.{firmware_minor}",
                'hardware': hardware,
                'serial': serial_number
            }
        
        return None
    
    def get_health(self):
        """获取设备健康状态"""
        self.serial.reset_input_buffer()
        self._send_command(self.CMD_GET_HEALTH)
        time.sleep(0.2)  # 增加等待时间
        
        # 读取响应描述符（7字节）
        descriptor = self.serial.read(7)
        if len(descriptor) < 7:
            print(f"未收到健康状态响应（收到{len(descriptor)}字节）")
            self.serial.reset_input_buffer()
            return None
        
        # 读取健康数据（3字节）
        health_data = self.serial.read(3)
        if len(health_data) == 3:
            status = health_data[0]
            error_code = struct.unpack('<H', health_data[1:3])[0]
            
            status_text = {0: "良好", 1: "警告", 2: "错误"}.get(status, "未知")
            
            print(f"\n=== 健康状态 ===")
            print(f"状态: {status_text}")
            print(f"错误代码: {error_code}")
            print("================\n")
            
            return {'status': status, 'error_code': error_code}
        
        return None
    
    def read_scan_data(self):
        """
        读取扫描数据
        
        Returns:
            生成器，返回 (角度, 距离, 质量) 元组
        """
        if not self.is_scanning:
            raise Exception("扫描未启动")
        
        while self.is_scanning:
            # 读取一个数据包（5字节）
            data = self.serial.read(5)
            
            if len(data) < 5:
                continue
            
            # 解析数据包
            point = self._parse_scan_point(data)
            if point:
                yield point
    
    def _parse_scan_point(self, data):
        """
        解析扫描数据点（5字节标准格式）
        
        格式:
        Byte 0: [S|not_S|Quality[6bit]]
        Byte 1: Check bit + Angle[6:0]
        Byte 2: Angle[14:7]
        Byte 3: Distance[7:0]
        Byte 4: Distance[15:8]
        
        Args:
            data: 5字节数据
            
        Returns:
            (angle, distance, quality) 或 None
        """
        if len(data) != 5:
            return None
        
        try:
            # 解析第一个字节
            byte0 = data[0]
            start_flag = (byte0 >> 0) & 0x01  # S位
            not_start_flag = (byte0 >> 1) & 0x01  # not S位
            quality = (byte0 >> 2) & 0x3F  # 质量值（6位）
            
            # 解析角度（两个字节，15位有效）
            byte1 = data[1]
            byte2 = data[2]
            check_bit = (byte1 >> 0) & 0x01
            angle_q6 = ((byte1 >> 1) | (byte2 << 7)) & 0x7FFF
            angle = angle_q6 / 64.0  # 转换为度
            
            # 解析距离（两个字节，单位: 0.25mm）
            distance_q2 = struct.unpack('<H', data[3:5])[0]
            distance = distance_q2 / 4000.0  # 转换为米
            
            # 只返回有效数据（距离>0且距离<20米）
            if 0.1 < distance < 20.0:
                return (angle, distance, quality)
            
        except Exception as e:
            # 解析错误时返回None
            pass
        
        return None
    
    def __enter__(self):
        """支持with语句"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """支持with语句"""
        self.disconnect()

