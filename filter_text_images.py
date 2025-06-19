import os
from PIL import Image
import pytesseract

# 设置图片文件夹路径（与脚本同目录下的images文件夹）
image_folder = os.path.join(os.path.dirname(__file__), 'images')

blocked_images = []

for filename in os.listdir(image_folder):
    if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.gif')):
        image_path = os.path.join(image_folder, filename)
        try:
            text = pytesseract.image_to_string(Image.open(image_path), lang='chi_sim')
            if '全国信息' in text:
                blocked_images.append('images/' + filename)
                print(f'发现含有"全国信息"的图片: {filename}')
        except Exception as e:
            print(f'处理{filename}时出错: {e}')

# 输出结果到txt文件
with open(os.path.join(os.path.dirname(__file__), 'blocked_images.txt'), 'w', encoding='utf-8') as f:
    for img in blocked_images:
        f.write(img + '\n')

print('筛选完成，结果已保存到 blocked_images.txt') 