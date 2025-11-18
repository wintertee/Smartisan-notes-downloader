# Smartisan-notes-downloader

个人用的锤子便签下载器。只在自己的账号上测试通过（1500条便签）。

## 使用方法（使用pip）
- 安装 Python3
- 安装 Chrome
- 安装依赖: `pip install -r requirements.txt`
- 运行程序：`python main.py`

## 使用方法（使用uv）
- 安装uv
- 安装Chrome
- 运行程序 `uv run main.py`

## 注意事项
- 需要根据本机安装的浏览器版本，手动下载对应的WebDriver，将可执行文件放入本项目的根目录下
  - 请前往 https://chromedriver.chromium.org/ 下载符合电脑中 Chrome 版本的 ChromeDriver，放在此项目根目录下
  - 请前往 https://developer.microsoft.com/microsoft-edge/tools/webdriver/ 下载符合电脑中 Edge 版本的驱动，放在此项目根目录下
  - 也可以使用`--driver-path`参数指定WebDriver的Path
- 使用Edge浏览器，需要加入`--browser edge`参数
- 如果使用测试版本，需要手动指定测试版本浏览器的binary路径
  - 以Edge Beta为例
  ~~~python
  edge_options.binary_location = (
    "/Applications/Microsoft Edge Beta.app/Contents/MacOS/Microsoft Edge Beta"
    )
    ~~~
