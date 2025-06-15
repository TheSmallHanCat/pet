# 系统功能模块
# 包含所有可以被AI调用的系统功能

import subprocess
import webbrowser
import os
import re
import json

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
        print(f"[DEBUG] {message}")

def open_program(args):
    """打开系统程序"""
    program_name = args.get('program_name', '').strip()
    
    if not program_name:
        return "错误：没有指定程序名称"
    try:
        subprocess.Popen([program_name], shell=False)
        return f"成功：程序 {program_name} 已启动"
    except Exception as e:
        print_debug(f"程序启动失败: {str(e)}")
        return f"错误：程序启动失败 - {str(e)}"

def open_notepad(args):
    """描述"""
    try:
        #代码主体
        return "成功：记事本已启动"
    except Exception as e:
        print_debug(f"错误日志: {str(e)}")
        return f"错误：错误日志 - {str(e)}"

def set_volume(args):
    """设置系统音量"""
    try:
        level = args.get('level', 50)
        
        # 检查音量范围
        if not isinstance(level, int) or level < 0 or level > 100:
            return "错误：音量值必须是0-100之间的整数"
        
        try:
            # 使用pycaw库设置音量
            from ctypes import cast, POINTER
            from comtypes import CLSCTX_ALL
            from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
            
            # 获取音频设备
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            volume = cast(interface, POINTER(IAudioEndpointVolume))
            
            # 设置音量（0-100转换为0.0-1.0）
            volume_scalar = level / 100.0
            volume.SetMasterVolumeLevelScalar(volume_scalar, None)
            
            return f"成功：系统音量已设置为 {level}%"
            
        except ImportError:
            return "错误：缺少pycaw库，无法设置音量"
            
    except Exception as e:
        print_debug(f"音量设置失败: {str(e)}")
        return f"错误：音量设置失败 - {str(e)}"

def open_url(args):
    """在浏览器中打开网址"""
    try:
        url = args.get('url', '').strip()
        
        if not url:
            return "错误：没有指定网址"
        
        # 如果没有协议，自动添加https://
        if not (url.startswith('http://') or url.startswith('https://')):
            url = 'https://' + url
        
        webbrowser.open(url)
        return f"成功：已在浏览器中打开 {url}"
        
    except Exception as e:
        print_debug(f"网址打开失败: {str(e)}")
        return f"错误：网址打开失败 - {str(e)}"

def open_wyy(args):
    """打开网易云音乐"""
    try:
        path=["C:\\Program Files\\Netease\\","C:\\Program Files (x86)\\Netease\\","D:\\","E:\\","F:\\","G:\\"]
        for p in path:
            wyy_path = os.path.join(p, "CloudMusic", "cloudmusic.exe")
            if os.path.exists(wyy_path):
                found_path = wyy_path  #找到后的网易云地址
                break
        #如果你的网易云音乐安装在自定义路径，可以注释掉以上内容，直接赋值found_path为你网易云主程序的绝对路径
        if found_path:
            subprocess.Popen([found_path])
            return "成功：网易云音乐已启动"
        else:
            # 遍历完所有路径都没找到
            print_debug("网易云音乐可执行文件未找到。请检查安装路径。")
            return "错误：网易云音乐可执行文件未找到。请检查安装路径。你可以询问用户要不要打开网页版"
    except Exception as e:
        print_debug(f"网易云启动失败: {str(e)}，或者告诉用户要不要打开网页版")
        return f"错误：网易云启动失败 - {str(e)}，你可以询问用户要不要打开网页版"

def weather(args):
    """查询天气"""
    try:
        city = args.get('city', '').strip()
        
        if not city:
            return "错误：没有指定城市名称"
        
        import requests
        
        # 使用高德地图API查询天气
        api_key = "your_api_key"
        url = f"https://restapi.amap.com/v3/weather/weatherInfo?city={city}&key={api_key}"
        
        response = requests.get(url, timeout=10)
        data = response.json()
        if data.get('status') == '1' and data.get('lives'):
            weather_info = data['lives'][0]
            city_name = weather_info.get('city', city)
            weather_desc = weather_info.get('weather', '未知')
            temperature = weather_info.get('temperature', '未知')
            humidity = weather_info.get('humidity', '未知')
            wind_direction = weather_info.get('winddirection', '未知')
            wind_power = weather_info.get('windpower', '未知')
            
            result = f"{city_name}天气：{weather_desc}，温度{temperature}°C，湿度{humidity}%，{wind_direction}风{wind_power}级"
            return result
        else:
            return f"错误：无法获取{city}的天气信息"
            
    except Exception as e:
        print_debug(f"天气查询失败: {str(e)}")
        return f"错误：天气查询失败 - {str(e)}"

def capture_screen(args):
    """
    使用pyautogui.screenshot()截取整个屏幕，
    返回OpenAI标准格式的图片消息，以便AI能正确识别图片内容。
    """
    try:
        # 检查导入所需模块
        import pyautogui
        import io
        import base64
        from PIL import Image
        
        print_debug("开始使用pyautogui.screenshot()截取屏幕...")
        
        # 使用pyautogui截取屏幕，返回PIL Image对象
        screenshot_img = pyautogui.screenshot()
        
        if screenshot_img is None:
            return "错误：截屏失败，pyautogui.screenshot()返回None"
        
        print_debug(f"截屏成功，图片尺寸: {screenshot_img.size}")
        
        # 将PIL Image对象转换为PNG格式的字节流
        png_buffer = io.BytesIO()
        screenshot_img.save(png_buffer, format='PNG')
        png_buffer.seek(0)  # 重置缓冲区指针到开始位置
        
        # 读取字节数据并编码为Base64
        image_bytes = png_buffer.read()
        base64_string = base64.b64encode(image_bytes).decode('utf-8')
        
        print_debug(f"成功：已截取屏幕图片并转换为Base64 (长度: {len(base64_string)})")
        
        # 返回OpenAI标准格式的图片消息结构
        image_message = {
            "type": "image",
            "image_url": {
                "url": f"data:image/png;base64,{base64_string}",
                "detail": "high"
            }
        }
        
        print_debug("已生成OpenAI标准格式图片消息")
        return image_message
        
    except ImportError as e:
        missing_module = str(e).split("'")[-2] if "'" in str(e) else "未知模块"
        return f"错误：缺少依赖库 {missing_module}，请安装：pip install pyautogui Pillow"
        
    except Exception as e:
        print_debug(f"屏幕截取失败: {str(e)}")
        return f"错误：屏幕截取失败 - {str(e)}"



# 函数映射表 - 将函数名映射到实际的函数
FUNCTION_MAP = {
    'open_program': open_program,
    'open_notepad': open_notepad,
    'set_volume': set_volume,
    'open_url': open_url,
    'open_wyy': open_wyy,
    'weather': weather,
    'bilibili_search': bilibili_search,
    'capture_screen': capture_screen
}
def execute_function(function_name, arguments):
    """执行指定的函数"""
    if function_name not in FUNCTION_MAP:
        return f"错误：未知的函数 '{function_name}'"

    try:
        # 调用对应的函数
        func = FUNCTION_MAP[function_name]
        result = func(arguments)
        return result
    except Exception as e:
        print_debug(f"函数执行失败: {str(e)}")
        return f"错误：函数执行失败 - {str(e)}"
