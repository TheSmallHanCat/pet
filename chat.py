# 聊天窗口模块

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTextEdit,
                           QLineEdit, QPushButton, QLabel, QFrame)
from PyQt6.QtCore import Qt, QEvent, QTimer
from PyQt6.QtGui import QFont

# 从config.json读取debug配置
def load_debug_config():
    """从config.json加载debug配置"""
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
        print(f"[CHAT DEBUG] {message}")

class Chat(QDialog):
    """聊天窗口类"""
    
    def __init__(self):
        super().__init__()
        
        # AI管理器引用（稍后设置）
        self.ai_manager = None
        
        # 宠物窗口引用（稍后设置）
        self.pet_window = None
        
        # 设置窗口
        self.setup_window()
        self.setup_ui()
        
        print_debug("聊天窗口初始化完成")
    
    def setup_window(self):
        """设置窗口属性"""
        self.setWindowTitle("聊天")
        self.setFixedSize(350, 450)
        
        # 设置窗口样式
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |     # 无边框
            Qt.WindowType.Tool |                    # 工具窗口
            Qt.WindowType.WindowStaysOnTopHint      # 置顶
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)  # 背景透明
    
    def setup_ui(self):
        """设置用户界面"""
        # 主布局
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 创建背景框架
        self.frame = QFrame(self)
        self.frame.setObjectName("blurFrame")
        self.frame.setStyleSheet("""
            #blurFrame {
                background-color: rgba(255, 255, 255, 180);
                border-radius: 15px;
                border: 1px solid rgba(200, 200, 200, 200);
            }
        """)
        
        # 框架布局
        frame_layout = QVBoxLayout(self.frame)
        frame_layout.setContentsMargins(15, 15, 15, 15)
        
        # 标题栏
        title_layout = QHBoxLayout()
        title_label = QLabel("聊天")
        title_label.setStyleSheet("""
            color: #555555; 
            font-weight: bold;
            font-family: 'Microsoft YaHei', Arial;
        """)
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        
        # 关闭按钮
        close_button = QPushButton("×")
        close_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #888888;
                font-size: 20px;
                width: 30px;
                height: 30px;
                border-radius: 15px;
            }
            QPushButton:hover {
                background-color: rgba(200, 200, 200, 100);
                color: #333333;
            }
        """)
        close_button.clicked.connect(self.hide)
        title_layout.addWidget(close_button)
        
        # 聊天历史显示区域
        self.chat_history = QTextEdit()
        self.chat_history.setReadOnly(True)
        self.chat_history.setAcceptRichText(True)
        self.chat_history.setFrameStyle(QFrame.Shape.NoFrame)
        self.chat_history.setStyleSheet("""
            QTextEdit {
                background-color: rgba(255, 255, 255, 100);
                border-radius: 10px;
                padding: 10px;
                font-family: 'Microsoft YaHei', Arial;
                font-size: 12px;
            }
        """)
        
        # 设置字体
        font = QFont("Microsoft YaHei", 10)
        self.chat_history.setFont(font)
        
        # 添加欢迎消息
        self.add_welcome_message()
        
        # 输入区域
        input_layout = QHBoxLayout()
        
        # 消息输入框
        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("在这里输入消息...")
        self.message_input.installEventFilter(self)  # 安装事件过滤器处理回车键
        self.message_input.setStyleSheet("""
            QLineEdit {
                border-radius: 18px;
                padding: 10px 15px;
                background: rgba(255, 255, 255, 150);
                border: 1px solid rgba(200, 200, 200, 150);
                font-family: 'Microsoft YaHei', Arial;
                font-size: 12px;
            }
        """)
        input_layout.addWidget(self.message_input, 4)
        
        # 发送按钮
        self.send_button = QPushButton("发送")
        self.send_button.clicked.connect(self.send_message)
        self.send_button.setStyleSheet("""
            QPushButton {
                background-color: #4a86e8;
                color: white;
                border-radius: 18px;
                padding: 10px 15px;
                border: none;
                font-family: 'Microsoft YaHei', Arial;
                font-weight: bold;
                min-width: 60px;
            }
            QPushButton:hover {
                background-color: #3a76d8;
            }
            QPushButton:pressed {
                background-color: #2a66c8;
            }
        """)
        input_layout.addWidget(self.send_button, 1)
        
        # 构建完整布局
        frame_layout.addLayout(title_layout)
        frame_layout.addWidget(self.chat_history)
        frame_layout.addLayout(input_layout)
        
        layout.addWidget(self.frame)
        self.setLayout(layout)
    
    def set_ai_manager(self, ai_manager):
        """设置AI管理器引用"""
        self.ai_manager = ai_manager
    
    def set_pet_window(self, pet_window):
        """设置宠物窗口引用"""
        self.pet_window = pet_window
    
    def eventFilter(self, obj, event):
        """事件过滤器，处理回车键"""
        if obj is self.message_input and event.type() == QEvent.Type.KeyPress:
            if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
                self.send_message()
                return True
        return super().eventFilter(obj, event)
    
    def focus_input(self):
        """聚焦到输入框"""
        self.message_input.setFocus()
    
    def add_welcome_message(self):
        """添加欢迎消息"""
        welcome_html = """
            <div style='margin:12px 0;text-align:left;'>
                <div style='display:inline-block;max-width:80%;'>
                    <div style='font-size:9px;color:#888;margin-bottom:2px;'>小助手</div>
                    <div style='background-color:#f0f0f0;border-radius:15px;padding:10px 14px;color:#333;'>
                        你可以询问任何问题，或者让我帮你执行一些简单的操作。
                    </div>
                </div>
            </div>
        """
        self.chat_history.setHtml(welcome_html)
    
    def add_message(self, role, content):
        """添加消息到聊天历史"""
        if role == "user":
            # 用户消息样式
            html = f"""
            <br>
                <div style='margin:16px 0;text-align:right;'>
                    <div style='display:inline-block;max-width:80%;'>
                        <div style='font-size:9px;color:#888;margin-bottom:3px;'>我</div>
                        <div style='background-color:#d9f4fe;border-radius:15px;padding:10px 14px;color:#333;box-shadow:0 1px 2px rgba(0,0,0,0.1);'>
                            {content}
                        </div>
                    </div>
                </div>
            """
        elif role == "assistant":
            # AI助手消息样式
            html = f"""
            <br>
                <div style='margin:16px 0;text-align:left;'>
                    <div style='display:inline-block;max-width:80%;'>
                        <div style='font-size:9px;color:#888;margin-bottom:3px;'>小助手</div>
                        <div style='background-color:#f0f0f0;border-radius:15px;padding:10px 14px;color:#333;box-shadow:0 1px 2px rgba(0,0,0,0.1);'>
                            {content}
                        </div>
                    </div>
                </div>
            """
        else:
            # 系统消息样式
            html = f"""
                <div style='margin:12px 0;text-align:center;'>
                    <div style='display:inline-block;padding:5px 12px;background-color:rgba(240,240,240,0.7);border-radius:12px;'>
                        <span style='color:#888888;font-style:italic;'>{content}</span>
                    </div>
                </div>
            """
        
        # 添加HTML到聊天历史
        cursor = self.chat_history.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.chat_history.setTextCursor(cursor)
        self.chat_history.insertHtml(html)
        
        # 滚动到底部
        scrollbar = self.chat_history.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def send_message(self):
        """发送用户消息"""
        message = self.message_input.text().strip()
        if not message:
            return

        print_debug(f"发送消息: {message}")

        # 立即显示用户消息
        self.add_message("user", message)

        # 清空输入框
        self.message_input.clear()

        # 禁用输入控件
        self.disable_input("正在思考中...")

        # 通知宠物窗口用户正在交互
        if self.pet_window:
            self.pet_window.handle_user_interaction()

        # 异步处理AI响应，避免阻塞界面
        QTimer.singleShot(10, lambda: self.process_ai_response(message))

    def process_ai_response(self, message):
        """异步处理AI响应"""
        # 发送给AI处理
        if self.ai_manager:
            # 通知宠物窗口AI开始说话
            if self.pet_window:
                self.pet_window.handle_ai_talking()

            try:
                # 获取AI回复
                ai_response = self.ai_manager.send_message(message)

                # 显示AI回复
                self.add_message("assistant", ai_response)
                print_debug(f"收到AI回复: {ai_response}")

            except Exception as e:
                error_msg = f"AI处理失败: {str(e)}"
                self.add_message("system", error_msg)
                print_debug(error_msg)

            # 通知宠物窗口AI说话结束
            if self.pet_window:
                self.pet_window.handle_ai_finished()
        else:
            self.add_message("system", "AI管理器未初始化")

        # 重新启用输入控件
        self.enable_input()
    
    def disable_input(self, placeholder=""):
        """禁用输入控件"""
        self.message_input.setEnabled(False)
        self.send_button.setEnabled(False)
        if placeholder:
            self.message_input.setPlaceholderText(placeholder)
    
    def enable_input(self):
        """启用输入控件"""
        self.message_input.setEnabled(True)
        self.send_button.setEnabled(True)
        self.message_input.setPlaceholderText("在这里输入消息...")
        self.message_input.setFocus()
    
    def closeEvent(self, event):
        """重写关闭事件，改为隐藏"""
        event.ignore()
        self.hide()
        print_debug("聊天窗口已隐藏")
