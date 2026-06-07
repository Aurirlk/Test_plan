from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.alert import Alert

# 设置正确的驱动路径
service = ChromeService(executable_path="./chromedriver-mac-arm64/chromedriver")
options = webdriver.ChromeOptions()
driver = webdriver.Chrome(service=service, options=options)

# 打开网页
driver.get("https://example.com")

# 触发 confirm 弹窗
driver.execute_script("confirm('这是一个 confirm 弹窗');")

# 切换到 confirm 弹窗
alert = Alert(driver)

# 获取弹窗文本
print(alert.text)

# 点击"确定"按钮
alert.accept()

# 或者点击"取消"按钮
# alert.dismiss()

# 关闭浏览器
driver.quit()