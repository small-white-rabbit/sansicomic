import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import requests
import parsel
import os
import time
from threading import Lock
from concurrent.futures import ThreadPoolExecutor

# 2025.2.23 借助grok3 ai完成图形化界面

class ComicDownloaderGUI:
    def __init__(self, master):
        self.master = master
        master.title("漫画下载器 最终版")
        master.geometry("800x600")

        # 初始化参数
        self.headers = {
            'Referer': 'https://www.san421.com/',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        self.download_path = os.path.join(os.path.expanduser("~"), "Downloads")
        self.is_downloading = False
        self.lock = Lock()
        self.html_filename = ""
        self.comic_title = ""
        self.max_retries = 3

        # 状态跟踪
        self.total_pages = 0
        self.completed_pages = 0
        self.failed_downloads = []

        # 线程池配置
        self.thread_pool = ThreadPoolExecutor(max_workers=5)
        self.active_tasks = set()

        # 初始化界面
        self.create_widgets()

    def create_widgets(self):
        # 输入区域
        input_frame = ttk.Frame(self.master)
        input_frame.pack(pady=10, padx=10, fill=tk.X)

        # URL输入行
        url_frame = ttk.Frame(input_frame)
        url_frame.grid(row=0, column=0, columnspan=3, sticky=tk.EW)
        ttk.Label(url_frame, text="漫画链接:").pack(side=tk.LEFT)
        self.url_entry = ttk.Entry(url_frame, width=60)
        self.url_entry.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        ttk.Button(url_frame, text="粘贴",
                   command=lambda: self.paste_from_clipboard(self.url_entry),
                   width=4).pack(side=tk.LEFT)

        # 路径输入行
        path_frame = ttk.Frame(input_frame)
        path_frame.grid(row=1, column=0, columnspan=3, pady=5, sticky=tk.EW)
        ttk.Label(path_frame, text="保存路径:").pack(side=tk.LEFT)
        self.path_entry = ttk.Entry(path_frame, width=60)
        self.path_entry.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        self.path_entry.insert(0, self.download_path)
        ttk.Button(path_frame, text="浏览",
                   command=self.choose_path, width=4).pack(side=tk.LEFT)
        ttk.Button(path_frame, text="粘贴",
                   command=lambda: self.paste_from_clipboard(self.path_entry),
                   width=4).pack(side=tk.LEFT)

        # 控制按钮
        self.download_btn = ttk.Button(
            self.master,
            text="开始下载",
            command=self.toggle_download
        )
        self.download_btn.pack(pady=5)

        # 进度条区域
        progress_frame = ttk.Frame(self.master)
        progress_frame.pack(pady=5)
        self.progress = ttk.Progressbar(
            progress_frame,
            orient=tk.HORIZONTAL,
            length=500,
            mode='determinate'
        )
        self.progress.pack(side=tk.LEFT, padx=5)
        self.progress_label = ttk.Label(progress_frame, text="0.00%")
        self.progress_label.pack(side=tk.LEFT)

        # 日志区域
        log_frame = ttk.LabelFrame(self.master, text="下载日志")
        log_frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)

        # 日志文本框
        self.log_text = tk.Text(log_frame, wrap=tk.WORD, font=('Consolas', 10))
        scrollbar = ttk.Scrollbar(log_frame, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 漫画名称输出框（移到 log_frame 下方）
        self.comic_name_label = ttk.Label(self.master, text="当前漫画: 未开始", font=('Consolas', 10))
        self.comic_name_label.pack(pady=5)

        # 配置文本颜色标签
        self.log_text.tag_config("green", foreground="#4CAF50")
        self.log_text.tag_config("red", foreground="#F44336")

    def paste_from_clipboard(self, entry_widget):
        try:
            clipboard_content = self.master.clipboard_get()
            if clipboard_content.strip():
                entry_widget.delete(0, tk.END)
                entry_widget.insert(0, clipboard_content)
        except tk.TclError:
            messagebox.showwarning("粘贴失败", "剪贴板内容不可用")

    def choose_path(self):
        path = filedialog.askdirectory()
        if path:
            self.path_entry.delete(0, tk.END)
            self.path_entry.insert(0, path)

    def toggle_download(self):
        if self.is_downloading:
            self.stop_download()
        else:
            self.start_download()

    def start_download(self):
        # 重置状态
        self.progress['value'] = 0
        self.progress_label.config(text="0.00%")
        self.log_text.delete(1.0, tk.END)
        self.comic_name_label.config(text="当前漫画: 未开始")
        self.total_pages = 0
        self.completed_pages = 0
        self.failed_downloads = []

        url = self.url_entry.get()
        if not url.startswith('http'):
            messagebox.showerror("错误", "请输入有效的URL地址")
            return

        self.download_path = self.path_entry.get()
        if not os.path.exists(self.download_path):
            os.makedirs(self.download_path)

        self.is_downloading = True
        self.download_btn.config(text="停止下载")
        self.thread_pool.submit(self.get_list_url, url)

    def stop_download(self):
        self.is_downloading = False
        self.download_btn.config(text="开始下载")
        self.append_message("\n操作已终止")
        self.comic_name_label.config(text="当前漫画: 已停止")

        # 取消所有任务
        for task in self.active_tasks:
            task.cancel()
        self.active_tasks.clear()

    def update_progress(self):
        if self.total_pages > 0:
            progress = (self.completed_pages / self.total_pages) * 100
            self.progress['value'] = progress
            self.progress_label.config(text=f"{progress:.2f}%")
        self.master.update_idletasks()

    def append_log(self, log_type, data, failed=False):
        # 在主线程中实时更新日志
        def update_gui():
            if log_type == "complete":
                filename = data
                message = f"✓ 已下载: {filename.ljust(40)}"
                if failed:
                    message += f" (失败: 已达最大重试次数{self.max_retries})"
                self.log_text.insert(tk.END, message + "\n", "green" if not failed else "red")
            elif log_type == "message":
                self.log_text.insert(tk.END, data + "\n")
            self.log_text.see(tk.END)
            self.master.update_idletasks()

        self.master.after(0, update_gui)

    def append_message(self, message):
        self.append_log("message", message)

    def get_page_url(self, herf, dirnames, fir_num):
        try:
            with requests.Session() as session:
                session.headers.update(self.headers)
                res_page = session.get(herf, timeout=10)
                res_page.raise_for_status()

                res_page_img = parsel.Selector(text=res_page.text, type='html')
                end = res_page_img.xpath('//*[@class="post-page-numbers current"]/span/text()').get()
                self.append_message(f"\n第 {end} 页已进入下载队列")

                imgs = res_page_img.xpath('//*[@class="article-content"]//img/@src').getall()
                che_num = herf.split('.')[-2].split('-')[-1]
                if che_num == fir_num:
                    che_num = '1'

                tracker = PageTracker(
                    total_items=len(imgs),
                    on_complete=lambda: self.handle_page_complete()
                )

                for index, src in enumerate(imgs, start=1):
                    if not self.is_downloading:
                        return
                    filename = f"{che_num}-{index:03d}"
                    os.chdir(dirnames)

                    with open(self.html_filename, 'a', encoding='utf-8') as fdd:
                        fdd.write(
                            '<div style="text-align:center; margin:-2px 0;">\n'
                            f'  <img src="{filename}.jpg" style="max-width:100%;height:auto;">\n'
                            '</div>\n\n'
                        )

                    task = self.thread_pool.submit(
                        self.get_download,
                        src, dirnames, filename, tracker
                    )
                    self.active_tasks.add(task)
                    task.add_done_callback(lambda t: self.active_tasks.discard(t))

        except Exception as e:
            self.append_message(f"页面处理失败: {str(e)}")

    def get_download(self, src, dirnames, filename, tracker):
        retries = 0
        success = False
        while retries <= self.max_retries and not success:
            try:
                if retries > 0:
                    self.append_message(f"正在第{retries}次重试: {filename}")

                with requests.Session() as session:
                    session.headers.update(self.headers)
                    response = session.get(src, timeout=(3, 10))
                    response.raise_for_status()

                    os.chdir(dirnames)
                    with open(f'{filename}.jpg', 'wb') as fd:
                        fd.write(response.content)

                    self.append_log("complete", filename)
                    tracker.report_success()
                    success = True

            except Exception as e:
                if retries == self.max_retries:
                    self.append_log("complete", filename, failed=True)
                    with self.lock:
                        self.failed_downloads.append((src, dirnames, filename))
                    tracker.report_failure()
                retries += 1
                time.sleep(min(2 ** retries, 10))

    def handle_page_complete(self):
        with self.lock:
            self.completed_pages += 1
            self.master.after(0, self.update_progress)

        if self.completed_pages >= self.total_pages:
            failed_count = len(self.failed_downloads)
            if failed_count > 0:
                self.append_message(f"\n下载完成！失败图片数: {failed_count}")
            else:
                self.append_message("\n所有图片下载成功！")
            self.stop_download()

    def get_list_url(self, url):
        try:
            with requests.Session() as session:
                session.headers.update(self.headers)
                resp = session.get(url, timeout=10)
                resp.raise_for_status()
                resp.encoding = resp.apparent_encoding

                html = parsel.Selector(text=resp.text, type='html')
                list_href = html.xpath('//*[contains(@class,"article-paging")][1]/a/@href').getall()

                if len(list_href) > 0:
                    del list_href[-1]
                list_href.insert(0, url)

                self.total_pages = len(list_href)
                self.master.after(0, self.update_progress)

                fir_num = url.split('.')[-2].split('-')[-1]
                raw_title = html.xpath('//*[contains(@class,"article-title")]/a/text()').get().strip().split('/')[0]
                safe_title = "".join([c for c in raw_title if c not in r'\/:*?"<>|'])
                self.comic_title = safe_title

                self.append_message(f"开始下载: {self.comic_title}")
                self.append_message(f"总章节数: {self.total_pages}")
                self.comic_name_label.config(text=f"当前漫画: {self.comic_title}")

                dirnames = os.path.join(self.download_path, self.comic_title)
                if not os.path.exists(dirnames):
                    os.makedirs(dirnames)

                self.html_filename = os.path.join(dirnames, f"{self.comic_title}.html")
                with open(self.html_filename, 'w', encoding='utf-8') as f:
                    f.write(
                        '<!DOCTYPE html>\n<html>\n<head>\n'
                        f'<title>{self.comic_title}</title>\n'
                        '<meta charset="utf-8">\n'
                        '<style>\n'
                        'body { background: #2d2d2d; margin: 0; padding: -2px; }\n'
                        '.page { margin: -2px auto; max-width: 1000px; }\n'
                        'img { box-shadow: 0 2px 5px rgba(0,0,0,0.3); }\n'
                        '</style>\n</head>\n<body>\n'
                    )

                for i in list_href:
                    if not self.is_downloading:
                        break
                    self.get_page_url(i, dirnames, fir_num)

                with open(self.html_filename, 'a', encoding='utf-8') as f:
                    f.write('</body>\n</html>')

        except Exception as e:
            self.append_message(f"初始化失败: {str(e)}")
            self.stop_download()


class PageTracker:
    def __init__(self, total_items, on_complete):
        self.lock = Lock()
        self.total = total_items
        self.success = 0
        self.failed = 0
        self.callback = on_complete

    def report_success(self):
        with self.lock:
            self.success += 1
            self._check_completion()

    def report_failure(self):
        with self.lock:
            self.failed += 1
            self._check_completion()

    def _check_completion(self):
        if self.success + self.failed >= self.total:
            self.callback()


if __name__ == "__main__":
    root = tk.Tk()
    app = ComicDownloaderGUI(root)
    root.mainloop()

# 打包命令（在命令行中运行）：
# pyinstaller --onefile --noconsole comic_downloader.py
# 可选：添加图标
# pyinstaller --onefile --noconsole --icon=icon.ico comic_downloader.py
