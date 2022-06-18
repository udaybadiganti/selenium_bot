from regex import L
from Logger import TailLogger, recordDbLog, LoggerLib
import logging
from logging.handlers import RotatingFileHandler
import psycopg2
from psycopg2 import connect, extras
from configparser import ConfigParser
import os
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
import time
import sys
sys.tracebacklimit = 0

options = webdriver.ChromeOptions()
options.add_argument('--disable-notifications') 
driver = webdriver.Chrome(ChromeDriverManager().install(), options=options) 
wait = WebDriverWait(driver, 20)
actions = ActionChains(driver)
#Current_Path=os.path.dirname(os.path.abspath(os.getcwd()))
Current_Path=os.path.abspath(os.getcwd())

# loglib = LoggerLib(Current_Path, level="INFO")
# Logger, tail = loglib.set_Logger()

# try:
#     x = (1,2,3)
#     print(1/0)
#     Logger.info('info message')
#     recordDbLog(101, 201, 'sample_bot2', tail.contents())
# except Exception as e:
#     Logger.exception(e)
#     recordDbLog(101, 201, 'sample_bot2', tail.contents())

# Logger.info('info message')
# recordDbLog(101, 201, 'sample_bot2', tail.contents())
#
# Logger.info('second info msg')
# recordDbLog(102, 202, 'sample_bot3', tail.contents())


def start():
    loglib = LoggerLib(Current_Path, level="info")
    # logger = logging.getLogger("digit")
    Logger, tail = loglib.set_Logger()
    # tail = TailLogger()

    # Log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(filename)s - %(funcName)s - %(lineno)d - %(message)s')
    # Logger = logging.getLogger()
    # Logger.setLevel(logging.INFO)
    # File_handler = RotatingFileHandler(filename = 'log.log', mode = 'a', maxBytes=100000000, backupCount=10)
    # File_handler.setFormatter(Log_formatter)
    # File_handler.setLevel(logging.INFO)
    # Logger.addHandler(File_handler)



    # # Console_handler = logging.StreamHandler() 
    # # Console_handler.setLevel(logging.INFO)
    # # Console_handler.setFormatter(Log_formatter)
    # # Logger.addHandler(Console_handler)

    # log_handler = tail.log_handler
    # log_handler.setFormatter(Log_formatter)
    # Logger.addHandler(log_handler)

    # # Logger.info('info message')
    # # print(tail.contents())
    # # print("ok")
    # # recordDbLog(101, 201, 'sample_bot2', tail.contents())

    # # Logger.info('second info msg')
    # # recordDbLog(102, 202, 'sample_bot3', tail.contents())

    

    def launchBrowser(url):
        try:
            driver.get(url)
            Logger.info('rul get loaded')
            recordDbLog(102, 202, 'sample_bot3', tail.contents())
            driver.maximize_window()
        except Exception as e:
            Logger.exception(e)
            recordDbLog(102, 202, 'sample_bot3', tail.contents())

    def scrollWebPage():
        recent_height = driver.execute_script("return document.body.scrollHeight")
        
        while True:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            updated_height = driver.execute_script("return document.body.scrollHeight")
            
            if recent_height == updated_height:
                break
            recent_height = updated_height
        
    def main_process():
        try:
            mnu = driver.find_element_by_xpath("//span[@class='used-cars-india0000']")
            actions.move_to_element(mnu).perform()
            Logger.info('mouse over on used cars menu')
            recordDbLog(102, 202, 'sample_bot3', tail.contents())
            driver.find_element_by_xpath("//ul//a[@class='used-cars-india']").click()
            Logger.info('clicked on mouse over')
            recordDbLog(102, 202, 'sample_bot3', tail.contents())
            #wait.until(EC.visibility_of_element_located((By.XPATH, "//span[@class='icon-cd-search location']/parent::div/input")))
            wait.until(EC.element_to_be_clickable((By.XPATH, "//span[@class='icon-cd-search location']/parent::div/input")))
            #driver.find_element_by_xpath("//span[@class='icon-cd-search location']/parent::div/input").click()

            wait.until(EC.element_to_be_clickable((By.XPATH, "//section[@data-track-component='Popular Cities']//li/a")))
            cities = driver.find_elements_by_xpath("//section[@data-track-component='Popular Cities']//li/a")
            Logger.info('all cities fetched ')
            recordDbLog(102, 202, 'sample_bot3', tail.contents())
            city_links = {city.get_attribute("title").split()[-1] :city.get_attribute("href") for city in cities}
            #print(city_links)
            Logger.info('all cars links fetched')
            recordDbLog(102, 202, 'sample_bot3', tail.contents())
            data = {}
            details = []
            for key in city_links:
                driver.get(city_links[key])
                Logger.info(f'url loaded for {key}')
                recordDbLog(102, 202, 'sample_bot3', tail.contents())
                #scrollWebPage()
                #driver.execute_script('return document.readyState') == 'complete'
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                Logger.info(f'mouse scrolled')
                recordDbLog(102, 202, 'sample_bot3', tail.contents())
                cars = driver.find_elements_by_xpath("//div[@class='holder hover']")
                print("processing {}.....".format(key))
                #print(len(cars))
                for car in cars:
                    Logger.info(f'taking each car details')
                    recordDbLog(102, 202, 'sample_bot3', tail.contents())
                    car_details = car.find_element_by_tag_name('a')
                    car_title = car_details.get_attribute("title")
                    car_link = car_details.get_attribute("href")
                    price = car.find_element_by_xpath(".//div[@class=' price']//span[@class='amnt ']").text
                    features = car.find_elements_by_xpath(".//div[@class='truncate dotlist-2']/div")
                    NumOfKms = features[0].text
                    FuelType = features[1].text
                    Type = features[2].text
                    Logger.info(f'all details fetched')
                    recordDbLog(102, 202, 'sample_bot3', tail.contents())
                    details.append({'city': key, 'car_title': car_title, 'car_link': car_link, 'price': price, 'NumOfKms': NumOfKms, 'FuelType': FuelType, 'Type': Type})
                    Logger.info(f'details loaded into dictonary and append into list')
                    recordDbLog(102, 202, 'sample_bot3', tail.contents())
                #data[key] = details
                #break
        except Exception as e:
            Logger.exception(e)
            recordDbLog(102, 202, 'sample_bot3', tail.contents())
        return details
    #https://www.cardekho.com/
    launchBrowser(url = "https://www.cardekho.com/")
    data = main_process()
    time.sleep(5)
    driver.close()
    Logger.info(f'driver closed successfully ')
    recordDbLog(102, 202, 'sample_bot3', tail.contents())

start()