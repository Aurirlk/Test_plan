from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time

class BaiduSearcher:
    def __init__(self, headless=False, implicit_wait=0, debug_prefix="debug"):
        # 添加参数来禁止日志输出
        # 这会告诉 ChromeDriver 只报告严重的错误
        options = Options()
        options.add_experimental_option('excludeSwitches', ['enable-automation', 'enable-logging'])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument("--disable-blink-features=AutomationControlled")
        if headless:
            options.add_argument("--headless=new")  
        options.add_argument("--log-level=3")

        self.driver = webdriver.Chrome(options=options)
        if implicit_wait:
            self.driver.implicitly_wait(implicit_wait)
        self.wait = WebDriverWait(self.driver, 10)
        self.search_box = None
        self.search_type = None
        self.debug_prefix = debug_prefix

    def try_use_visible_input(self, query):
        """尝试找到可见的传统输入框并输入（兼容旧版）"""
        inputs = self.driver.find_elements(By.CSS_SELECTOR, "input#kw, input.s_ipt, input[type='search']")
        for inp in inputs:
            try:
                if inp.is_displayed() and inp.is_enabled():
                    inp.click()
                    inp.clear()
                    inp.send_keys(query)
                    print("  - 使用可见传统输入框输入完成")
                    return True
            except Exception:
                continue
        return False

    def try_js_inject_and_click(self, query):
        """使用 JS 注入 value 并尝试点击按钮（绕过遮罩/虚拟层）"""
        js = """
        (function(q){
          var input = document.querySelector('#chat-textarea') 
                   || document.querySelector('input#kw') 
                   || document.querySelector('input.s_ipt') 
                   || document.querySelector("input[type='search']");
          if (input) {
            input.focus();
            try { input.value = q; } catch(e) {}
            var ev = new Event('input', { bubbles: true });
            input.dispatchEvent(ev);
            var ev2 = new KeyboardEvent('keydown', {bubbles:true, key:'Enter'});
            input.dispatchEvent(ev2);
          }
          var btn = document.querySelector('#chat-submit-button') 
                 || document.querySelector('input#su') 
                 || document.querySelector("input[type='submit']")
                 || document.querySelector('button');
          if (btn) { try { btn.click(); return true;} catch(e){} }
          return false;
        })(arguments[0])
        """
        try:
            result = self.driver.execute_script(js, query)
            print(f"  - JS 注入并点击尝试，结果: {result}")
            return bool(result)
        except Exception as e:
            print("  - JS 注入失败:", e)
            return False

    def save_debug(self, name_suffix):
        path = f"{self.debug_prefix}_{name_suffix}.png"
        try:
            self.driver.save_screenshot(path)
            print(f"  - 已保存截图: {path}")
        except Exception as e:
            print("  - 保存截图失败:", e)

    # ---------------- core flow methods ----------------
    def open_homepage(self, url="https://www.baidu.com"):
        self.driver.get(url)
        self.driver.maximize_window()
        # 等待页面准备好
        try:
            self.wait.until(lambda d: d.execute_script("return document.readyState") == "complete")
        except Exception:
            pass
        # 隐藏 webdriver 标识（可选）
        try:
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        except Exception:
            pass
        print("打开页面：", self.driver.current_url)

        # 优先检测新版（chat-textarea），否则检测旧版（kw）
        try:
            # 优先尝试短时间查找新版
            self.search_box = WebDriverWait(self.driver, 2).until(
                EC.presence_of_element_located((By.ID, "chat-textarea"))
            )
            self.search_type = "新版AI"
            print("检测到新版AI输入框 (#chat-textarea)")
            return
        except TimeoutException:
            pass

        try:
            self.search_box = WebDriverWait(self.driver, 2).until(
                EC.presence_of_element_located((By.ID, "kw"))
            )
            self.search_type = "经典版"
            print("检测到经典版输入框 (#kw)")
            return
        except TimeoutException:
            pass

        # 都没检测到
        print("❌ 未检测到 chat-textarea 或 kw")
        self.save_debug("no_search_box")
        raise SystemExit("无法继续：未找到搜索输入框")

    def ensure_search(self, query):
        """尝试多种方式完成搜索（你的 ensure_search 整合版）"""
        print(f"开始尝试搜索：'{query}'（当前搜索类型：{self.search_type}）")
        # 如果是新版且存在 chat-submit-button，优先用它
        if self.search_type == "新版AI":
            try:
                box = self.driver.find_element(By.CSS_SELECTOR, ".chat-input-background_3edHa #chat-submit-button")
                try:
                    box.click()
                    box.clear()
                    box.send_keys(query)
                    print("  - 在 chat-textarea 中输入（常规）")
                except Exception:
                    print("  - chat-textarea 常规输入失败，尝试 JS 注入")
                    js_ok = self.try_js_inject_and_click(query)
                    if js_ok:
                        return True
                # 尝试回车
                try:
                    box.send_keys("\n")
                    print("  - 使用回车触发搜索")
                    return True
                except Exception:
                    pass
            except NoSuchElementException:
                print("  - 未找到 chat-textarea 元素")
        # 尝试传统输入框方案（兼容旧版）
        if self.try_use_visible_input(query):
            # 找到可见按钮并点击（CSS方法）
            try:
                btns = self.driver.find_elements(By.CSS_SELECTOR, "input#su, input[type='submit'], button,#chat-submit-button")
                for b in btns:
                    try:
                        if b.is_displayed() and b.is_enabled():
                            b.click()
                            print("  - 点击找到的按钮完成搜索")
                            return True
                    except Exception:
                        continue
            except Exception:
                pass
            # 如果没有找到按钮，尝试 JS
            js_ok = self.try_js_inject_and_click(query)
            if js_ok:
                return True

        # 最后再尝试 JS 注入（通用）
        js_ok = self.try_js_inject_and_click(query)
        if js_ok:
            return True

        # 最后回退：强制打开旧版首页，再试一次
        print("回退到旧版首页尝试（?simple=1）")
        self.driver.get("https://www.baidu.com/?simple=1")
        try:
            time.sleep(1)
            if self.try_use_visible_input(query):
                try:
                    btn = self.driver.find_element(By.ID, "su")
                    btn.click()
                    print("  - 在旧版页面使用按钮点击成功")
                    return True
                except Exception:
                    pass
        except Exception:
            pass

        # 全部失败
        print("❌ 所有搜索方法均失败")
        self.save_debug("search_failed")
        return False

    def click_result_link(self, target_keyword="Selenium"):
        """尝试多种定位方式点击搜索结果中包含 target_keyword 的链接"""
        print(f"尝试点击搜索结果中包含: '{target_keyword}' 的链接")
        # 等待 search results 区域出现（常见 id/class）
        try:
            # 若有 content_left（旧版），等之；新版可能没有，短等待
            try:
                self.wait.until(EC.presence_of_element_located((By.ID, "content_left")))
            except Exception:
                pass
            # 方法1：部分 link text
            try:
                link = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.PARTIAL_LINK_TEXT, target_keyword))
                )
                print("  - 通过 PARTIAL_LINK_TEXT 定位到链接：", link.text[:80])
                link.click()
                return True
            except Exception:
                pass
            # 方法2：XPath 包含
            try:
                xpath = f"//a[contains(normalize-space(.), '{target_keyword}')]"
                link = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, xpath))
                )
                print("  - 通过 XPath 定位到链接：", link.text[:80])
                link.click()
                return True
            except Exception:
                pass
            # 方法3：使用 font[color='#CC0000']（有时百度把结果高亮）
            try:
                link = self.driver.find_element(By.CSS_SELECTOR, "font[color='#CC0000']")
                parent = link.find_element(By.XPATH, "./ancestor::a[1]")  # 找最近祖先 a
                parent.click()
                print("  - 通过 font 高亮定位并点击链接")
                return True
            except Exception:
                pass
            # 方法4：最后尝试第一个可点击的 <a>
            try:
                all_a = self.driver.find_elements(By.CSS_SELECTOR, "a")
                for a in all_a:
                    try:
                        if a.is_displayed() and target_keyword in a.text:
                            a.click()
                            print("  - 通过遍历 <a> 并匹配文本点击")
                            return True
                    except Exception:
                        continue
            except Exception:
                pass
        except Exception as e:
            print("点击搜索结果时出错:", e)

        print("❌ 未能定位到目标链接，已截图供调试")
        self.save_debug("click_result_failed")
        return False

    def quit(self):
        try:
            self.driver.quit()
        except Exception:
            pass

    # ---------------- top-level run ----------------
    def run(self, query="软件测试工具", target="Selenium", keep_open=False):
        try:
            self.open_homepage()
            ok = self.ensure_search(query)
            if not ok:
                print("搜索未成功，退出。")
                return
            # 等待结果加载一段时间
            time.sleep(2)
            clicked = self.click_result_link(target)
            if not clicked:
                print("未能点击目标链接。")
            else:
                print("目标链接已点击。")
            # 留给用户查看页面
            if keep_open:
                print("keep_open=True，脚本将不自动关闭浏览器。")
                return
            time.sleep(3)
        finally:
            print("退出并清理资源。")
            time.sleep(30)
            self.quit()


# ---------------- 使用示例 ----------------
if __name__ == "__main__":
    s = BaiduSearcher()
    # 参数： query = 搜索词, target = 要点击的结果关键词（可模糊）
    s.run(query="软件测试工具", target="Selenium --开源中国", keep_open=False)



