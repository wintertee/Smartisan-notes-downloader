import json
import logging
import os
import queue
import re
import threading
import time
from datetime import datetime

import requests
import yaml
from pathvalidate import sanitize_filename
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from seleniumwire import webdriver
from seleniumwire.utils import decode
from tqdm import tqdm
from webdriver_manager.chrome import ChromeDriverManager

# 工作目录
if not os.path.exists("downloads"):
    os.mkdir("downloads")
work_dir = os.path.join("downloads", str(int(datetime.now().timestamp())))
print("当前工作目录为 " + work_dir)
if not os.path.exists(work_dir):
    os.mkdir(work_dir)

logger = logging.getLogger()
fileHandler = logging.FileHandler(os.path.join(work_dir, "debug.log"), encoding="utf-8")
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
fileHandler.setFormatter(formatter)
logger.addHandler(fileHandler)
logger.setLevel(logging.WARNING)


# 登录和下载便签JSON


def wait_load_complete(driver):
    WebDriverWait(driver, 10).until(
        lambda d: d.execute_script("return document.readyState") == "complete"
    )


chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument("--incognito")
chrome_options.add_argument("--log-level=3")


try:
    driver = webdriver.Chrome(
        service=ChromeService(ChromeDriverManager().install()), options=chrome_options
    )
except Exception as e:
    print("自动启动chromedriver失败，尝试本地chromedriver", e)
    try:
        driver = webdriver.Chrome(chrome_options=chrome_options)
    except Exception as e:
        print("本地chromedriver启动失败", e)
        print("请前往 https://chromedriver.chromium.org/ 下载符合电脑中 Chrome 版本的 ChromeDriver，放在此项目根目录下。")
        exit(1)


driver.get("https://yun.smartisan.com/")
wait_load_complete(driver)

driver.find_element(By.CLASS_NAME, "login-btn").click()
wait_load_complete(driver)

input("在浏览器中输入用户名和密码，点击登录后请在shell中回车")

cookies = driver.get_cookies()
user_agent = driver.execute_script("return navigator.userAgent;")


driver.get("https://yun.smartisan.com/#/notes")
request = driver.wait_for_request(r"index.php\?r=v2.*", timeout=30)
web_response = decode(
    request.response.body,
    request.response.headers.get("Content-Encoding", "identity"),
).decode("utf-8")

print("便签获取完成，关闭浏览器。")
driver.quit()

# 解析和保存便签JSON
web_response_dict = json.loads(web_response)

note_total = int(web_response_dict["data"]["note"]["total"])
note_list = web_response_dict["data"]["note"]["list"]

with open(os.path.join(work_dir, "web_response.json"), "w", encoding="utf-8") as f:
    f.write(web_response)


# 多线程图片下载队列

THREAD_NUM = 4
image_queue = queue.Queue()
thread_list = []


def downloader():
    s = requests.Session()
    for cookie in cookies:
        s.cookies.set(cookie["name"], cookie["value"])

    while True:
        task = image_queue.get()
        time.sleep(0.1)
        if task is None:
            image_queue.task_done()
            break

        url, filepath = task
        res = s.get(url, headers={"user-agent": user_agent})
        with open(filepath, "wb") as f:
            f.write(res.content)

        logger.debug("OK  " + url + filepath)
        logger.debug("QUEUE SIZE " + str(image_queue.qsize()))
        image_queue.task_done()


# 图片标签转为HTML格式，下载链接添加至image_queue
def image_tag_handler(matchobj):
    global subdir

    file_name = matchobj.group(4)
    image_queue.put(
        (
            "https://yun.smartisan.com/apps/note/notesimage/" + file_name,
            os.path.join(subdir, file_name),
        )
    )
    logger.debug(
        "ADD "
        + "https://yun.smartisan.com/apps/note/notesimage/"
        + file_name
        + os.path.join(subdir, file_name)
    )
    logger.debug("QUEUE SIZE " + str(image_queue.qsize()))

    return '\n<img src="{}" alt="{}" width="{}" height="{}">\n'.format(
        *matchobj.group(4, 3, 1, 2)
    )


# 逐个保存便签为Markdown格式

DATETIME_FORMAT = "%Y%m%d"

IMAGE_PATTERN = r"<image w=([0-9]+) h=([0-9]+) describe=(.*) name=(.+)>"
IMAGE_REPL = r'<img src="\\4" alt="\\3" width="\\1" height="\\2">'

for note_item in note_list:
    # 解析元数据
    content = note_item.pop("detail")
    modify_time = datetime.fromtimestamp(
        note_item["modify_time"] / 1000
    )  # millisecond to second
    note_item["modify_time_r"] = str(modify_time)  # readable time

    # 每个便签单独创建文件夹
    filename = (
        modify_time.strftime(DATETIME_FORMAT)
        + "_"
        + sanitize_filename(note_item["title"], max_len=15)
        + ".md"
    )

    subdir = os.path.join(work_dir, filename)
    if not os.path.exists(subdir):
        os.mkdir(subdir)

    # 写入Markdown
    with open(os.path.join(subdir, filename), "w", encoding="utf-8") as f:
        f.write("---\n")
        f.write(str(yaml.dump(note_item, allow_unicode=True)))  # 写入元数据
        f.write("---\n")
        f.write("\n")
        f.write(
            re.sub(IMAGE_PATTERN, image_tag_handler, content)
        )  # 写入替换图片标签后的正文

# image_tag_handler()已将图片下载链接入队完毕。添加downloader结束信号。
for _ in range(THREAD_NUM):
    image_queue.put(None)

# 创建下载线程
for _ in range(THREAD_NUM):
    t = threading.Thread(target=downloader)
    t.daemon = True
    t.start()
    thread_list.append(t)

# 使用tqdm监控队列长度
print("开始下载图片")
with tqdm(total=image_queue.qsize()) as pbar:
    initial_size = image_queue.qsize()
    while any([t.is_alive() for t in thread_list]):
        current_size = image_queue.qsize()
        pbar.update(initial_size - current_size)
        initial_size = current_size
        time.sleep(0.1)  # 每0.1秒刷新一次

# 等待线程结束
for t in thread_list:
    t.join()

# 等待队列清空
image_queue.join()
