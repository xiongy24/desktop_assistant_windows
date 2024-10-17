import sys
import os
import win32gui
import win32ui
import win32con
import win32api
from ctypes import windll
from PIL import Image
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QLabel, QDialog, QLineEdit, QTextEdit, QPlainTextEdit, QMessageBox, QDesktopWidget
from PyQt5.QtCore import Qt, QPoint, QTimer
from PyQt5.QtGui import QPainter, QPixmap, QColor, QPen, QBrush, QPainterPath, QImage, QTextDocument, QKeySequence
import datetime
import webbrowser
import uuid
import json
import shutil
import time

print("Imports successful")

class ImageTextEdit(QTextEdit):
    def __init__(self, parent=None, temp_image_folder=None):
        super().__init__(parent)
        self.parent = parent
        self.temp_image_folder = temp_image_folder

    def keyPressEvent(self, event):
        if event.matches(QKeySequence.Paste):
            mime_data = QApplication.clipboard().mimeData()
            if mime_data.hasImage():
                image = QImage(mime_data.imageData())
                if not image.isNull():
                    image_id = str(uuid.uuid4())
                    image_filename = f"{image_id}.png"
                    image_path = os.path.join(self.temp_image_folder, image_filename)
                    image.save(image_path)
                    self.insertPlainText(f"![Image]({image_filename})")
                    return
        super().keyPressEvent(event)

