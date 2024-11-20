import os
import random
import json
import cv2
import numpy as np
from moviepy.editor import VideoFileClip, concatenate_videoclips, AudioFileClip, vfx
from PIL import Image, ImageDraw, ImageFont  # 引入 Pillow

# 读取配置文件
def load_config():
    with open('config.json', 'r', encoding='utf-8') as f:
        return json.load(f)

# 自动创建必要文件夹
def setup_directories():
    required_dirs = ['video', 'music', 'result']
    for directory in required_dirs:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"创建文件夹: {directory}")

# 读取 logo
def load_logo(logo_path):
    if os.path.exists(logo_path):
        return cv2.imread(logo_path, cv2.IMREAD_UNCHANGED)
    else:
        print(f"未找到 logo 文件: {logo_path}")
        return None

# 添加 logo 到帧
def add_logo_to_frame(frame, logo_img):
    if logo_img is None:
        return frame

    frame = frame.copy()
    h, w = frame.shape[:2]
    logo_h, logo_w = logo_img.shape[:2]

    # 如果 logo 是带透明通道的 RGBA 图像，保留 alpha 通道
    if logo_img.shape[2] == 4:
        # 分离 RGBA 通道
        logo_rgb = logo_img[:, :, :3]  # 提取 RGB 通道
        alpha_channel = logo_img[:, :, 3] / 255.0  # alpha 通道归一化到 0-1 之间

        # 将 RGB 转换为 BGR
        logo_bgr = cv2.cvtColor(logo_rgb, cv2.COLOR_RGB2BGR)

        # 使用 alpha 通道混合 logo 和背景
        for c in range(3):  # 对每个颜色通道进行处理
            frame[0:logo_h, 0:logo_w, c] = (1 - alpha_channel) * frame[0:logo_h, 0:logo_w, c] + alpha_channel * logo_bgr[:, :, c]
    else:
        # 如果没有透明通道，则直接将 logo 图像叠加到背景帧
        # 如果 logo 是 RGB 格式，转换为 BGR 格式
        if logo_img.shape[2] == 3:  # 如果是 RGB 图像，转换为 BGR
            logo_img = cv2.cvtColor(logo_img, cv2.COLOR_RGB2BGR)

        overlay = frame[0:logo_h, 0:logo_w]
        combined = cv2.addWeighted(overlay, 0.5, logo_img, 0.5, 0)
        frame[0:logo_h, 0:logo_w] = combined

    return frame




# 添加文字到帧
def add_text_to_frame(frame, text, font_path, font_size, position, color, thickness, frame_idx, start, end):
    frame = frame.copy()

    if not (start <= frame_idx <= end):
        return frame

    img = Image.fromarray(frame)

    # 加载字体
    font = ImageFont.truetype(font_path, font_size)

    # 创建绘图对象
    draw = ImageDraw.Draw(img)

    # 绘制文字
    draw.text(position, text, font=font, fill=color, stroke_width=thickness, stroke_fill=(0, 0, 0))

    # 将图像转换回 OpenCV 格式
    return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)

# 添加 logo 和文字到帧
def add_logo_and_text_to_frame(frame, logo_img, text, font_path, font_size, position, color, thickness, frame_idx, start, end):
    frame = add_text_to_frame(frame, text, font_path, font_size, position, color, thickness, frame_idx, start, end)
    frame = add_logo_to_frame(frame, logo_img)

    return frame

def slow_down_video(input_clip, target_duration):
    # 计算原始视频的时长和目标时长
    original_duration = input_clip.duration
    print(f"原始时长: {original_duration} 秒，目标时长: {target_duration} 秒")
    
    # 计算播放速度因子
    speed_factor = original_duration / target_duration
    print(f"播放速度因子: {speed_factor}")
    
    # 如果目标时长大于原始时长，我们需要减慢视频播放速度
    if target_duration > original_duration:
        print("将视频播放速度减慢")
        extended_clip = input_clip.fx(vfx.speedx, speed_factor)  # 减慢播放速度
    else:
        print("目标时长小于或等于原始时长，无需修改播放速度")
        extended_clip = input_clip  # 如果目标时长更短或相等，直接返回原始视频
    
    return extended_clip

# 处理视频文件
def process_videos(config):
    music_dir = 'music'
    video_dir = 'video'
    result_dir = 'result'

    music_files = [f for f in os.listdir(music_dir) if f.endswith('.ogg')]
    folder_names = [f for f in os.listdir(video_dir) if os.path.isdir(os.path.join(video_dir, f))]
    logo_img = load_logo(config['logo_path'])

    for folder in folder_names:
        print(f"正在处理文件夹: {folder}")

        folder_path = os.path.join(video_dir, folder)
        video_files = [f for f in os.listdir(folder_path) if f.endswith(('.mp4', '.avi', '.mov'))]

        if not video_files:
            print(f"文件夹 {folder} 中没有视频文件，跳过...")
            continue

        video_clips = []
        for video_file in video_files:
            video_path = os.path.join(folder_path, video_file)
            video_clip = VideoFileClip(video_path)
            video_clips.append(video_clip)

        # 拼接视频
        final_clip = concatenate_videoclips(video_clips) if len(video_clips) > 1 else video_clips[0]

        # 延长视频至 60 秒
        target_duration = 60  # 目标时长（秒）
        final_clip = slow_down_video(final_clip, target_duration)

        # 处理拼接后的视频，添加 logo 和文字
        def add_overlay(get_frame, t):
            frame = get_frame(t)
            frame_idx = int(t * final_clip.fps)
            return add_logo_and_text_to_frame(
                frame, logo_img, config["text"], config["font_path"],
                config["text_font_size"], (10, frame.shape[0] - 50),  # 左下角
                tuple(config["text_color"]), config["text_thickness"],
                frame_idx, config["text_frame_start"], config["text_frame_end"]
            )

        final_clip = final_clip.fl(add_overlay)

        # 添加背景音乐
        if music_files:
            music_file = random.choice(music_files)
            music_path = os.path.join(music_dir, music_file)
            audio_clip = AudioFileClip(music_path)

            if audio_clip.duration > final_clip.duration:
                audio_clip = audio_clip.subclip(0, final_clip.duration)

            final_clip = final_clip.set_audio(audio_clip)

        # 输出最终视频
        output_path = os.path.join(result_dir, f'{folder}_output.mp4')
        print(f"保存视频: {output_path}")
        final_clip.write_videofile(output_path, codec='libx264', fps=24)
        final_clip.close()

    print("所有视频处理完成！")



# 主程序入口
if __name__ == "__main__":
    setup_directories()
    config = load_config()
    process_videos(config)
