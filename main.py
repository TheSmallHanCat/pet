# 桌面宠物主程序

import sys
import json
import os
from pathlib import Path
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon, QAction

# 导入桌宠的模块
from pet import Pet
from chat import Chat
from ai import AI

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
        print(f"[MAIN DEBUG] {message}")

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

def load_config(config_path='config.json'):
    """加载配置文件"""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            print_debug("配置文件加载成功")
            return config
    except Exception as e:
        print(f"加载配置文件失败: {str(e)}")
        print("请确保config.json文件存在且格式正确")
        sys.exit(1)

def check_assets():
    """检查资源文件是否存在"""
    assets_dir = get_resource_path('assets')
    if not os.path.exists(assets_dir):
        print("错误：assets目录不存在")
        print("请确保assets目录存在并包含宠物图片文件")
        sys.exit(1)

    # 检查必要的图片文件
    required_files = [
        'pet_idle.gif',
        'pet_attention.gif',
        'pet_talking.gif',
        'pet_sleeping.gif',
        'tray_icon.png'
    ]

    missing_files = []
    for file in required_files:
        file_path = os.path.join(assets_dir, file)
        if not os.path.exists(file_path):
            missing_files.append(file)

    if missing_files:
        print("错误：缺少以下资源文件：")
        for file in missing_files:
            print(f"  - {file}")
        print("请将这些文件放在assets目录中")
        sys.exit(1)

    print_debug("资源文件检查通过")

def create_tray_icon(app):
    """创建系统托盘图标"""
    icon_path = get_resource_path('assets/tray_icon.png')

    if not os.path.exists(icon_path):
        print("错误：找不到托盘图标文件")
        sys.exit(1)

    # 创建托盘图标
    tray_icon = QSystemTrayIcon(QIcon(icon_path), app)

    print_debug("系统托盘图标创建成功")
    return tray_icon

def create_tray_menu(pet_window, chat_window, app):
    """创建托盘菜单"""
    menu = QMenu()
    
    # 显示宠物
    show_pet_action = QAction("显示宠物", menu)
    show_pet_action.triggered.connect(pet_window.show)
    menu.addAction(show_pet_action)
    
    # 隐藏宠物
    hide_pet_action = QAction("隐藏宠物", menu)
    hide_pet_action.triggered.connect(pet_window.hide)
    menu.addAction(hide_pet_action)
    
    # 打开聊天
    chat_action = QAction("打开聊天", menu)
    chat_action.triggered.connect(lambda: pet_window.toggle_chat())
    menu.addAction(chat_action)



    # 分隔线
    menu.addSeparator()
    
    # 退出程序
    exit_action = QAction("退出", menu)
    exit_action.triggered.connect(app.quit)
    menu.addAction(exit_action)
    
    print_debug("托盘菜单创建成功")
    return menu

def main():
    """主函数"""
    print_debug("程序启动")
    
    # 创建QApplication
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)  # 关闭窗口不退出应用
    # 检查资源文件
    check_assets()
    # 加载配置
    config = load_config()
    # 创建AI管理器
    print_debug("初始化AI管理器...")
    ai_manager = AI(config)
    # 创建宠物窗口
    print_debug("初始化宠物窗口...")
    pet_window = Pet(config)
    # 创建聊天窗口
    print_debug("初始化聊天窗口...")
    chat_window = Chat()
    # 设置相互引用
    pet_window.set_chat_window(chat_window)
    chat_window.set_ai_manager(ai_manager)
    chat_window.set_pet_window(pet_window)
    
    print_debug("组件关联设置完成")
    
    # 创建系统托盘
    tray_icon = create_tray_icon(app)
    tray_menu = create_tray_menu(pet_window, chat_window, app)
    tray_icon.setContextMenu(tray_menu)
    
    # 托盘图标双击事件
    def on_tray_activated(reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            pet_window.show()
            print_debug("双击托盘图标，显示宠物")
    
    tray_icon.activated.connect(on_tray_activated)
    
    # 显示托盘图标
    tray_icon.show()
    
    # 显示宠物窗口
    pet_window.show()
    
    print_debug("程序初始化完成，进入事件循环")
    
    # 运行应用程序
    try:
        sys.exit(app.exec())
    except KeyboardInterrupt:
        print_debug("程序被用户中断")
        sys.exit(0)

if __name__ == "__main__":
    main()
