from selenium import webdriver
import selenium.webdriver.support.ui as ui
from selenium.webdriver.common.keys import Keys
from selenium.webdriver import ActionChains
from urllib.request import urlretrieve
import os
import logging
from logging.handlers import RotatingFileHandler

ffbrowser = webdriver.Chrome()
wait = ui.WebDriverWait(ffbrowser,12)

logger = None

def prepareLog(name = 'log'):
    """"""
    if not os.path.exists('logs'):
        os.mkdir('logs')
    file_handler = RotatingFileHandler('logs/'+ name +'.log',
                                       maxBytes=10240000, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s '
        '[in %(pathname)s:%(lineno)d]'))
    file_handler.setLevel(logging.INFO)
    global logger 
    logger = logging.getLogger('downloade.py')
    logger.addHandler(file_handler)
    consoleHandler = logging.StreamHandler()
    logger.addHandler(consoleHandler)    
    logger.setLevel(logging.INFO)

def prepareResource():
    """"""
    logger.info("prepare resources started.")
    ffbrowser.get("http://www.effortlessenglishpage.com/p/mp3-free-download.html")
    body = ffbrowser.find_element_by_xpath("//*[@id=\"Blog1\"]/div[1]/div[1]/div[2]")
    elems = body.find_elements_by_partial_link_text(".mp3")
    resources = {}
    for elem in elems:
        try:
            url = elem.get_attribute("href")
            name = elem.text
            resources[name] = url
        except Exception as e:
            logger.error("add resource err:{}".format(e))
    logger.info("prepare resources finished, count {0}".format(len(resources)))
    return resources

def download(resources, dirToSave, retryCount = 0, shutdownWhenFinish = False):
    logger.info("start downloading ,retryCount {0}".format(retryCount))
    failures = {}
    i = 1
    if not os.path.isdir(dirToSave):
        os.mkdir(dirToSave)    
    for name,url in resources.items():
        try:
            path = dirToSave+'/'+name
            logger.info("seqence {}, name {}, path {}".format(i, name, path))
            i+=1
            if os.path.isfile(path):
                os.remove(path)
            urlretrieve(url, path)            
        except Exception as e:
            logger.error("download err:{}".format(e))
            failures[name] = url
    if len(failures) > 0:
        logger.error("failures {}".format(str(failures)))
    logger.info("finish downloading ,retryCount {0}".format(retryCount))
    if len(failures) > 0 and retryCount < 4:
        download(failures, dirToSave, retryCount + 1, shutdownWhenFinish)
    else:
        if shutdownWhenFinish:
            os.system("shutdown -h now")

if __name__ == '__main__':
    prepareLog('endown')
    logger.info("start")
    resources = prepareResource()
    download(resources, 'mp3', shutdownWhenFinish=True)
    logger.info("end")