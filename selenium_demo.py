from selenium import webdriver
from selenium.webdriver.common.by import By
import time

driver = webdriver.Chrome()
driver.get("https://www.baidu.com")
driver.maximize_window()
time.sleep(2)
search_box = driver.find_element(By.ID, "kw")
search_box.send_keys("软件测试工具")
time.sleep(1)
search_button = driver.find_element(By.ID, "su")
search_button.click()
time.sleep(3)
selenium_link = driver.find_element(By.LINK_TEXT, "Selenium - 开源中国")
selenium_link.click()
time.sleep(3)
driver.quit()