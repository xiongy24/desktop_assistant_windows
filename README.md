# 桌面助手

桌面助手是一个简单而实用的 Windows 应用程序，它可以悬浮在您的桌面右上角，随时为您提供快速截图和记录想法的功能。

## 功能

1. **截图**：一键捕获整个屏幕的截图。
2. **记录想法**：快速记录灵感和想法。
3. **始终置顶**：窗口总是显示在其他应用程序之上。
4. **可拖动**：可以自由移动窗口到屏幕上的任何位置。
5. **右上角显示**：程序启动时自动显示在屏幕右上角。

## 安装

1. 下载 `PandaAssistant.exe` 文件。
2. 双击运行 `PandaAssistant.exe`。

## 使用方法

1. 运行 `PandaAssistant.exe` 文件。
2. 桌面助手窗口将出现在您的屏幕右上角。
3. 点击相应的按钮来使用不同的功能。
4. 所有生成的文件都会保存在桌面的 `PandaAssistant` 文件夹中。

## 文件保存位置

所有由程序生成的文件和文件夹都位于桌面的 `PandaAssistant` 文件夹中，包括：

- 截图
- 想法记录
- 自由写作
- 带截图的想法

## 开机自启动（Windows）

1. 按下 `Win + R`，输入 `shell:startup`，然后按回车键。
2. 将 `PandaAssistant.exe` 的快捷方式复制到打开的文件夹中。

现在，每次 Windows 启动时，桌面助手都会自动运行。

## 将 Python 文件转换为 .exe 文件

如果您想自定义程序并创建自己的 .exe 文件，请按照以下步骤操作：

1. 确保您的系统上安装了 Python（推荐 Python 3.7 或更高版本）。

2. 安装所需的依赖项：
   ```bash
   pip install PyQt5 pyautogui pillow pywin32 html2text pyinstaller
   ```

3. 下载 `desktop_assistant.py` 文件。

4. 打开命令提示符或 PowerShell，导航到包含 `desktop_assistant.py` 文件的目录。

5. 运行以下命令来创建 .exe 文件：
   ```bash
   pyinstaller --onefile --windowed --add-data "photo.png;." --hidden-import win32gui desktop_assistant.py
   ```

6. 生成的 .exe 文件将位于新创建的 `dist` 文件夹中。

注意：生成的 .exe 文件可能会被一些杀毒软件误报为病毒。这是因为 PyInstaller 生成的文件结构类似于某些恶意软件。您可能需要将其添加到杀毒软件的白名单中。

## 注意事项

- 如果您想关闭程序，可以右键点击任务栏中的图标并选择退出。

## 自定义

如果您需要修改程序的功能或界面，可以编辑 `desktop_assistant.py` 文件，然后按照上述步骤重新生成 .exe 文件。

## 贡献

欢迎提出建议和改进意见！如果您有任何想法，请随时联系开发者。

## 许可

本项目采用 MIT 许可证。详情请见 [LICENSE](LICENSE) 文件。
