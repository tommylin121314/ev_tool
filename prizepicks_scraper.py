import time 
from tqdm import tqdm
import pandas as pd 
from selenium import webdriver 
from selenium.webdriver import Chrome 
from selenium.webdriver.chrome.service import Service 
from selenium.webdriver.common.by import By 
from webdriver_manager.chrome import ChromeDriverManager


class PrizePicksNBAScraper:

    def startDriver(self):
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.104 Safari/537.36"
        options = webdriver.ChromeOptions() 
        options.page_load_strategy = 'none' 
        options.add_argument('headless')
        options.add_argument(f"user-agent={user_agent}")
        options.add_argument("log-level=3")
        options.add_experimental_option('excludeSwitches', ['enable-logging'])

        chrome_path = ChromeDriverManager().install() 
        chrome_service = Service(chrome_path) 

        self.driver = Chrome(options=options, service=chrome_service)
        self.driver.implicitly_wait(5)
        url = "https://app.prizepicks.com/?league=nba" 
        
        self.driver.get(url) 
        time.sleep(5)
        self.driver.refresh()
        time.sleep(3)
        self.league = self.driver.find_element(By.XPATH, "//div[@class='league selected']" ).find_element(By.CLASS_NAME, "name").text;

    
    def generateData(self):
        print("    Generating PP data")
        stat_navs = self.driver.find_elements(By.CLASS_NAME, "stat")
        stat_dict = {'Points': 'PTS', 'Rebounds': 'REB', 'Assists': 'AST', '3-PT Made': '3PT', 'Blocks': 'BLK', 'Steals': 'STL', "Blks+Stls": "BLK+STL"}
        player_props = []

        try:
            for i in tqdm(range(len(stat_navs))):
                time.sleep(1)
                stat_navs = self.driver.find_elements(By.CLASS_NAME, "stat")
                stat_nav = stat_navs[i]
                stat = stat_nav.text
                if stat in list(stat_dict.keys()):
                    play_type = stat_dict[stat]
                    stat_nav.click()
                    time.sleep(1)
                    projections = self.driver.find_elements(By.CLASS_NAME, "projection")
                    for proj in projections:
                        name = proj.find_element(By.CLASS_NAME, 'name').text
                        line = proj.find_element(By.CLASS_NAME, 'score').text
                        if "\n" in line:
                            line = line.split("\n")[1]
                        player_props.append([name, line, play_type])
        except Exception as e:
            print(e)
            return None
 
        print("    Success")
        return player_props