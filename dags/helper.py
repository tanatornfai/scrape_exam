import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import time
import random
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import duckdb
import os

current_dir = os.path.dirname(os.path.abspath(__file__))


def bypass_cloudflare():
    options = Options()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    options.add_argument(
        "--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    options.add_argument("--headless")
    options.binary_location = "/usr/bin/chromium"

    service = webdriver.ChromeService(executable_path="/usr/bin/chromedriver")
    driver = webdriver.Chrome(service=service, options=options)
    driver.execute_script(
        "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    )
    return driver


def get_samsung_product_id(name):
    pattern_list = [r"[A-Z]{2}\d{2}[A-Z0-9]+", r"\d{2}[A-Z]{1,3}\d{0,4}"]
    for pattern in pattern_list:
        match = re.search(pattern, name)
        if match:
            return match.group()
    return None


def get_size(text):
    match = re.search(r"""(\d+)\s*[inch”]""", text, re.IGNORECASE)
    return match.group(1) if match else "No info"


def check_if_keyword_in_name(keyword, name):
    keywords = keyword.split(" ")
    have_all_keyword = None
    for keyword in keywords:
        if keyword.lower().replace("[-_ ]", "") in name.lower().replace("[-_ ]", ""):
            if have_all_keyword == None:
                have_all_keyword = True
            else:
                have_all_keyword = have_all_keyword and True
        else:
            have_all_keyword = False
    if have_all_keyword == None:
        return False
    else:
        return have_all_keyword


class BaseScraping:
    def __init__(self, page_limit):
        self.page_limit = page_limit

    def get_detail_from_page(self, page):
        pass

    def scrape_data(self):
        product_list = []
        for i in range(1, self.page_limit + 1):
            product_list.extend(self.get_detail_from_page(i))
        return product_list

    def create_dataframe(self, product_list):
        df = pd.DataFrame(
            product_list, columns=["website", "keyword", "name", "price"]
        ).drop_duplicates()
        df["product_id"] = df["name"].apply(lambda x: get_samsung_product_id(x))
        df["monitor_size"] = df["name"].apply(lambda x: get_size(x))
        return df

    def write_result_to_duckdb(self, website, df):
        conn = duckdb.connect(os.path.join(current_dir, "products.db"))
        conn.execute(f"""DELETE FROM products WHERE website = '{website}' """)
        conn.execute(f"INSERT INTO products SELECT * FROM df")

    def execute(self):
        pass


class HomeProProductScraping(BaseScraping):
    HOMEPRO_URL = "https://www.homepro.co.th/search?searchtype=&q={keyword}&page={page}"

    def __init__(self, keyword, page_limit=3):
        super().__init__(page_limit)
        self.keyword = keyword
        self.page_limit = page_limit

    def get_detail_from_page(self, page):
        product_list = []

        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

        response = requests.get(
            url=self.HOMEPRO_URL.format(
                keyword=self.keyword.replace(" ", "+"), page=page
            ),
            headers=headers,
        )
        soup = BeautifulSoup(response.content, "html.parser")
        products = soup.find_all("div", class_="product-plp-card")
        for i in products:
            _id = i.get("id").replace("product-", "")
            name = i.find("input", id=f"gtmNameEN-{_id}").get("value")
            price = i.find("input", id=f"gtmPrice-{_id}").get("value")
            if check_if_keyword_in_name(self.keyword, name):
                product_list.append(["Homepro", self.keyword, name, price])
        return product_list

    def execute(self):
        product_list = self.scrape_data()
        homepro_df = self.create_dataframe(product_list)
        self.write_result_to_duckdb("Homepro", homepro_df)


class PowerBuyProductScraping(BaseScraping):
    POWERBUY_URL = "https://www.powerbuy.co.th/en/search/{keyword}?page={page}"

    def __init__(self, keyword, page_limit=3):
        super().__init__(page_limit)
        self.keyword = keyword
        self.page_limit = page_limit

    def get_detail_from_page(self, page):
        product_list = []
        driver = bypass_cloudflare()
        driver.get(
            self.POWERBUY_URL.format(keyword=self.keyword.replace(" ", "+"), page=page)
        )
        time.sleep(random.uniform(3, 5))

        soup = BeautifulSoup(driver.page_source, "html.parser")
        products = soup.find_all(
            "div",
            class_="MuiGrid-root MuiGrid-item MuiGrid-grid-xs-6 MuiGrid-grid-sm-4 MuiGrid-grid-md-3 MuiGrid-grid-lg-3 MuiGrid-grid-xl-3 css-1nozjar",
        )
        for product in products:
            name = product.find("h2").get_text(strip=True)
            price = (
                product.find(
                    "div",
                    class_="text-redPrice font-bold text-sm leading-3 w-full flex",
                )
                .get_text(strip=True)
                .replace("฿", "")
                .replace(",", "")
            )

            if check_if_keyword_in_name(self.keyword, name):
                product_list.append(["Powerbuy", self.keyword, name, float(price)])
        driver.quit()
        return product_list

    def execute(self):
        product_list = self.scrape_data()
        powerbuy_df = self.create_dataframe(product_list)
        self.write_result_to_duckdb("Powerbuy", powerbuy_df)
