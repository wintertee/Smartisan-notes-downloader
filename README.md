# Smartisan-notes-downloader

个人用的锤子便签下载器。只在自己的账号上测试通过（1500条便签）。

## 使用方法（推荐：使用uv）

* 安装 [uv](https://docs.astral.sh/uv/)
* 安装 Chrome 或 Edge 浏览器
* 运行程序：`uv run main.py`

## 使用方法（传统方法：使用pip）

* 安装 Python3
* 安装 Chrome 或 Edge 浏览器
* 安装依赖：`pip install -r requirements.txt`
* 运行程序：`python main.py`

## 注意事项

* WebDriver 会自动下载，无需手动安装
* 默认使用 Chrome 浏览器，如需使用 Edge，请添加参数：`uv run main.py --browser edge`
* 如果自动下载失败，可以手动下载 WebDriver 并使用 `--driver-path` 参数指定路径：
  + Chrome: https://chromedriver.chromium.org/
  + Edge: https://developer.microsoft.com/microsoft-edge/tools/webdriver/
  + 示例：`uv run main.py --driver-path ./chromedriver.exe`
* 如果使用测试版本浏览器（如 Edge Beta），需要在 `main.py` 中手动指定 binary 路径：
  ~~~python
  # 取消注释并修改以下代码
  edge_options.binary_location = (

    "/Applications/Microsoft Edge Beta.app/Contents/MacOS/Microsoft Edge Beta"

  )
  ~~~
