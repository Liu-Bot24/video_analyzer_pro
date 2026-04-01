import os
import cv2
import base64
import requests
import csv
import shutil
import re
import yaml
import time
import logging
import threading
from concurrent.futures import ThreadPoolExecutor

# ==========================================
# 核心功能：热加载配置文件
# ==========================================
def load_config():
    """实时从磁盘读取最新的 config.yaml"""
    try:
        with open("config.yaml", 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as e:
        # 如果用户正在保存文件导致冲突，稍等一下返回 None
        return None

# 初始加载，用于确定路径和并发数
initial_config = load_config()
if not initial_config:
    print("错误：无法读取配置文件 config.yaml")
    exit(1)

# 路径归一化
SOURCE_DIR = os.path.normpath(initial_config['video']['source_dir'])

# 日志初始化（保持初始路径，避免运行中日志文件跳变）
log_path = os.path.join(SOURCE_DIR, initial_config['system']['log_file'])
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.FileHandler(log_path, encoding='utf-8'), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# 全局写入锁
write_lock = threading.Lock()

def safe_csv_operation(file_path, mode, callback, *args, **kwargs):
    while True:
        try:
            with open(file_path, mode, newline="", encoding="utf-8-sig") as f:
                return callback(f, *args, **kwargs)
        except PermissionError:
            logger.warning(f"⚠️ 文件被占用: {file_path}。请关闭 Excel。5秒后自动重试...")
            time.sleep(5)
        except Exception as e:
            logger.error(f"CSV 操作发生未知错误: {e}")
            raise

def get_dynamic_frame_count(video_path, video_settings):
    try:
        vidcap = cv2.VideoCapture(video_path)
        fps = vidcap.get(cv2.CAP_PROP_FPS)
        total_frames = int(vidcap.get(cv2.CAP_PROP_FRAME_COUNT))
        vidcap.release()
        if fps <= 0 or total_frames <= 0: return 8
        duration = total_frames / fps
        steps = video_settings['dynamic_frames']
        sorted_steps = sorted(steps, key=lambda x: x[0])
        for limit, count in sorted_steps:
            if duration <= limit:
                return count
        return sorted_steps[-1][1] if sorted_steps else 8
    except:
        return 8

def extract_frames(video_path, video_settings):
    num_frames = get_dynamic_frame_count(video_path, video_settings)
    try:
        vidcap = cv2.VideoCapture(video_path)
        if not vidcap.isOpened(): return [], 0
        total_frames = int(vidcap.get(cv2.CAP_PROP_FRAME_COUNT))
        if total_frames <= 0: return [], 0
        step = max(total_frames // num_frames, 1)
        frames_b64 = []
        for i in range(num_frames):
            vidcap.set(cv2.CAP_PROP_POS_FRAMES, i * step)
            success, image = vidcap.read()
            if success:
                height, width = image.shape[:2]
                max_dim = video_settings['max_dimension']
                if max(height, width) > max_dim:
                    scale = max_dim / max(height, width)
                    image = cv2.resize(image, (int(width * scale), int(height * scale)))
                _, buffer = cv2.imencode('.jpg', image, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
                b64_str = base64.b64encode(buffer).decode('utf-8')
                frames_b64.append(f"data:image/jpeg;base64,{b64_str}")
        vidcap.release()
        return frames_b64, num_frames
    except Exception as e:
        logger.error(f"提取视频帧失败 {video_path}: {e}")
        return [], 0

def analyze_video(video_path, api_settings, video_settings, category_map, system_settings):
    frames, count = extract_frames(video_path, video_settings)
    if not frames: return None
    
    categories_list = "\n".join([f"- {name}: {info['desc']}" for name, info in category_map.items()])
    prompt = system_settings['prompt_template'].format(categories_list=categories_list)
    
    payload = {
        "model": api_settings['model'],
        "messages": [{"role": "user", "content": [{"type": "text", "text": prompt}] + [{"type": "image_url", "image_url": {"url": f}} for f in frames]}],
        "temperature": api_settings['temperature'],
        "max_tokens": api_settings['max_tokens']
    }
    headers = {"Authorization": f"Bearer {api_settings['key']}", "Content-Type": "application/json"}
    
    for attempt in range(api_settings['max_retries'] + 1):
        try:
            response = requests.post(f"{api_settings['base_url']}/chat/completions", json=payload, headers=headers, timeout=api_settings['timeout'])
            if response.ok:
                return response.json()['choices'][0]['message']['content']
            logger.warning(f"API 错误 (尝试 {attempt+1}/{api_settings['max_retries']+1}): {response.text}")
        except Exception as e:
            logger.warning(f"请求异常 (尝试 {attempt+1}/{api_settings['max_retries']+1}): {e}")
        if attempt < api_settings['max_retries']: time.sleep(2)
    return None

def process_one_video(video_path):
    # --- 热加载逻辑开始 ---
    current_config = load_config()
    while not current_config:
        time.sleep(1) # 如果读不到（正在编辑），等一秒再读
        current_config = load_config()
    
    api_cfg = current_config['api']
    video_cfg = current_config['video']
    cat_map = current_config['categories']
    sys_cfg = current_config['system']
    # --- 热加载逻辑结束 ---

    filename = os.path.basename(video_path)
    result = analyze_video(video_path, api_cfg, video_cfg, cat_map, sys_cfg)
    
    if not result:
        logger.warning(f"❌ {filename} 识别失败，跳过。")
        return

    # 使用配置中定义的第一个分类作为默认值，防止硬编码导致崩溃
        category = list(cat_map.keys())[0] if cat_map else "safe"
    match_cat = re.search(r'\[Category:\s*(.*?)\]', result, re.IGNORECASE)
    if match_cat:
        cat_key = match_cat.group(1).lower().strip()
        if cat_key in cat_map:
                category = cat_key
            else:
                logger.warning(f"⚠️ AI 返回了未定义的分类: {cat_key}，已回退到默认分类: {category}")
        
    title = "未命名视频"
    match_title = re.search(r'\[Title:\s*(.*?)\]', result, re.IGNORECASE)
    if match_title:
        title = match_title.group(1).strip()[:15]
    else:
        title = re.sub(r'\[.*?\]', '', result).strip()[:15].replace('\n', ' ')

    csv_path = os.path.join(SOURCE_DIR, sys_cfg['csv_file'])
    
    with write_lock:
        def write_callback(f):
            writer = csv.writer(f)
            writer.writerow([filename, result, title])
        
        try:
            safe_csv_operation(csv_path, "a", write_callback)
            dest_folder = os.path.join(SOURCE_DIR, os.path.normpath(cat_map[category]['path']))
            os.makedirs(dest_folder, exist_ok=True)
            
            safe_title = re.sub(r'[\\/:*?"<>|]', '', title).strip()
            name_part, ext_part = os.path.splitext(filename)
            
            if video_cfg['auto_rename']:
                if video_cfg.get('keep_original_name', True):
                    base_name = f"{safe_title}_{name_part}"
                else:
                    base_name = safe_title
            else:
                base_name = name_part
            
            final_name = f"{base_name}{ext_part}"
            final_path = os.path.join(dest_folder, final_name)
            counter = 1
            while os.path.exists(final_path):
                final_name = f"{base_name}_{counter}{ext_part}"
                final_path = os.path.join(dest_folder, final_name)
                counter += 1
                
            shutil.move(video_path, final_path)
            logger.info(f"✅ {filename} -> {category} | 存为: {final_name}")
        except Exception as e:
            logger.error(f"落地执行失败 {filename}: {e}")

def main():
    initial_sys_cfg = initial_config['system']
    csv_path = os.path.join(SOURCE_DIR, initial_sys_cfg['csv_file'])
    
    if not os.path.exists(csv_path):
        def init_callback(f):
            csv.writer(f).writerow(["Filename", "Full Result", "Title"])
        safe_csv_operation(csv_path, "w", init_callback)

    def read_callback(f):
        res = set()
        reader = csv.reader(f)
        next(reader, None)
        for row in reader:
            if row: res.add(row[0])
        return res
    processed_files = safe_csv_operation(csv_path, "r", read_callback)

    all_videos = [os.path.join(SOURCE_DIR, f) for f in os.listdir(SOURCE_DIR)
                  if os.path.isfile(os.path.join(SOURCE_DIR, f)) 
                  and os.path.splitext(f)[1].lower() in initial_config['video']['extensions']]
    
    pending_videos = [v for v in all_videos if os.path.basename(v) not in processed_files]
    logger.info(f"扫描完成: 总计 {len(all_videos)}，已处理 {len(processed_files)}，待处理 {len(pending_videos)}。支持热切换配置。")

    if pending_videos:
        with ThreadPoolExecutor(max_workers=initial_sys_cfg['concurrency']) as executor:
            executor.map(process_one_video, pending_videos)
    else:
        logger.info("任务已全部完成。")

if __name__ == "__main__":
    main()
