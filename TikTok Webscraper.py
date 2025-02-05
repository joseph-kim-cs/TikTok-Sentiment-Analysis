# Joseph Kim -- TikTok Webscraper
# This python script scrapes title and engagement data from the TikTok 'Trending' ('For You') page

from selenium import webdriver
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import time
import pandas as pd
import os


# data stores TikTok title and engagement data in dictionaries
data = []
all_articles = set() # use a set to ensure no duplicate titles are stored


# Set up drivers for Selenium to scroll the TikTok page
def set_up_driver(): 
    service = webdriver.ChromeService()
    options = webdriver.ChromeOptions()

    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    # user-agent argument to behave like an actual user to disguise the web-scraping request coming from a real browser

    options.add_argument("--headless") 
    # add --headless to run without a browser open
    
    driver = webdriver.Chrome(service=service, options=options)
    return driver


def tiktok_scraper():
    driver = set_up_driver()

    url = "https://www.tiktok.com/foryou"
    driver.get(url)
    time.sleep(5)  

    # Locate the scroll container
    try:
        scroll_container = driver.find_element(By.CLASS_NAME, "css-3xtvlt-DivColumnListContainer")
        print("Successfully located scroll container.")
    except Exception as e:
        print(f"Error locating the scroll container: {e}")
        driver.quit()
        return

    # Scroll and scrape 30 iterations
    for i in range(30): 
        try:
            # Scroll within the container
            driver.execute_script(
                "arguments[0].scrollTop = arguments[0].scrollHeight", scroll_container
            )
            print(f"Scroll iteration {i + 1} completed.")
            time.sleep(2) 

            # Parse the page source to find articles with 'data-scroll-index'
            soup = BeautifulSoup(driver.page_source, "html.parser")
            articles = soup.find_all("article", attrs={"data-scroll-index": True})

            # Extract data from each article
            for article in articles:
                try:
                    index = article['data-scroll-index']
                    if index not in all_articles:
                        all_articles.add(index) 

                        # Extract title
                        title_element = article.find('span', class_="css-j2a19r-SpanText")
                        title = title_element.get_text().strip() if title_element else ''

                        if title: 
                            likes = article.find('strong', {'data-e2e' : 'like-count'}).get_text()
                            comments = article.find('strong', {'data-e2e' : 'comment-count'}).get_text()
                            shares = article.find('strong', {'data-e2e' : 'share-count'}).get_text()
                            favorites = article.find('strong', {'data-e2e' : 'undefined-count'}).get_text()

                            print(f"Article {index}: Title - {title}")
                            data.append({
                                "Title": title,
                                "Likes": likes,
                                "Comments": comments,
                                "Shares": shares,
                                "Favorites": favorites
                            })

                except Exception as e:
                    print(f"Error extracting data from article {index}: {e}")

        except Exception as e:
            print(f"Error during scroll iteration {i + 1}: {e}")

    # Close the browser
    driver.quit()


def update_dataframe():
    global data
    csv_file = "tiktok_data.csv"

    # If 'tiktok_data.csv' does not exist, create the new file; else, update it
    if os.path.exists(csv_file):
        df_existing = pd.read_csv(csv_file)
    else:
        df_existing = pd.DataFrame()

    df_temp = pd.DataFrame(data)

    # Append new data to the existing DataFrame
    df_combined = pd.concat([df_existing, df_temp], ignore_index=True)
    df_combined.drop_duplicates(subset="Title", keep="last", inplace=True)

    # Save the updated DataFrame to the CSV file
    df_combined.to_csv(csv_file, index=False)


if __name__ == '__main__':
    # Run the scraper 3 times with a 20-second delay between each run
    # Note: the first call of tiktok_scraper() finds around 40 unique videos, while many duplicates are found in subsequent calls.
    for run in range(2):
        tiktok_scraper()
        time.sleep(20) 

    # create a dataframe 
    df = pd.DataFrame(data)

    # Save the data to a CSV file after all runs
    update_dataframe()