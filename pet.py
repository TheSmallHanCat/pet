# 宠物窗口模块

import os
import sys
import json
import time
from pathlib import Path
from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt6.QtCore import Qt, QPoint, QTimer, QSize
from PyQt6.QtGui import QMovie, QPixmap

# 从config.json读取debug配置
def load_debug_config():
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
            return config.get('debug', False)
    except Exception:
        return False

DEBUG = load_debug_config()

def print_debug(message):
    """打印调试信息"""
    if DEBUG:
        print(f"[PET DEBUG] {message}")

def get_resource_path(relative_path):
    """获取资源文件的正确路径，兼容开发环境和打包后的环境"""
    if hasattr(sys, '_MEIPASS'):
        # 打包后的环境
        base_path = Path(sys._MEIPASS)
    else:
        # 开发环境
        base_path = Path(__file__).parent

    # 尝试不同的路径
    paths_to_try = [
        base_path / relative_path,  # 打包后的路径
        base_path / '..' / relative_path,  # 开发环境路径
        Path(relative_path)  # 相对路径
    ]

    for path in paths_to_try:
        if path.exists():
            return str(path)

    # 如果都找不到，返回原始路径
    return relative_path

class Pet(QWidget):
    """宠物窗口类"""
    
    def __init__(self, config):
        super().__init__()
        
        # 保存配置
        self.pet_states = config.get('pet_states', {})
        self.idle_timeout = config.get('idle_timeout_seconds', 60) * 1000  # 转换为毫秒
        
        # 当前状态
        self.current_state = "idle"
        self.current_movie = None
        
        # 拖拽相关
        self.is_dragging = False
        self.drag_offset = None
        
        # 聊天窗口引用（稍后设置）
        self.chat_window = None
        
        # 空闲计时器
        self.idle_timer = QTimer(self)
        self.idle_timer.timeout.connect(self.go_to_sleep)
        
        # 初始化界面
        self.setup_window()
        self.setup_ui()
        self.set_state("idle")
        
        # 启动空闲计时器
        self.start_idle_timer()
        
        print_debug("宠物窗口初始化完成")
    
    def setup_window(self):
        """设置窗口属性"""
        # 窗口设置
        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint |  # 窗口置顶
            Qt.WindowType.FramelessWindowHint |   # 无边框
            Qt.WindowType.Tool                    # 工具窗口（不在任务栏显示）
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)  # 透明背景
        
        # 设置窗口大小
        self.resize(150, 150)
        
        # 将窗口放在屏幕右下角
        screen = self.screen().availableGeometry()
        self.move(screen.width() - 200, screen.height() - 200)
    
    def setup_ui(self):
        """设置用户界面"""
        # 主布局
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 宠物图像标签
        self.pet_label = QLabel()
        self.pet_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.pet_label.setMinimumSize(150, 150)
        
        layout.addWidget(self.pet_label)
        self.setLayout(layout)
    
    def set_chat_window(self, chat_window):
        """设置聊天窗口引用"""
        self.chat_window = chat_window
    
    def set_state(self, state_name):
        """设置宠物状态"""
        # 如果状态相同且动画正在播放，不做改变
        if (self.current_state == state_name and 
            self.current_movie and 
            self.current_movie.state() == QMovie.MovieState.Running):
            return
        
        print_debug(f"切换状态: {self.current_state} -> {state_name}")
        self.current_state = state_name
        # 停止当前动画
        if self.current_movie:
            self.current_movie.stop()
            self.current_movie = None
        # 获取状态对应的文件路径
        if state_name in self.pet_states:
            file_path = get_resource_path(self.pet_states[state_name])
            # 检查文件是否存在
            if not os.path.exists(file_path):
                print_debug(f"文件不存在: {file_path}")
                return
            # 根据文件类型处理
            if file_path.lower().endswith('.gif'):# GIF动画
                self.current_movie = QMovie(file_path)
                self.current_movie.setScaledSize(QSize(120, 120))
                self.pet_label.setMovie(self.current_movie)
                self.current_movie.start()
                print_debug(f"播放GIF动画: {file_path}")
            else:# 静态图片
                pixmap = QPixmap(file_path)
                pixmap = pixmap.scaled(120, 120, Qt.AspectRatioMode.KeepAspectRatio, 
                                     Qt.TransformationMode.SmoothTransformation)
                self.pet_label.setPixmap(pixmap)
                print_debug(f"显示静态图片: {file_path}")
        # 如果不是睡眠状态，重置空闲计时器
        if state_name != "sleeping":
            self.start_idle_timer()
    
    def start_idle_timer(self):
        """启动空闲计时器"""
        self.idle_timer.stop()
        self.idle_timer.start(self.idle_timeout)
        print_debug(f"空闲计时器已启动，{self.idle_timeout/1000}秒后进入睡眠")
    
    def reset_idle_timer(self):
        """重置空闲计时器"""
        if self.current_state == "sleeping":
            self.set_state("idle")
        self.start_idle_timer()
        print_debug("空闲计时器已重置")
    
    def go_to_sleep(self):
        """进入睡眠状态"""
        self.set_state("sleeping")
        self.idle_timer.stop()
        print_debug("宠物进入睡眠状态")
    
    def get_chat_position(self):
        """计算聊天窗口应该显示的位置"""
        pet_pos = self.pos()
        # 聊天窗口显示在宠物下方
        chat_pos = QPoint(pet_pos.x() - 125, pet_pos.y() + 150)
        return chat_pos
    
    def toggle_chat(self):
        """切换聊天窗口显示状态"""
        if self.chat_window:
            if self.chat_window.isVisible():
                self.chat_window.hide()
                print_debug("隐藏聊天窗口")
            else:
                chat_pos = self.get_chat_position()
                self.chat_window.move(chat_pos)
                self.chat_window.show()
                self.chat_window.focus_input()
                print_debug("显示聊天窗口")
            
            self.set_state("attention")
            self.reset_idle_timer()
    
    def update_chat_position(self):
        """更新聊天窗口位置"""
        if self.chat_window and self.chat_window.isVisible():
            chat_pos = self.get_chat_position()
            self.chat_window.move(chat_pos)
    
    # 鼠标事件处理
    def mousePressEvent(self, event):
        """鼠标按下事件"""
        if event.button() == Qt.MouseButton.LeftButton:
            # 检测双击
            if event.type() == event.Type.MouseButtonDblClick:
                print_debug("检测到双击，切换聊天窗口")
                self.toggle_chat()
            else:
                # 单击开始拖拽
                print_debug("开始拖拽")
                self.is_dragging = True
                self.drag_offset = event.globalPosition().toPoint() - self.pos()
                self.set_state("attention")
            # 重置空闲计时器
            self.reset_idle_timer()
    
    def mouseMoveEvent(self, event):
        """鼠标移动事件（拖拽）"""
        if self.is_dragging and event.buttons() & Qt.MouseButton.LeftButton:
            # 计算新位置
            new_pos = event.globalPosition().toPoint() - self.drag_offset
            self.move(new_pos)
            # 更新聊天窗口位置
            self.update_chat_position()
    
    def mouseReleaseEvent(self, event):
        """鼠标释放事件"""
        if event.button() == Qt.MouseButton.LeftButton:
            print_debug("结束拖拽")
            self.is_dragging = False
            # 拖拽结束后，短暂保持attention状态，然后回到idle
            if self.current_state == "attention":
                QTimer.singleShot(2000, lambda: self.set_state("idle"))
    
    def handle_user_interaction(self):
        """处理用户交互（由聊天窗口调用）"""
        self.reset_idle_timer()
        print_debug("用户正在交互")
    
    def handle_ai_talking(self):
        """处理AI正在说话状态"""
        self.set_state("talking")
        print_debug("AI正在说话")
    
    def handle_ai_finished(self):
        """处理AI说话结束"""
        self.set_state("idle")
        print_debug("AI说话结束")