class PandaAssistant(QWidget):
    def __init__(self):
        super().__init__()
        # 获取桌面路径
        self.desktop_path = os.path.join(os.path.expanduser('~'), 'Desktop')
        # 创建 PandaAssistant 文件夹路径
        self.panda_assistant_folder = os.path.join(self.desktop_path, 'PandaAssistant')
        # 确保 PandaAssistant 文件夹存在
        os.makedirs(self.panda_assistant_folder, exist_ok=True)
        
        # 更新 image_folder 路径
        self.image_folder = os.path.join(self.panda_assistant_folder, "Images")
        os.makedirs(self.image_folder, exist_ok=True)
        
        self.last_screenshot_folder = None
        self.last_screenshot_filename = None
        self.idea_click_count = 0
        self.idea_click_timer = QTimer()
        self.idea_click_timer.timeout.connect(self.reset_idea_click_count)
        self.last_free_writing_file = None
        self.initUI()

    def initUI(self):
        self.setWindowTitle('助手')
        self.setGeometry(100, 100, 300, 400)  # 调整窗口大小
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)

        # 将窗口移动到右上角
        self.move_to_top_right()

        # 加载背景图片
        current_dir = os.path.dirname(os.path.abspath(__file__))
        image_path = os.path.join(current_dir, 'photo.png')
        self.background = QPixmap(image_path)

        # 创建主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)  # 设置边距
        main_layout.setSpacing(5)  # 减小控件之间的间距

        # 添加一个弹簧，将按钮推底部
        main_layout.addStretch(1)

        # 创建按钮并连接事件
        screenshot_btn = self.create_transparent_button('记录灵感')
        screenshot_btn.clicked.connect(lambda: self.take_screenshot("记录灵感"))

        drifting_thoughts_btn = self.create_transparent_button('记录想法')
        drifting_thoughts_btn.clicked.connect(lambda: self.take_screenshot("记录想法"))

       
        idea_layout = QHBoxLayout()
        idea_btn_separate = self.create_transparent_button('自由撰写')
        idea_btn_separate.clicked.connect(self.free_writing)
        idea_btn_with_screenshot = self.create_transparent_button('（给截图）添加文字')
        idea_btn_with_screenshot.clicked.connect(self.add_idea_with_screenshot)
        idea_layout.addWidget(idea_btn_separate)
        idea_layout.addWidget(idea_btn_with_screenshot)

        ask_gpt_btn = self.create_transparent_button('问问GPT')
        ask_gpt_btn.clicked.connect(self.open_chatgpt)

        close_btn = self.create_transparent_button('关闭')
        close_btn.clicked.connect(self.close)

        # 将按钮添加到主布局（从上往下，但位于底部）
        main_layout.addWidget(screenshot_btn)
        main_layout.addWidget(drifting_thoughts_btn)
        main_layout.addLayout(idea_layout)
        main_layout.addWidget(ask_gpt_btn)
        main_layout.addWidget(close_btn)

        self.setLayout(main_layout)

        self.oldPos = self.pos()

    def create_transparent_button(self, text):
        button = QPushButton(text, self)
        button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                color: #87CEFA;  /* 淡蓝色 */
                padding: 5px;
                font-weight: bold;
                font-size: 18px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 30);
            }
            QPushButton:pressed {
                background-color: rgba(255, 255, 255, 50);
            }
        """)
        return button

    def take_screenshot(self, folder_name):
        screenshot_folder = os.path.join(self.panda_assistant_folder, folder_name)
        os.makedirs(screenshot_folder, exist_ok=True)
        self.hide()
        time.sleep(0.5)  # 给一点时间让窗口完全隐藏
        screen = QApplication.primaryScreen()
        screenshot = screen.grabWindow(0)
        self.show()

        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        self.last_screenshot_filename = os.path.join(screenshot_folder, f"screenshot_{timestamp}.png")
        screenshot.save(self.last_screenshot_filename, 'png')
        print(f"Screenshot saved as {self.last_screenshot_filename}")

    def on_idea_btn_clicked(self):
        self.idea_click_count += 1
        self.idea_click_timer.start(500)  # 500 ms timeout
        self.record_idea()

    def reset_idea_click_count(self):
        self.idea_click_count = 0

    def record_idea(self, with_screenshot):
        dialog = IdeaDialog(self, with_screenshot, self.last_screenshot_filename)
        if dialog.exec_():
            title = dialog.title_edit.text()
            content = dialog.content_edit.toPlainText()
            
            if with_screenshot and self.last_screenshot_folder and self.last_screenshot_filename:
                # 保存带截图的想法
                base_filename = os.path.splitext(self.last_screenshot_filename)[0]
                file_path = os.path.join(self.last_screenshot_folder, f"{base_filename}.md")
                screenshot_relative_path = os.path.basename(self.last_screenshot_filename)
                
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(f"# {title}\n\n")
                    f.write(f"![Screenshot]({screenshot_relative_path})\n\n")
                    f.write(f"{content}\n")
            else:
                # 保存普通想法
                idea_folder = os.path.join(self.panda_assistant_folder, "Idea log")
                os.makedirs(idea_folder, exist_ok=True)
                timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
                file_path = os.path.join(idea_folder, f"{timestamp}.md")
                
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(f"# {title}\n\n")
                    f.write(f"{content}\n")

            print(f"Idea saved as {file_path}")

    def mousePressEvent(self, event):
        self.oldPos = event.globalPos()

    def mouseMoveEvent(self, event):
        delta = QPoint(event.globalPos() - self.oldPos)
        self.move(self.x() + delta.x(), self.y() + delta.y())
        self.oldPos = event.globalPos()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)

        # 计算缩放后的图片大小，保持原始比例
        scaled_pixmap = self.background.scaled(self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)

        # 计算图片在窗口中的位置，使其居中
        x = (self.width() - scaled_pixmap.width()) // 2
        y = (self.height() - scaled_pixmap.height()) // 2

        # 绘制背景图片
        painter.drawPixmap(x, y, scaled_pixmap)

    def closeEvent(self, event):
        QApplication.quit()  # 这将关闭整个应用，包括终端窗口

    def open_chatgpt(self):
        webbrowser.open('https://chatgpt.com/')

    def free_writing(self):
        self.hide()  # 隐藏主窗口
        dialog = FreeWritingDialog(self)
        if dialog.exec_():
            self.save_free_writing(dialog.title_edit.text(), dialog.content_edit.toPlainText(), "自由撰写", dialog.temp_image_folder)
        self.show()  # 重新显示主窗口

    def add_idea_with_screenshot(self):
        self.take_screenshot("（给截图）添加文字")
        dialog = IdeaWithScreenshotDialog(self, self.last_screenshot_filename)
        if dialog.exec_():
            self.save_idea_with_screenshot(dialog.title_edit.text(), dialog.content_edit.toPlainText())

    def save_free_writing(self, title, content, folder_name, temp_image_folder):
        idea_folder = os.path.join(self.panda_assistant_folder, folder_name)
        os.makedirs(idea_folder, exist_ok=True)
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        file_path = os.path.join(idea_folder, f"{timestamp}.md")

        # 创建一个与 Markdown 文件同名的图片文件夹
        image_folder = os.path.join(idea_folder, f"{timestamp}_images")
        os.makedirs(image_folder, exist_ok=True)

        # 处理图片
        content = self.process_images_for_markdown(content, temp_image_folder, image_folder)

        full_content = f"# {title}\n\n{content}"

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(full_content)

        print(f"Free writing saved as {file_path}")

        # 保存最后编辑的文件路径
        self.last_free_writing_file = file_path

        # 删除临时图片文件夹
        shutil.rmtree(temp_image_folder)

    def process_images_for_markdown(self, content, source_folder, target_folder):
        import re

        def replace_image(match):
            image_filename = match.group(1)
            source_path = os.path.join(source_folder, image_filename)
            target_path = os.path.join(target_folder, image_filename)
            
            if os.path.exists(source_path):
                shutil.copy2(source_path, target_path)
                return f"![Image]({os.path.basename(target_folder)}/{image_filename})"
            else:
                print(f"Warning: Image file not found: {source_path}")
                return match.group(0)

        pattern = r'!\[Image\]\((.+?)\)'
        return re.sub(pattern, replace_image, content)

    def save_idea_with_screenshot(self, title, content):
        idea_folder = os.path.join(self.panda_assistant_folder, "（给截图）添加文字")
        os.makedirs(idea_folder, exist_ok=True)
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        file_path = os.path.join(idea_folder, f"{timestamp}.md")

        # 创建一个与 Markdown 文件同名的图片文件夹
        image_folder = os.path.join(idea_folder, f"{timestamp}_images")
        os.makedirs(image_folder, exist_ok=True)

        # 处理图片
        content = self.process_images_for_markdown(content, self.image_folder, image_folder)

        # 复制截图到新的图片文件夹
        screenshot_filename = os.path.basename(self.last_screenshot_filename)
        shutil.copy2(self.last_screenshot_filename, os.path.join(image_folder, screenshot_filename))

        full_content = f"# {title}\n\n![Screenshot]({os.path.basename(image_folder)}/{screenshot_filename})\n\n{content}"

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(full_content)

        print(f"Idea with screenshot saved as {file_path}")

    def convert_image_tags_to_markdown(self, content):
        import re
        pattern = r'\[图片: (.+?)\]'
        return re.sub(pattern, r'![Image](\1)', content)

    def move_to_top_right(self):
        # 获取屏幕的几何信息
        screen = QDesktopWidget().screenNumber(QDesktopWidget().cursor().pos())
        screen_geometry = QDesktopWidget().screenGeometry(screen)
        
        # 计算窗口应该移动到的位置
        x = screen_geometry.width() - self.width() - 20  # 20是与幕右边缘的间距
        y = 20  # 与屏幕顶部的间距
        
        # 移动窗口
        self.move(x, y)

    def load_last_free_writing(self):
        if self.last_free_writing_file and os.path.exists(self.last_free_writing_file):
            with open(self.last_free_writing_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 分离标题和内容
            lines = content.split('\n')
            title = lines[0].lstrip('# ')
            content = '\n'.join(lines[2:])

            return title, content
        return None, None

class IdeaDialog(QDialog):
    def __init__(self, parent=None, with_screenshot=False, screenshot_filename=None):
        super().__init__(parent)
        self.with_screenshot = with_screenshot
        self.screenshot_filename = screenshot_filename
        self.initUI()

    def initUI(self):
        self.setWindowTitle('记录想法')
        self.setGeometry(100, 100, 500, 400)

        layout = QVBoxLayout()

        # 标题输入
        title_layout = QHBoxLayout()
        title_label = QLabel('标题:')
        self.title_edit = QLineEdit()
        title_layout.addWidget(title_label)
        title_layout.addWidget(self.title_edit)
        layout.addLayout(title_layout)

        # 内容输入
        self.content_edit = QPlainTextEdit()
        layout.addWidget(self.content_edit)

        # 如果有截图，显示截图文件名
        if self.with_screenshot and self.screenshot_filename:
            screenshot_label = QLabel(f"关联截图: {self.screenshot_filename}")
            layout.addWidget(screenshot_label)

        # 按钮
        button_layout = QHBoxLayout()
        save_button = QPushButton('保存')
        save_button.clicked.connect(self.accept)
        cancel_button = QPushButton('取消')
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)

        self.setLayout(layout)

class FreeWritingDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.temp_image_folder = os.path.join(parent.panda_assistant_folder, f"temp_images_{uuid.uuid4()}")
        os.makedirs(self.temp_image_folder, exist_ok=True)
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        self.title_edit = QLineEdit(self)
        self.title_edit.setPlaceholderText("输入标题")
        layout.addWidget(self.title_edit)

        # 添加提示标签
        hint_label = QLabel("提示：使用 Ctrl+V 可以粘贴图片", self)
        hint_label.setStyleSheet("color: #999999; font-style: italic;")
        hint_label.setAlignment(Qt.AlignRight)
        layout.addWidget(hint_label)

        self.content_edit = ImageTextEdit(self.parent, self.temp_image_folder)
        self.content_edit.setPlaceholderText("输入内容")
        layout.addWidget(self.content_edit)

        buttons = QHBoxLayout()
        save_button = QPushButton("保存", self)
        save_button.clicked.connect(self.accept)
        cancel_button = QPushButton("取消", self)
        cancel_button.clicked.connect(self.reject)
        open_last_button = QPushButton("打开上次", self)
        open_last_button.clicked.connect(self.open_last_file)
        buttons.addWidget(save_button)
        buttons.addWidget(cancel_button)
        buttons.addWidget(open_last_button)

        layout.addLayout(buttons)
        self.setLayout(layout)
        self.setWindowTitle("自由撰写")

    def open_last_file(self):
        title, content = self.parent.load_last_free_writing()
        if title and content:
            self.title_edit.setText(title)
            self.content_edit.setPlainText(content)
        else:
            QMessageBox.information(self, "提示", "没有找到上次编辑的文件")

    def closeEvent(self, event):
        # 删除临时图片文件夹
        shutil.rmtree(self.temp_image_folder)
        super().closeEvent(event)

class IdeaWithScreenshotDialog(QDialog):
    def __init__(self, parent=None, screenshot_filename=None):
        super().__init__(parent)
        self.parent = parent
        self.screenshot_filename = screenshot_filename
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        # 添加截图预览
        if self.screenshot_filename:
            screenshot_label = QLabel(self)
            pixmap = QPixmap(self.screenshot_filename)
            scaled_pixmap = pixmap.scaled(400, 300, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            screenshot_label.setPixmap(scaled_pixmap)
            layout.addWidget(screenshot_label)

        self.title_edit = QLineEdit(self)
        self.title_edit.setPlaceholderText("输入标题")
        layout.addWidget(self.title_edit)

        self.content_edit = ImageTextEdit(self.parent, self.parent.image_folder)
        self.content_edit.setPlaceholderText("输入内容")
        layout.addWidget(self.content_edit)

        buttons = QHBoxLayout()
        save_button = QPushButton("保存", self)
        save_button.clicked.connect(self.accept)
        cancel_button = QPushButton("取消", self)
        cancel_button.clicked.connect(self.reject)
        buttons.addWidget(save_button)
        buttons.addWidget(cancel_button)

        layout.addLayout(buttons)
        self.setLayout(layout)
        self.setWindowTitle("添加想法")

def main():
    app = QApplication(sys.argv)
    ex = PandaAssistant()
    ex.show()
    sys.exit(app.exec_())  # 使用 sys.exit() 确保程序完全退出

if __name__ == '__main__':
    main()
