from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time

def get_instagram_data(hashtag: str):
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # 브라우저 화면 숨김
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    try:
        url = f"https://www.instagram.com/explore/tags/{hashtag}/"
        driver.get(url)
        time.sleep(5)
        
        count_element = driver.find_element(By.XPATH, "//span[contains(text(),'posts') or contains(text(),'게시물')]")
        count_text = count_element.text.replace(",", "").split()[0]  
        count = int(count_text)
        
        print(f"#{hashtag} 검색 결과 {count}개의 게시물이 있습니다.")
        
        return count
    except Exception as e:
        print(f"Error: {e}")
        return 0
    finally:
        driver.quit()
    
    
    