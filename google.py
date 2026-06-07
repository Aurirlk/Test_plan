from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# 创建一个 Options 对象
chrome_options = Options()

# 添加参数来禁止日志输出
# 这会告诉 ChromeDriver 只报告严重的错误
chrome_options.add_argument("--log-level=3") 
chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])

# 在初始化 Chrome 时传入这些选项
driver = webdriver.Chrome(options=chrome_options)

driver.get('https://www.google.com')
print(driver.title) # 依然会输出：Google
driver.quit()

