#coding:utf-8
 
from selenium import webdriver
import selenium.webdriver.support.ui as ui
from selenium.webdriver.common.keys import Keys
from selenium.webdriver import ActionChains
import time
 
ffbrowser = webdriver.Chrome()
wait = ui.WebDriverWait(ffbrowser,12)
 
def LoginWeibo(username,password):
    try:
        ffbrowser.get("http://weibo.com/login.php")
        euser=ffbrowser.find_element_by_css_selector("div.input_wrap>input")
        euser.send_keys(Keys.ENTER)
        euser.send_keys(username)
 
        epwd=ffbrowser.find_element_by_css_selector("[name='password']")
        epwd.send_keys(Keys.ENTER)
        epwd.send_keys(password)
 
        # 为防止报：Firefox 中的不安全密码警示这个错误，因此点击下密码框附件的区域
        #eunsafe=ffbrowser.find_element_by_css_selector("[class='info_list auto_login clearfix']")
        #eunsafe.click()
        #点击登录按钮
        esubmit=ffbrowser.find_element_by_xpath("//a[@action-type='btn_submit']")
        esubmit.click()
        time.sleep(6)
        eweibo=ffbrowser.find_element_by_css_selector("li>a[bpfilter='page_frame']")
        eweibo.click()
    except Exception as e:
        print(e)
    finally:
        pass
 
def DeleteWeibo():
    try:
        elists=ffbrowser.find_elements_by_css_selector(".W_ficon.ficon_arrow_down.S_ficon")
        for e in elists[1:]:
            e.click()
            time.sleep(1)
            ees=ffbrowser.find_elements_by_css_selector(".screen_box>.layer_menu_list>ul>li>a")
            print(ees[0].text)
            ees[0].click()
            time.sleep(1)
            eenter=ffbrowser.find_element_by_css_selector(".W_btn_a>span")
            eenter.click()
            time.sleep(1)
            try:
                eclose=ffbrowser.find_element_by_css_selector(".W_ficon.ficon_close.S_ficon")
                eclose.click()
                time.sleep(1)
            except:
                pass
 
    except Exception as e:
        print(e)
        try:
            time.sleep(2)
            okenter = ffbrowser.find_element_by_css_selector(".W_btn_b>span")
            okenter.click()
        except:
            pass
    finally:
        pass
 
 
if __name__ == '__main__':
    print("开始登录微博")
    LoginWeibo("username","password")
    print("登录成功")
    i=1
    while True:
        print("开始第"+str(i)+"轮删除")
        time.sleep(6)
        DeleteWeibo()
        i+=1