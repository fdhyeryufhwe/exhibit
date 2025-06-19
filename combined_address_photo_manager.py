import tkinter as tk
from tkinter import messagebox, filedialog
import sqlite3
import tkinter.ttk as ttk
import os
import shutil
from PIL import Image, ImageTk
import json
import subprocess # 用于执行 Git 命令
import threading # 引入 threading 模块

# 移除 python-pptx 相关导入和检查
# try:
#     from pptx import Presentation
#     from pptx.util import Inches
#     from pptx.enum.text import PP_ALIGN
#     from pptx.enum.shapes import MSO_VERTICAL_ALIGNMENT
#     PPTX_AVAILABLE = True
# except ImportError:
#     PPTX_AVAILABLE = False

class AddressManagerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("地址照片管理软件")

        # 设置窗口初始大小
        self.root.geometry("1200x800")

        # 创建一个 Canvas 作为主滚动区域
        self.main_canvas = tk.Canvas(root)
        self.main_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 创建一个垂直滚动条并连接到 Canvas
        self.main_scrollbar = ttk.Scrollbar(root, orient=tk.VERTICAL, command=self.main_canvas.yview)
        self.main_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 配置 Canvas 的滚动
        self.main_canvas.configure(yscrollcommand=self.main_scrollbar.set)
        self.main_canvas.bind('<MouseWheel>', self._on_mouse_wheel) # 绑定鼠标滚轮事件

        # 在 Canvas 内部创建一个 Frame 来放置所有其他 widgets
        self.content_frame = ttk.Frame(self.main_canvas)
        self.content_frame_id = self.main_canvas.create_window((0, 0), window=self.content_frame, anchor="nw")

        # 确保 content_frame 的大小被计算，并据此设置 Canvas 的 scrollregion
        self.content_frame.bind('<Configure>', self._on_frame_configure)

        # 文件路径设置
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.data_file_path = os.path.join(self.base_dir, 'data.json')
        self.images_dir = os.path.join(self.base_dir, 'images')

        # 确保 images 文件夹存在
        if not os.path.exists(self.images_dir):
            os.makedirs(self.images_dir)

        # 检查Pillow是否安装
        try:
            from PIL import Image, ImageTk
        except ImportError:
            messagebox.showerror("错误", "Pillow库未安装。请运行 'pip install Pillow' 进行安装。")
            self.root.destroy()
            return

        # 移除 python-pptx 检查
        # if not PPTX_AVAILABLE:
        #     messagebox.showwarning("缺少库", "未安装 'python-pptx' 库。导出PPT功能将不可用。请运行 'pip install python-pptx' 进行安装。")

        # 应用 ttk 主题
        self.style = ttk.Style()
        self.style.theme_use('vista')

        self.style.configure('TButton', background='#4CAF50', foreground='white', font=('Arial', 10, 'bold'))
        self.style.map('TButton', background=[('active', '#45a049')])
        self.style.configure('Danger.TButton', background='#f44336', foreground='white', font=('Arial', 10, 'bold'))
        self.style.map('Danger.TButton', background=[('active', '#da190b')])

        # 连接或创建数据库
        self.conn = sqlite3.connect('addresses.db')
        self.cursor = self.conn.cursor()

        # 创建一个 Notebook (标签页) 来组织不同功能
        self.notebook = ttk.Notebook(self.content_frame) # 将 notebook 放在 content_frame 中
        self.notebook.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 照片上传与网站更新标签页
        self.photo_upload_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.photo_upload_tab, text="照片上传与网站更新")

        # 密钥管理标签页
        self.key_management_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.key_management_tab, text="密钥管理")

        # 在 content_frame (现在是 address_tab) 创建之后调用 create_table
        self.create_table()

        # 创建界面元素
        self.create_photo_uploader_widgets(self.photo_upload_tab) # 照片上传界面
        self.create_key_management_widgets(self.key_management_tab) # 密钥管理界面

        # 初始填充省份下拉框
        # self.populate_provinces()

    def _on_mouse_wheel(self, event):
        # print(f"Mouse wheel event: {event.delta}") # 调试完成后可删除
        self.main_canvas.yview_scroll(-1 * (event.delta // 120), "units")

    def _on_frame_configure(self, event):
        """更新 Canvas 的滚动区域以匹配内容 Frame 的大小"""
        self.main_canvas.config(scrollregion=self.main_canvas.bbox("all"))

    def create_table(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS addresses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                province TEXT NOT NULL,
                city TEXT NOT NULL,
                street TEXT,
                full_address TEXT NOT NULL,
                remark TEXT,
                phone TEXT,
                wechat TEXT,
                qq TEXT,
                price TEXT,
                project TEXT,
                photo_path TEXT,
                age TEXT,
                duration_hours TEXT,
                height TEXT,
                weight TEXT
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS keys (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key_hash TEXT NOT NULL UNIQUE,
                key_type TEXT NOT NULL,
                expiration_time REAL, -- Unix timestamp
                plain_key TEXT -- 用于临时显示，不应该长期存储
            )
        ''')
        self.conn.commit()

    def create_photo_uploader_widgets(self, parent_frame):
        # 照片上传区域
        upload_frame = tk.LabelFrame(parent_frame, text="上传照片到网站", bg='#e0e0e0', fg='#333333')
        upload_frame.pack(padx=10, pady=10, fill="both", expand=True)

        tk.Label(upload_frame, text="照片文件:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.upload_photo_path_entry = tk.Entry(upload_frame, width=60)
        self.upload_photo_path_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        tk.Button(upload_frame, text="选择照片", command=self.select_photo_for_upload).grid(row=0, column=2, padx=5, pady=5)

        tk.Label(upload_frame, text="完整地址:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.upload_full_address_entry = tk.Entry(upload_frame, width=60)
        self.upload_full_address_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        tk.Label(upload_frame, text="年龄:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.upload_age_entry = tk.Entry(upload_frame, width=60)
        self.upload_age_entry.grid(row=2, column=1, padx=5, pady=5, sticky="ew")

        tk.Label(upload_frame, text="价格:").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.upload_price_entry = tk.Entry(upload_frame, width=60)
        self.upload_price_entry.grid(row=3, column=1, padx=5, pady=5, sticky="ew")

        tk.Label(upload_frame, text="身高:").grid(row=4, column=0, padx=5, pady=5, sticky="w")
        self.upload_height_entry = tk.Entry(upload_frame, width=60)
        self.upload_height_entry.grid(row=4, column=1, padx=5, pady=5, sticky="ew")

        tk.Label(upload_frame, text="体重:").grid(row=5, column=0, padx=5, pady=5, sticky="w")
        self.upload_weight_entry = tk.Entry(upload_frame, width=60)
        self.upload_weight_entry.grid(row=5, column=1, padx=5, pady=5, sticky="ew")

        tk.Button(upload_frame, text="添加照片并更新网站", command=self.add_photo_and_update_website).grid(row=6, column=1, padx=5, pady=10, sticky="e")
        tk.Button(upload_frame, text="清空输入", command=self.clear_uploader_fields).grid(row=6, column=0, padx=5, pady=10, sticky="w")

        upload_frame.grid_columnconfigure(1, weight=1) # 让输入框可以伸展

        # 已上传照片列表区域
        list_frame = tk.LabelFrame(parent_frame, text="已上传照片", bg='#e0e0e0', fg='#333333')
        list_frame.pack(padx=10, pady=10, fill="both", expand=True)

        self.uploaded_photos_listbox = tk.Listbox(list_frame, height=10, selectmode=tk.EXTENDED)
        self.uploaded_photos_listbox.pack(padx=5, pady=5, fill="both", expand=True)

        delete_selected_button = tk.Button(list_frame, text="删除选中照片", command=self.delete_selected_uploaded_photo)
        delete_selected_button.pack(pady=5)

        # 新增的导入按钮
        self.import_db_button = ttk.Button(list_frame, text="导入旧信息 (DB)", command=self.import_info_from_db)
        self.import_db_button.pack(side=tk.LEFT, padx=5, pady=5)

        self.import_photos_button = ttk.Button(list_frame, text="导入旧照片 (文件夹)", command=self.import_photos_from_folder)
        self.import_photos_button.pack(side=tk.LEFT, padx=5, pady=5)

        self.sync_website_button = ttk.Button(list_frame, text="同步到网站", command=self.regenerate_data_json_from_db_and_images)
        self.sync_website_button.pack(side=tk.LEFT, padx=5, pady=5)

        self.load_uploaded_photos_listbox() # 初始加载列表

    def select_photo(self):
        """地址管理页面选择照片"""
        filename = filedialog.askopenfilename(
            title="选择照片文件",
            filetypes=(("Image files", "*.jpg *.jpeg *.png *.gif"), ("All files", "*.*"))
        )
        if filename:
            self.photo_path_entry.delete(0, tk.END)
            self.photo_path_entry.insert(0, filename)

    def select_photo_for_upload(self):
        """照片上传页面选择照片"""
        filename = filedialog.askopenfilename(
            title="选择照片文件",
            filetypes=(("Image files", "*.jpg *.jpeg *.png *.gif"), ("All files", "*.*"))
        )
        if filename:
            self.upload_photo_path_entry.delete(0, tk.END)
            self.upload_photo_path_entry.insert(0, filename)

    def add_address(self):
        province = self.province_entry.get().strip()
        city = self.city_entry.get().strip()
        street = self.street_entry.get().strip()
        full_address = f"{province}{city}{street}"
        remark = self.remark_entry.get().strip()
        phone = self.phone_entry.get().strip()
        wechat = self.wechat_entry.get().strip()
        qq = self.qq_entry.get().strip()
        price = self.price_entry.get().strip()
        project = self.project_entry.get().strip()
        photo_path = self.photo_path_entry.get().strip()
        age = self.age_entry.get().strip()
        duration_hours = self.duration_hours_entry.get().strip()
        height = self.height_entry.get().strip()
        weight = self.weight_entry.get().strip()

        if not province or not city or not street:
            messagebox.showwarning("输入错误", "省份、城市和详细地址都不能为空")
            return

        try:
            self.cursor.execute("SELECT COUNT(*) FROM addresses WHERE phone = ? AND wechat = ? AND qq = ?",
                                (phone, wechat, qq))
            count = self.cursor.fetchone()[0]

            if count > 0:
                messagebox.showwarning("重复", "已存在相同电话、微信和 QQ 的记录，无法添加。")
                return

        except Exception as e:
            messagebox.showerror("数据库错误", f"检查重复项失败: {e}")
            return

        try:
            self.cursor.execute("INSERT INTO addresses (province, city, street, full_address, remark, phone, wechat, qq, price, project, photo_path, age, duration_hours, height, weight) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                                (province, city, street, full_address, remark, phone, wechat, qq, price, project, photo_path, age, duration_hours, height, weight))
            self.conn.commit()
            messagebox.showinfo("成功", "地址添加成功")
            self.clear_input_fields()
            self.populate_provinces()
        except Exception as e:
            messagebox.showerror("错误", f"添加地址失败: {e}")

    def add_photo_and_update_website(self):
        original_photo_path = self.upload_photo_path_entry.get().strip()
        full_address = self.upload_full_address_entry.get().strip()
        age = self.upload_age_entry.get().strip()
        price = self.upload_price_entry.get().strip()
        height = self.upload_height_entry.get().strip()
        weight = self.upload_weight_entry.get().strip()

        if not original_photo_path or not full_address:
            messagebox.showwarning("输入错误", "照片文件和完整地址不能为空。")
            return

        # 1. 复制照片到 images 文件夹
        try:
            photo_filename = os.path.basename(original_photo_path)
            destination_photo_path = os.path.join(self.images_dir, photo_filename)

            # 使用优化函数复制照片
            if not self.optimize_image(original_photo_path, destination_photo_path):
                messagebox.showerror("文件错误", "照片优化和复制失败。")
                return

            web_photo_path = f"images/{photo_filename}"
        except Exception as e:
            messagebox.showerror("文件错误", f"复制照片失败: {e}")
            return

        # 2. 更新 data.json
        new_entry = {
            "photo_path": web_photo_path,
            "full_address": full_address,
            "age": age,
            "price": price,
            "height": height,
            "weight": weight
        }

        try:
            current_data = self.load_data()
            current_data.append(new_entry)
            self.save_data(current_data)
            
            # 将新添加的信息也存储到 SQLite 数据库
            self.cursor.execute("INSERT INTO addresses (province, city, street, full_address, remark, phone, wechat, qq, price, project, photo_path, age, duration_hours, height, weight) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                                ('', '', '', full_address, '', '', '', '', price, '', destination_photo_path, age, '', height, weight))
            self.conn.commit()

            messagebox.showinfo("成功", "照片信息已成功添加到数据文件和数据库。正在更新网站。")
            self.clear_uploader_fields()
            
            # 调用新的同步函数，确保网站数据与数据库和图片文件夹一致
            self.regenerate_data_json_from_db_and_images()

        except Exception as e:
            messagebox.showerror("数据错误", f"更新数据文件失败: {e}")

    def load_data(self):
        """从 data.json 文件加载数据"""
        if os.path.exists(self.data_file_path) and os.path.getsize(self.data_file_path) > 0:
            try:
                with open(self.data_file_path, 'r', encoding='utf-8-sig') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                # 如果文件内容不正确，返回空列表
                return []
        return []

    def save_data(self, data):
        """将数据保存到 data.json 文件"""
        try:
            with open(self.data_file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            messagebox.showerror("保存错误", f"保存数据到 data.json 失败: {e}")

    def optimize_image(self, original_path, destination_path, min_size=(600, 400), max_size=(1200, 900), quality=85):
        """
        优化图片大小和质量并保存到目标路径。
        图片会被按比例缩小以适应max_size，如果小于min_size也会按比例放大。
        """
        try:
            img = Image.open(original_path)
            width, height = img.size

            # 先处理放大逻辑
            if width < min_size[0] or height < min_size[1]:
                # 计算需要放大的比例，取两者中较大的一个以确保图片至少达到最小尺寸
                ratio_w = min_size[0] / width
                ratio_h = min_size[1] / height
                scale_ratio = max(ratio_w, ratio_h)
                new_width = int(width * scale_ratio)
                new_height = int(height * scale_ratio)
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                width, height = img.size # Update dimensions after potential upscale

            # 再处理缩小逻辑
            if width > max_size[0] or height > max_size[1]:
                img.thumbnail(max_size, Image.Resampling.LANCZOS)

            # 根据图片格式决定保存方式
            if original_path.lower().endswith(('.jpg', '.jpeg')):
                if img.mode == 'RGBA':
                    img = img.convert('RGB') # 转换为RGB，去除透明度，以便保存为JPEG
                img.save(destination_path, "JPEG", quality=quality, optimize=True)
            elif original_path.lower().endswith( '.png'):
                img.save(destination_path, "PNG", optimize=True)
            elif original_path.lower().endswith( '.webp'):
                img.save(destination_path, "WEBP", quality=quality, optimize=True)
            else:
                img.save(destination_path)
            return True
        except Exception as e:
            print(f"图片优化失败: {e}")
            return False

    def run_git_commands(self, commit_message=None):
        # 检查是否正在运行 Git 命令以避免重复执行
        if hasattr(self, 'git_process_running') and self.git_process_running:
            messagebox.showinfo("Git 操作", "Git 同步操作正在后台进行中，请稍候...", parent=self.root)
            return

        self.git_process_running = True
        messagebox.showinfo("Git 操作", "Git 同步操作将在后台进行，应用程序将保持响应。", parent=self.root)

        # 默认提交信息
        if commit_message is None:
            commit_message = "Update address and photo data"

        def _run_git_in_thread():
            try:
                # 切换到项目目录
                os.chdir(self.base_dir)

                # 1. git add .
                subprocess.run(["git", "add", "."], check=True, capture_output=True, text=True)
                print("Git add successful.")

                # 2. git commit -m "..."
                subprocess.run(["git", "commit", "-m", commit_message], check=True, capture_output=True, text=True)
                print("Git commit successful.")

                # 3. git push origin main
                # 确保使用正确的远程和分支名称
                # 如果您的主分支是 master，请将 main 替换为 master
                # 重新引入 PAT 认证逻辑
                pat = None
                pat_file_path = os.path.join(self.base_dir, 'github_pat.txt')
                if os.path.exists(pat_file_path):
                    with open(pat_file_path, 'r', encoding='utf-8') as f:
                        pat = f.read().strip()

                if not pat:
                    messagebox.showerror("Git 错误", "未找到个人访问令牌（PAT）。请在 'github_pat.txt' 文件中放置您的 PAT。", parent=self.root)
                    return

                remote_url = f"https://{pat}@github.com/fdhyeryufhwe/Information.git"
                subprocess.run(["git", "push", remote_url, "main"], check=True, capture_output=True, text=True)
                print("Git push successful.")

                messagebox.showinfo("Git 操作", "数据已成功同步到 GitHub Pages！", parent=self.root)

            except subprocess.CalledProcessError as e:
                error_message = f"Git 命令执行失败！\n命令: {e.cmd}\n标准输出: {e.stdout}\n错误输出: {e.stderr}"
                print(error_message)
                messagebox.showerror("Git 错误", error_message, parent=self.root)
            except FileNotFoundError:
                messagebox.showerror("Git 错误", "未找到 Git 命令。请确保 Git 已安装并添加到系统 PATH 中。", parent=self.root)
            except Exception as e:
                messagebox.showerror("Git 错误", f"执行 Git 命令时发生意外错误: {e}", parent=self.root)
            finally:
                self.git_process_running = False # 确保在操作完成后重置标志

        # 在新线程中运行 Git 命令
        git_thread = threading.Thread(target=_run_git_in_thread)
        git_thread.start()

    def populate_provinces(self):
        try:
            self.cursor.execute("SELECT DISTINCT province FROM addresses ORDER BY province")
            provinces = [row[0] for row in self.cursor.fetchall()]
            self.province_combobox['values'] = provinces
            self.city_combobox['values'] = []
            self.city_var.set('')
            self.address_listbox.delete(0, tk.END)
        except Exception as e:
            print(f"获取省份失败: {e}")

    def on_province_select(self, event=None):
        selected_province = self.province_var.get()
        if selected_province:
            try:
                self.cursor.execute("SELECT DISTINCT city FROM addresses WHERE province = ? ORDER BY city", (selected_province,))
                cities = [row[0] for row in self.cursor.fetchall()]
                self.city_combobox['values'] = cities
                self.city_var.set('')
                self.address_listbox.delete(0, tk.END)
            except Exception as e:
                print(f"获取城市失败: {e}")
        else:
            self.city_combobox['values'] = []
            self.city_var.set('')
            self.address_listbox.delete(0, tk.END)

    def search_addresses(self):
        selected_province = self.province_var.get()
        selected_city = self.city_var.get()

        if not selected_province or not selected_city:
            messagebox.showwarning("输入错误", "请选择省份和城市进行查询")
            return

        try:
            self.cursor.execute("SELECT id, province, city, street, full_address, remark, phone, wechat, qq, price, project, photo_path, age, duration_hours, height, weight FROM addresses WHERE province = ? AND city = ?",
                                (selected_province, selected_city))
            results = self.cursor.fetchall()

            self.address_listbox.delete(0, tk.END)
            self.addresses_in_listbox = []

            if results:
                for row in results:
                    (address_id, province, city, street, full_address, remark,
                     phone, wechat, qq, price, project, photo_path, age, duration_hours, height, weight) = row

                    display_text = f"{province}-{city}-{street}"
                    if remark: display_text += f" (备注: {remark})"
                    if phone: display_text += f" (电话: {phone})"
                    if wechat: display_text += f" (微信: {wechat})"
                    if qq: display_text += f" (QQ: {qq})"
                    if price: display_text += f" (价格: {price})"
                    if project: display_text += f" (项目: {project})"
                    if photo_path:
                         filename = os.path.basename(photo_path)
                         display_text += f" (照片: {filename})"
                    if age: display_text += f" (年龄: {age})"
                    if duration_hours: display_text += f" (时长: {duration_hours}小时)"
                    if height: display_text += f" (身高: {height})"
                    if weight: display_text += f" (体重: {weight})"

                    self.address_listbox.insert(tk.END, display_text)
                    self.addresses_in_listbox.append(row)
            else:
                self.address_listbox.insert(tk.END, "未找到匹配的地址")
                self.addresses_in_listbox = []

        except Exception as e:
            messagebox.showerror("查询错误", f"查询地址失败: {e}")

    def search_by_text(self):
        keyword = self.search_entry.get().strip()

        if not keyword:
            messagebox.showwarning("输入错误", "请输入搜索关键词")
            self.address_listbox.delete(0, tk.END)
            self.addresses_in_listbox = []
            return

        try:
            self.cursor.execute("SELECT DISTINCT province FROM addresses")
            all_provinces = [row[0] for row in self.cursor.fetchall()]
            
            is_province_search = False
            for p in all_provinces:
                if keyword == p or (p.endswith('省') and keyword == p[:-1]) or (p.endswith('市') and keyword == p[:-1]):
                    self.cursor.execute("SELECT id, province, city, street, full_address, remark, phone, wechat, qq, price, project, photo_path, age, duration_hours, height, weight FROM addresses WHERE province = ?",
                                        (p,))
                    is_province_search = True
                    break

            if not is_province_search:
                self.cursor.execute("SELECT id, province, city, street, full_address, remark, phone, wechat, qq, price, project, photo_path, age, duration_hours, height, weight FROM addresses "
                                    "WHERE province LIKE ? OR city LIKE ? OR street LIKE ? OR full_address LIKE ? OR remark LIKE ? OR phone LIKE ? OR wechat LIKE ? OR qq LIKE ? OR price LIKE ? OR project LIKE ? OR photo_path LIKE ? OR age LIKE ? OR duration_hours LIKE ? OR height LIKE ? OR weight LIKE ?",
                                    (f"%{keyword}%", f"%{keyword}%", f"%{keyword}%", f"%{keyword}%", f"%{keyword}%", f"%{keyword}%", f"%{keyword}%", f"%{keyword}%", f"%{keyword}%", f"%{keyword}%", f"%{keyword}%", f"%{keyword}%", f"%{keyword}%", f"%{keyword}%", f"%{keyword}%"))

            results = self.cursor.fetchall()

            self.address_listbox.delete(0, tk.END)
            self.addresses_in_listbox = []

            if results:
                for row in results:
                    (address_id, province, city, street, full_address, remark,
                     phone, wechat, qq, price, project, photo_path, age, duration_hours, height, weight) = row

                    display_text = f"{province}-{city}-{street}"
                    self.address_listbox.insert(tk.END, display_text)
                    self.addresses_in_listbox.append(row)
            else:
                self.address_listbox.insert(tk.END, "未找到匹配的地址")
                self.addresses_in_listbox = []

        except Exception as e:
            messagebox.showerror("查询错误", f"文本搜索失败: {e}")

    def clear_results(self):
        self.address_listbox.delete(0, tk.END)
        self.addresses_in_listbox = []

    def delete_address(self):
        selected_indices = self.address_listbox.curselection()
        if not selected_indices:
            messagebox.showwarning("未选中", "请在列表中选择要删除的地址")
            return

        ids_to_delete = [self.addresses_in_listbox[i][0] for i in selected_indices]

        if messagebox.askyesno("确认删除", f"确定要删除选中的 {len(ids_to_delete)} 条地址吗?"):
            try:
                placeholders = ', '.join('?' for _ in ids_to_delete)
                self.cursor.execute(f"DELETE FROM addresses WHERE id IN ({placeholders})", ids_to_delete)
                self.conn.commit()
                messagebox.showinfo("成功", f"成功删除 {len(ids_to_delete)} 条地址")
                self.search_addresses()
                self.populate_provinces()
            except Exception as e:
                messagebox.showerror("删除错误", f"删除地址失败: {e}")

    def edit_address(self):
        selected_indices = self.address_listbox.curselection()
        if not selected_indices:
            messagebox.showwarning("未选中", "请在列表中选择要编辑的地址")
            return
        if len(selected_indices) > 1:
             messagebox.showwarning("多个选中", "请只选择一条地址进行编辑")
             return

        selected_index = selected_indices[0]
        address_id_to_edit = self.addresses_in_listbox[selected_index][0]

        try:
            self.cursor.execute("SELECT province, city, street, remark, phone, wechat, qq, price, project, photo_path, age, duration_hours, height, weight FROM addresses WHERE id = ?", (address_id_to_edit,))
            result = self.cursor.fetchone()

            if result:
                (province, city, street, remark, phone, wechat, qq,
                 price, project, photo_path, age, duration_hours, height, weight) = result

                self.province_entry.delete(0, tk.END)
                self.province_entry.insert(0, province or "")
                self.city_entry.delete(0, tk.END)
                self.city_entry.insert(0, city or "")
                self.street_entry.delete(0, tk.END)
                self.street_entry.insert(0, street or "")
                self.remark_entry.delete(0, tk.END)
                self.remark_entry.insert(0, remark or "")
                self.phone_entry.delete(0, tk.END)
                self.phone_entry.insert(0, phone or "")
                self.wechat_entry.delete(0, tk.END)
                self.wechat_entry.insert(0, wechat or "")
                self.qq_entry.delete(0, tk.END)
                self.qq_entry.insert(0, qq or "")
                self.price_entry.delete(0, tk.END)
                self.price_entry.insert(0, price or "")
                self.project_entry.delete(0, tk.END)
                self.project_entry.insert(0, project or "")
                self.photo_path_entry.delete(0, tk.END)
                self.photo_path_entry.insert(0, photo_path or "")
                self.age_entry.delete(0, tk.END)
                self.age_entry.insert(0, age or "")
                self.duration_hours_entry.delete(0, tk.END)
                self.duration_hours_entry.insert(0, duration_hours or "")
                self.height_entry.delete(0, tk.END)
                self.height_entry.insert(0, height or "")
                self.weight_entry.delete(0, tk.END)
                self.weight_entry.insert(0, weight or "")


                self.editing_id = address_id_to_edit
                self.add_button.config(text="更新地址", command=self.update_address)
            else:
                 messagebox.showerror("错误", "未找到要编辑的地址信息")

        except Exception as e:
            messagebox.showerror("编辑错误", f"获取地址信息失败: {e}")

    def update_address(self):
        if not hasattr(self, 'editing_id') or self.editing_id is None:
            messagebox.showwarning("错误", "没有正在编辑的地址")
            return

        province = self.province_entry.get().strip()
        city = self.city_entry.get().strip()
        street = self.street_entry.get().strip()
        full_address = f"{province}{city}{street}"
        remark = self.remark_entry.get().strip()
        phone = self.phone_entry.get().strip()
        wechat = self.wechat_entry.get().strip()
        qq = self.qq_entry.get().strip()
        price = self.price_entry.get().strip()
        project = self.project_entry.get().strip()
        photo_path = self.photo_path_entry.get().strip()
        age = self.age_entry.get().strip()
        duration_hours = self.duration_hours_entry.get().strip()
        height = self.height_entry.get().strip()
        weight = self.weight_entry.get().strip()

        if not province or not city or not street:
            messagebox.showwarning("输入错误", "省份、城市和详细地址都不能为空")
            return

        try:
            self.cursor.execute("UPDATE addresses SET province = ?, city = ?, street = ?, full_address = ?, remark = ?, phone = ?, wechat = ?, qq = ?, price = ?, project = ?, photo_path = ?, age = ?, duration_hours = ?, height = ?, weight = ? WHERE id = ?",
                                (province, city, street, full_address, remark, phone, wechat, qq, price, project, photo_path, age, duration_hours, height, weight, self.editing_id))
            self.conn.commit()
            messagebox.showinfo("成功", "地址更新成功")

            self.add_button.config(text="添加地址", command=self.add_address)
            self.editing_id = None
            self.clear_input_fields()

            self.search_addresses()
            self.populate_provinces()

        except Exception as e:
            messagebox.showerror("更新错误", f"更新地址失败: {e}")

    def clear_input_fields(self):
        self.province_entry.delete(0, tk.END)
        self.city_entry.delete(0, tk.END)
        self.street_entry.delete(0, tk.END)
        self.remark_entry.delete(0, tk.END)
        self.phone_entry.delete(0, tk.END)
        self.wechat_entry.delete(0, tk.END)
        self.qq_entry.delete(0, tk.END)
        self.price_entry.delete(0, tk.END)
        self.project_entry.delete(0, tk.END)
        self.photo_path_entry.delete(0, tk.END)
        self.age_entry.delete(0, tk.END)
        self.duration_hours_entry.delete(0, tk.END)
        self.height_entry.delete(0, tk.END)
        self.weight_entry.delete(0, tk.END)

    def clear_uploader_fields(self):
        self.upload_photo_path_entry.delete(0, tk.END)
        self.upload_full_address_entry.delete(0, tk.END)
        self.upload_age_entry.delete(0, tk.END)
        self.upload_price_entry.delete(0, tk.END)
        self.upload_height_entry.delete(0, tk.END)
        self.upload_weight_entry.delete(0, tk.END)

    def view_photo(self):
        selected_indices = self.address_listbox.curselection()
        if not selected_indices:
            messagebox.showwarning("未选中", "请在列表中选择要查看照片的地址")
            return
        if len(selected_indices) > 1:
             messagebox.showwarning("多个选中", "请只选择一条地址查看照片")
             return

        selected_index = selected_indices[0]
        address_data = self.addresses_in_listbox[selected_index]
        photo_path = address_data[11]

        if photo_path and os.path.exists(photo_path):
            try:
                os.startfile(photo_path)
            except Exception as e:
                messagebox.showerror("打开照片失败", f"无法打开照片文件: {e}")
        else:
            messagebox.showinfo("无照片", "选中的地址没有关联的照片或文件不存在")

    def copy_selected_address(self):
        selected_indices = self.address_listbox.curselection()
        if not selected_indices:
            messagebox.showwarning("未选中", "请在列表中选择要复制的地址")
            return

        selected_items_text = []
        for index in selected_indices:
            item_text = self.address_listbox.get(index)
            selected_items_text.append(item_text)

        text_to_copy = "\n".join(selected_items_text)

        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(text_to_copy)
            messagebox.showinfo("成功", "选中内容已复制到剪贴板")
        except Exception as e:
            messagebox.showerror("复制失败", f"复制内容到剪贴板失败: {e}")

    def show_detail_popup(self, event=None):
        selected_indices = self.address_listbox.curselection()
        if not selected_indices:
            messagebox.showwarning("未选中", "请选择一个地址查看详细信息")
            return

        selected_index = selected_indices[0]
        address_data = self.addresses_in_listbox[selected_index]

        popup = tk.Toplevel(self.root)
        popup.title("地址详细信息")
        popup.transient(self.root)
        popup.grab_set()
        popup.focus_set()

        detail_frame = ttk.Frame(popup)
        detail_frame.pack(padx=10, pady=10, fill="both", expand=True)

        row_idx = 0

        photo_path = address_data[11]
        if photo_path and os.path.exists(photo_path):
            try:
                img = Image.open(photo_path)
                img.thumbnail((300, 300))
                photo = ImageTk.PhotoImage(img)
                photo_label = ttk.Label(detail_frame, image=photo)
                photo_label.image = photo
                photo_label.grid(row=row_idx, column=0, columnspan=2, padx=5, pady=5)
                img.close()
                row_idx += 1
            except Exception as e:
                ttk.Label(detail_frame, text=f"加载照片失败: {e}").grid(row=row_idx, column=0, columnspan=2, padx=5, pady=5, sticky="w")
                row_idx += 1
        else:
            ttk.Label(detail_frame, text="无照片").grid(row=row_idx, column=0, columnspan=2, padx=5, pady=5, sticky="w")
            row_idx += 1
        
        def create_text_field(parent, label_text, value, row):
            ttk.Label(parent, text=label_text).grid(row=row, column=0, padx=5, pady=2, sticky="w")
            text_widget = tk.Text(parent, wrap=tk.WORD, height=1, state=tk.NORMAL, width=50)
            text_widget.insert(tk.END, value if value is not None else "")
            text_widget.config(state=tk.DISABLED)
            text_widget.grid(row=row, column=1, padx=5, pady=2, sticky="ew")
            text_widget.bind("<Button-3>", lambda event: self.show_copy_menu(event, text_widget))
            return text_widget

        create_text_field(detail_frame, "省份:", address_data[1], row_idx); row_idx += 1
        create_text_field(detail_frame, "城市:", address_data[2], row_idx); row_idx += 1
        create_text_field(detail_frame, "详细地址:", address_data[3], row_idx); row_idx += 1
        create_text_field(detail_frame, "完整地址:", address_data[4], row_idx); row_idx += 1
        if address_data[5]: create_text_field(detail_frame, "备注:", address_data[5], row_idx); row_idx += 1
        if address_data[6]: create_text_field(detail_frame, "电话:", address_data[6], row_idx); row_idx += 1
        if address_data[7]: create_text_field(detail_frame, "微信:", address_data[7], row_idx); row_idx += 1
        if address_data[8]: create_text_field(detail_frame, "QQ:", address_data[8], row_idx); row_idx += 1
        if address_data[9]: create_text_field(detail_frame, "价格:", address_data[9], row_idx); row_idx += 1
        if address_data[10]: create_text_field(detail_frame, "项目:", address_data[10], row_idx); row_idx += 1
        if address_data[12]: create_text_field(detail_frame, "年龄:", address_data[12], row_idx); row_idx += 1
        if address_data[13]: create_text_field(detail_frame, "时长(小时):", address_data[13], row_idx); row_idx += 1
        if address_data[14]: create_text_field(detail_frame, "身高:", address_data[14], row_idx); row_idx += 1
        if address_data[15]: create_text_field(detail_frame, "体重:", address_data[15], row_idx); row_idx += 1

        if photo_path:
            copy_photo_path_button = ttk.Button(detail_frame, text="复制照片路径", command=lambda: self.copy_to_clipboard(photo_path))
            copy_photo_path_button.grid(row=row_idx, column=0, columnspan=2, padx=5, pady=5, sticky="e")
            row_idx += 1

        close_button = ttk.Button(detail_frame, text="关闭", command=popup.destroy)
        close_button.grid(row=row_idx, column=0, columnspan=2, padx=5, pady=5, sticky="e")
        row_idx += 1

        popup.update_idletasks()
        width = detail_frame.winfo_reqwidth() + 20
        height = detail_frame.winfo_reqheight() + 20
        popup.geometry(f"{width}x{height}")

        popup.protocol("WM_DELETE_WINDOW", lambda: self.on_popup_close(popup))

    def on_popup_close(self, popup):
        popup.grab_release()
        popup.destroy()

    def show_copy_menu(self, event, text_widget):
        menu = tk.Menu(text_widget, tearoff=0)
        menu.add_command(label="复制", command=lambda: self.copy_text_from_widget(text_widget))
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def copy_text_from_widget(self, text_widget):
        try:
            selected_text = text_widget.get(tk.SEL_FIRST, tk.SEL_LAST)
            if selected_text:
                self.root.clipboard_clear()
                self.root.clipboard_append(selected_text)
                messagebox.showinfo("成功", "选中内容已复制到剪贴板")
        except tk.TclError: # 捕获没有选中任何文本的错误
            messagebox.showwarning("无选中", "请选中要复制的文本。")
        except Exception as e:
            messagebox.showerror("复制失败", f"复制内容到剪贴板失败: {e}")

    def copy_to_clipboard(self, text):
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        messagebox.showinfo("成功", "内容已复制到剪贴板")

    def load_uploaded_photos_listbox(self):
        """从 data.json 读取数据并填充已上传照片列表框"""
        self.uploaded_photos_listbox.delete(0, tk.END)
        try:
            if os.path.exists(self.data_file_path) and os.path.getsize(self.data_file_path) > 0:
                with open(self.data_file_path, 'r', encoding='utf-8-sig') as f:
                    data = json.load(f)
                for i, item in enumerate(data):
                    display_text = f"[{i}] {item.get('full_address', 'N/A')} - {os.path.basename(item.get('photo_path', 'N/A'))}"
                    self.uploaded_photos_listbox.insert(tk.END, display_text)
            else:
                self.uploaded_photos_listbox.insert(tk.END, "暂无照片")
        except json.JSONDecodeError as e:
            messagebox.showerror("JSON 错误", f"data.json 文件格式不正确: {e}")
        except Exception as e:
            messagebox.showerror("读取错误", f"加载已上传照片列表失败: {e}")

    def delete_selected_uploaded_photo(self):
        """删除选中的已上传照片及其信息"""
        selected_indices = self.uploaded_photos_listbox.curselection()
        if not selected_indices:
            messagebox.showwarning("未选中", "请在列表中选择要删除的照片。")
            return

        if messagebox.askyesno("确认删除", f"确定要删除选中的 {len(selected_indices)} 张照片及其信息吗？此操作将更新网站。"):
            messagebox.showinfo("删除照片", "照片删除操作将在后台进行，应用程序将保持响应。", parent=self.root)
            
            # 在新线程中执行删除逻辑
            delete_thread = threading.Thread(target=self._delete_photos_in_thread, args=(selected_indices,))
            delete_thread.start()

    def _delete_photos_in_thread(self, selected_indices):
        try:
            current_data = self.load_data()
            deleted_count = 0
            files_deleted = []

            # 按倒序遍历，避免删除元素时影响后续索引的正确性
            for index in sorted(selected_indices, reverse=True):
                if 0 <= index < len(current_data):
                    deleted_item = current_data.pop(index)

                    # 删除图片文件
                    photo_file_to_delete = os.path.join(self.base_dir, deleted_item.get('photo_path', ''))
                    if os.path.exists(photo_file_to_delete):
                        print(f"Attempting to delete: {photo_file_to_delete}") # 新增：打印尝试删除的文件路径
                        os.remove(photo_file_to_delete)
                        files_deleted.append(os.path.basename(photo_file_to_delete))
                    deleted_count += 1
                else:
                    print(f"Warn: Skipping invalid index {index}") # 调试信息

            if deleted_count > 0:
                # 写回更新后的数据
                self.save_data(current_data)
                
                messagebox.showinfo("成功", f"已成功删除 {deleted_count} 张照片信息。\n已删除文件: {', '.join(files_deleted[:3])}{'...' if len(files_deleted) > 3 else ''}", parent=self.root)
                self.load_uploaded_photos_listbox() # 刷新列表
                
                # 执行 Git 命令并推送到 GitHub
                # 使用更明确的提交信息
                commit_message = f"Remove {deleted_count} photos: {', '.join(files_deleted[:3])}{'...' if len(files_deleted) > 3 else ''}"
                self.run_git_commands(commit_message=commit_message)

            else:
                messagebox.showwarning("无效选择", "没有有效的照片被选中或删除。", parent=self.root)

        except Exception as e:
            # 在错误消息中包含更多详情，例如文件路径
            messagebox.showerror("删除错误", f"删除照片失败: {e}\n可能原因：文件被占用或权限不足。请检查是否有其他程序打开了此文件或目录。", parent=self.root)

    def import_info_from_db(self):
        db_file_path = filedialog.askopenfilename(title="选择 addresses.db 文件", filetypes=[("SQLite Database", "*.db"), ("All Files", "*.*")])
        if not db_file_path: # 用户取消
            return

        try:
            conn = sqlite3.connect(db_file_path)
            cursor = conn.cursor()

            # 查询所有相关字段，包括 full_address
            cursor.execute("SELECT full_address, photo_path, age, price, height, weight FROM addresses")
            rows = cursor.fetchall()

            conn.close()

            # 加载现有数据以去重，基于网页使用的 photo_path
            current_data = self.load_data()
            existing_web_photo_paths = {entry.get("photo_path") for entry in current_data if entry.get("photo_path")}

            new_entries_added = False
            for row in rows:
                full_address, db_photo_path, age, price, height, weight = row

                if db_photo_path:
                    photo_filename = os.path.basename(db_photo_path)
                    web_photo_path = f"images/{photo_filename}" # 构建网页相对路径

                    if web_photo_path not in existing_web_photo_paths:
                        new_entry = {
                            "photo_path": web_photo_path, # 网页使用此路径
                            "full_address": full_address if full_address else "无地址信息", # 确保包含完整地址
                            "age": age if age else "N/A",
                            "price": price if price else "N/A",
                            "height": height if height else "N/A",
                            "weight": weight if weight else "N/A"
                        }
                        current_data.append(new_entry)
                        existing_web_photo_paths.add(web_photo_path)
                        new_entries_added = True
                else:
                    print(f"Warn: 数据库记录 '{full_address}' 没有关联的图片路径，已跳过导入到 data.json。")

            if new_entries_added:
                self.save_data(current_data)
                messagebox.showinfo("导入成功", "旧信息已导入并去重。请确保照片文件已复制到 images 文件夹。之后会重新生成网站数据并同步。")
                self.regenerate_data_json_from_db_and_images() # 导入后立即重新生成并同步
            else:
                messagebox.showinfo("导入完成", "没有新的信息需要导入或所有信息已存在。")

        except sqlite3.Error as e:
            messagebox.showerror("数据库错误", f"读取数据库时发生错误: {e}")
        except Exception as e:
            messagebox.showerror("错误", f"导入信息时发生意外错误: {e}")

    def import_photos_from_folder(self):
        photos_folder_path = filedialog.askdirectory(title="选择旧照片文件夹 (photos)")
        if not photos_folder_path: # 用户取消
            return

        copied_count = 0
        try:
            # 确保目标 images 文件夹存在
            if not os.path.exists(self.images_dir):
                os.makedirs(self.images_dir)

            for filename in os.listdir(photos_folder_path):
                if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp')):
                    source_path = os.path.join(photos_folder_path, filename)
                    destination_path = os.path.join(self.images_dir, filename)

                    if not os.path.exists(destination_path): # 检查是否已存在，去重
                        # 使用优化函数复制照片
                        if self.optimize_image(source_path, destination_path):
                            copied_count += 1
                            print(f"Copied (optimized): {filename}")
                        else:
                            print(f"Failed to optimize or copy: {filename}")
                    else:
                        print(f"Skipped (already exists): {filename}")

            if copied_count > 0:
                messagebox.showinfo("导入成功", f"已成功导入并优化 {copied_count} 张新照片到 images 文件夹。正在更新网站。")
                # 调用新的同步函数，确保网站数据与数据库和图片文件夹一致
                self.regenerate_data_json_from_db_and_images()
            else:
                messagebox.showinfo("导入完成", "没有新的照片需要导入或所有照片已存在。")

        except Exception as e:
            messagebox.showerror("错误", f"导入照片时发生意外错误: {e}")

    def regenerate_data_json_from_db_and_images(self):
        """
        从 SQLite 数据库和 images 文件夹重新生成 data.json 文件，并同步到 GitHub。
        这个函数是确保网站数据与本地数据一致的核心。
        """
        messagebox.showinfo("同步网站数据", "正在从数据库和本地图片重新生成网站数据，并准备同步到 GitHub Pages，这可能需要一些时间。", parent=self.root)

        def _regenerate_and_sync_in_thread():
            # 在新线程中创建独立的数据库连接和游标
            conn_thread = None
            cursor_thread = None
            try:
                conn_thread = sqlite3.connect(os.path.join(self.base_dir, 'addresses.db'))
                cursor_thread = conn_thread.cursor()

                cursor_thread.execute("SELECT full_address, photo_path, age, price, height, weight FROM addresses")
                db_data = cursor_thread.fetchall()

                website_data = []
                for row in db_data:
                    full_address, db_photo_path, age, price, height, weight = row

                    if db_photo_path:
                        photo_filename = os.path.basename(db_photo_path)
                        web_photo_path = f"images/{photo_filename}"
                        
                        local_image_path = os.path.join(self.images_dir, photo_filename)
                        if os.path.exists(local_image_path):
                            website_data.append({
                                "photo_path": web_photo_path,
                                "full_address": full_address if full_address else "无地址信息",
                                "age": age if age else "N/A",
                                "price": price if price else "N/A",
                                "height": height if height else "N/A",
                                "weight": weight if weight else "N/A"
                            })
                        else:
                            print(f"Warn: 图片文件 '{photo_filename}' 不存在于 images 文件夹，已跳过其信息。")
                    else:
                        print(f"Warn: 数据库记录 '{full_address}' 没有关联的图片路径，已跳过。")
                
                self.save_data(website_data)
                messagebox.showinfo("同步完成", "网站数据 (data.json) 已成功更新。现在将推送到 GitHub Pages。", parent=self.root)
                self.load_uploaded_photos_listbox() # 刷新列表框
                self.run_git_commands(commit_message="Regenerate data.json and sync website")

            except Exception as e:
                messagebox.showerror("同步失败", f"重新生成网站数据失败: {e}", parent=self.root)
            finally:
                if cursor_thread: # 确保关闭游标
                    cursor_thread.close()
                if conn_thread: # 确保关闭连接
                    conn_thread.close()
            
        sync_thread = threading.Thread(target=_regenerate_and_sync_in_thread)
        sync_thread.start()

    def create_key_management_widgets(self, parent_frame):
        key_frame = tk.LabelFrame(parent_frame, text="生成新密钥", bg='#e0e0e0', fg='#333333')
        key_frame.pack(padx=10, pady=10, fill="x", expand=True)

        ttk.Label(key_frame, text="密钥类型:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.key_type_var = tk.StringVar()
        self.key_type_combobox = ttk.Combobox(key_frame, textvariable=self.key_type_var, state="readonly",
                                              values=["试看密钥 (30分钟)", "选时密钥 (小时)", "长期密钥 (永久)"])
        self.key_type_combobox.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        self.key_type_combobox.set("试看密钥 (30分钟)") # 默认选择
        self.key_type_combobox.bind("<<ComboboxSelected>>", self.on_key_type_select)

        self.duration_label = ttk.Label(key_frame, text="时长 (小时):")
        self.duration_label.grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.duration_entry = ttk.Entry(key_frame, width=20)
        self.duration_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        self.duration_label.grid_remove() # 默认隐藏
        self.duration_entry.grid_remove() # 默认隐藏

        generate_button = ttk.Button(key_frame, text="生成密钥", command=self.generate_and_save_key)
        generate_button.grid(row=2, column=1, padx=5, pady=5, sticky="e")

        ttk.Label(key_frame, text="生成密钥:").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.generated_key_display = ttk.Entry(key_frame, width=40, state="readonly")
        self.generated_key_display.grid(row=3, column=1, padx=5, pady=5, sticky="ew")
        ttk.Button(key_frame, text="复制", command=lambda: self.copy_to_clipboard(self.generated_key_display.get())).grid(row=3, column=2, padx=5, pady=5)

        key_frame.grid_columnconfigure(1, weight=1)

        # 已生成密钥列表区域
        list_frame = tk.LabelFrame(parent_frame, text="已生成密钥", bg='#e0e0e0', fg='#333333')
        list_frame.pack(padx=10, pady=10, fill="both", expand=True)

        self.keys_listbox = tk.Listbox(list_frame, height=10)
        self.keys_listbox.pack(padx=5, pady=5, fill="both", expand=True)

        key_buttons_frame = ttk.Frame(list_frame)
        key_buttons_frame.pack(pady=5)

        delete_key_button = ttk.Button(key_buttons_frame, text="删除选中密钥", command=self.delete_selected_key)
        delete_key_button.pack(side=tk.LEFT, padx=5)

        sync_keys_button = ttk.Button(key_buttons_frame, text="同步密钥到网站", command=self.export_keys_for_frontend)
        sync_keys_button.pack(side=tk.LEFT, padx=5)

        self.load_keys_listbox()

    def on_key_type_select(self, event=None):
        selected_type = self.key_type_var.get()
        if "选时密钥" in selected_type:
            self.duration_label.grid()
            self.duration_entry.grid()
        else:
            self.duration_label.grid_remove()
            self.duration_entry.grid_remove()

    def generate_and_save_key(self):
        import hashlib
        import time
        import uuid
        from datetime import datetime, timedelta

        key_type = self.key_type_var.get()
        generated_key = str(uuid.uuid4())
        expiration_time = None # Unix timestamp

        if "试看密钥" in key_type:
            expiration_time = (datetime.now() + timedelta(minutes=30)).timestamp()
        elif "选时密钥" in key_type:
            try:
                duration_hours = float(self.duration_entry.get().strip())
                expiration_time = (datetime.now() + timedelta(hours=duration_hours)).timestamp()
            except ValueError:
                messagebox.showwarning("输入错误", "请为选时密钥输入有效的时长(小时)。")
                return
        # 长期密钥 expiration_time 保持 None

        key_hash = hashlib.sha256(generated_key.encode()).hexdigest()

        try:
            # 存储实际密钥和哈希值，方便用户查看和复制
            self.cursor.execute("INSERT INTO keys (key_hash, key_type, expiration_time, plain_key) VALUES (?, ?, ?, ?)",
                                (key_hash, key_type, expiration_time, generated_key))
            self.conn.commit()
            self.generated_key_display.config(state="normal")
            self.generated_key_display.delete(0, tk.END)
            self.generated_key_display.insert(0, generated_key)
            self.generated_key_display.config(state="readonly")
            messagebox.showinfo("成功", "密钥生成成功！请妥善保存生成的密钥。")
            self.load_keys_listbox()
        except Exception as e:
            messagebox.showerror("错误", f"生成密钥失败: {e}")

    def load_keys_listbox(self):
        from datetime import datetime
        self.keys_listbox.delete(0, tk.END)
        try:
            self.cursor.execute("SELECT id, key_type, expiration_time, plain_key FROM keys")
            keys_data = self.cursor.fetchall()
            self.active_keys_in_listbox = []

            for key_id, key_type, expiration_time, plain_key in keys_data:
                status_text = "永久有效"
                if expiration_time is not None:
                    exp_dt = datetime.fromtimestamp(expiration_time)
                    if exp_dt > datetime.now():
                        status_text = f"有效期至: {exp_dt.strftime('%Y-%m-%d %H:%M')}"
                    else:
                        status_text = "已过期"
                
                display_text = f"[{key_type}] {plain_key[:8]}... - {status_text}"
                self.keys_listbox.insert(tk.END, display_text)
                self.active_keys_in_listbox.append((key_id, key_type, expiration_time, plain_key)) # 存储完整的键数据
        except Exception as e:
            print(f"加载密钥列表失败: {e}")
            messagebox.showerror("错误", f"加载密钥列表失败: {e}")

    def delete_selected_key(self):
        selected_indices = self.keys_listbox.curselection()
        if not selected_indices:
            messagebox.showwarning("未选中", "请选择要删除的密钥。")
            return

        keys_to_delete_ids = [self.active_keys_in_listbox[i][0] for i in selected_indices]

        if messagebox.askyesno("确认删除", f"确定要删除选中的 {len(keys_to_delete_ids)} 个密钥吗？"):
            try:
                placeholders = ', '.join('?' for _ in keys_to_delete_ids)
                self.cursor.execute(f"DELETE FROM keys WHERE id IN ({placeholders})", keys_to_delete_ids)
                self.conn.commit()
                messagebox.showinfo("成功", "密钥删除成功。")
                self.load_keys_listbox()
                self.export_keys_for_frontend() # 删除后重新同步到网站
            except Exception as e:
                messagebox.showerror("删除错误", f"删除密钥失败: {e}")

    def export_keys_for_frontend(self):
        import hashlib
        import time
        from datetime import datetime

        keys_config_path = os.path.join(self.base_dir, 'keys_config.json')
        
        exported_keys = []
        try:
            self.cursor.execute("SELECT key_hash, key_type, expiration_time FROM keys")
            all_keys = self.cursor.fetchall()

            for key_hash, key_type, expiration_time in all_keys:
                if expiration_time is None or datetime.fromtimestamp(expiration_time) > datetime.now():
                    exported_keys.append({
                        "hash": key_hash,
                        "type": key_type,
                        "exp": expiration_time # Store raw timestamp
                    })
            
            with open(keys_config_path, 'w', encoding='utf-8') as f:
                json.dump(exported_keys, f, indent=4, ensure_ascii=False)
            
            messagebox.showinfo("成功", "有效密钥已成功导出到 keys_config.json 文件。正在准备同步到 GitHub Pages。")
            self.run_git_commands(commit_message="Sync valid keys_config.json to website")

        except Exception as e:
            messagebox.showerror("导出错误", f"导出密钥到 keys_config.json 失败: {e}")

    def __del__(self):
        if hasattr(self, 'conn') and self.conn:
            self.conn.close()

if __name__ == "__main__":
    root = tk.Tk()
    app = AddressManagerApp(root)
    root.mainloop()
