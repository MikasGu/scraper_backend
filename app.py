import logging
import requests
import time

from flask import Flask, jsonify, request
from flask_cors import CORS
from bs4 import BeautifulSoup
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from flask_sqlalchemy import SQLAlchemy
from country_codes import COUNTRY_CODES

app = Flask(__name__)
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///offers.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

_logger = logging.getLogger(__name__)


class Offer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    country = db.Column(db.String(50))
    country_code = db.Column(db.String(2))
    name = db.Column(db.String(255))
    price = db.Column(db.String(50))
    description = db.Column(db.Text)
    agency = db.Column(db.String(50))
    url = db.Column(db.String(255))

    def serialize(self):
        return {
            "id": self.id,
            "country": self.country,
            "country_code": COUNTRY_CODES.get(self.country, ""),
            "name": self.name,
            "price": self.price,
            "description": self.description,
            "agency": self.agency,
            "url": self.url
        }


def scrape_makalius(country):
    start_time = time.time()
    results = []
    page_number = 1

    while True:
        url = f"https://www.makalius.lt/puslapis/{page_number}/?s={country}"
        response = requests.get(url)

        if response.url == "https://www.makalius.lt/" or page_number > 10:
            break

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")

            offers = soup.select(".offer.search-offer")
            for offer in offers:
                try:
                    details_url = offer.select_one("a").get("href") if offer.select_one("a") else ""
                    name = offer.select_one(".valign.post-type-post strong").text if offer.select_one(
                        ".valign.post-type-post strong") else ""
                    price = offer.select_one(".price .valign strong").text if offer.select_one(".price") else ""
                    description = offer.select_one(".offer-description p").text.strip().replace("  ", "").replace("\n", " ").strip() if offer.select_one(
                        ".description") else ""
                    sold_out = description.find("IŠPARDUOTA") != -1
                    if not (name and price and description) or sold_out:
                        continue
                    results.append({"name": name, "price": price, "description": description, "agency": "Makalius", "url": details_url})
                except AttributeError as e:
                    print(f"Error: {e}")
                    results.append({"name": "Name not found"})

            page_number += 1
        else:
            print(f"Failed to fetch page {page_number}")
            break
    end_time = time.time()
    elapsed_time = end_time - start_time
    _logger.warning(f"\033[92mScraped Makalius: {len(results)} offers in {elapsed_time:.2f} seconds\033[0m")
    return results

def scrape_air_guru(country):
    start_time = time.time()
    results = []
    page_number = 1

    while True:
        url = f"https://airguru.lt/katalogas/?&page={page_number}"
        response = requests.get(url)
        if page_number > 10:
            break

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")

            offers = soup.select(".product_element")
            filtered_offers = [offer for offer in offers if country.lower() in offer.select_one(".title-wrapper span").text.lower()]

            for offer in filtered_offers:
                try:
                    details_url = offer.select_one("a").get("href") if offer.select_one("a") else ""
                    details_response = requests.get(details_url)
                    if details_response.status_code != 200:
                        continue
                    description = BeautifulSoup(details_response.text, "html.parser").select_one(".content-description").text.strip()
                    name = offer.select_one(".title-wrapper span").text if offer.select_one(".title-wrapper span") else ""
                    price = offer.select_one(".price-wrapper span").text.strip() if offer.select_one(".price-wrapper") else ""
                    if not (name and price):
                        continue
                    results.append({"name": name, "price": price, "description": description, "agency": "AirGuru", "url": details_url})
                except AttributeError as e:
                    print(f"Error: {e}")
                    results.append({"name": "Name not found"})

            page_number += 1
        else:
            print(f"Failed to fetch page {page_number}")
            break

    end_time = time.time()
    elapsed_time = end_time - start_time
    _logger.warning(f"\033[92mScraped Air Guru: {len(results)} offers in {elapsed_time:.2f} seconds\033[0m")
    return results

def scrape_tez_tour(country):
    start_time = time.time()
    results = []
    
    chrome_options = Options()
    chrome_options.add_argument("--headless")

    chromedriver_path = ChromeDriverManager().install()
    driver = webdriver.Chrome(executable_path=chromedriver_path, options=chrome_options)
    
    try:
        url = "https://www.teztour.lt/bestoffers.lt.html?product=tours"
        driver.implicitly_wait(5)
        driver.get(url)
        
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')

        filter_items = [item for item in soup.find_all(class_='tour-box') if country.lower() in item.find(class_='text-upper').text.lower()]
        for item in filter_items:
            item_url = "https://www.teztour.lt" + item.find(class_='search-url').get('href')
            description_container = item.find(class_='description-field')
            first_strong_tag = description_container.find('strong')
            description = first_strong_tag.text.strip() if first_strong_tag else "No description"
            item_name = item.find(class_='text-upper').text
            price = item.find(class_='eur-currency').text
            results.append({"name": item_name, "price": price, "description": description, "agency": "TezTour", "url": item_url})

    finally:
        driver.quit()

    end_time = time.time()
    elapsed_time = end_time - start_time
    _logger.warning(f"\033[92mScraped TezTour: {len(results)} offers in {elapsed_time:.2f} seconds\033[0m")
    return results

def save_to_db(results, country):
    for result in results:
        existing_offer = Offer.query.filter_by(url=result.get("url")).first()

        if not existing_offer:
            offer = Offer(
                name=result.get("name", "N/A"),
                price=result.get("price", "N/A"),
                country=country,
                country_code=COUNTRY_CODES.get(country, ""),
                description=result.get("description", "N/A"),
                agency=result.get("agency"),
                url=result.get("url", "N/A")
            )
            db.session.add(offer)

    db.session.commit()

@app.route("/scrape", methods=["POST"])
def scrape():
    data = request.get_json()

    if "country" in data:
        country = data["country"]
        tez_tour_results = scrape_tez_tour(country)
        makalius_results = scrape_makalius(country)
        air_guru_results = scrape_air_guru(country)
        
        results = makalius_results + air_guru_results + tez_tour_results
        results = sorted(results, key=lambda x: float(''.join(filter(str.isdigit, x.get("price", "0")))))
        if results:
            save_to_db(results, country)
            return jsonify({"status": "success", "results": results, "count": len(results)}), 200
        else:
            return jsonify({"status": "success", "message": "No results"}), 200
    else:
        return jsonify({"status": "error", "message": "Missing country parameter"}), 400
    
@app.route("/offers/<country_code>", methods=["GET"])
def get_offers(country_code):
    offers = Offer.query.filter_by(country_code=country_code).filter(Offer.agency.isnot(None), Offer.url.isnot(None), Offer.agency != '', Offer.url != '').all()
    return jsonify({"status": "success", "results": [offer.serialize() for offer in offers], "count": len(offers)}), 200

@app.route('/total_offers/all', methods=['GET'])
def get_total_offers_number():
    offers = Offer.query.filter(Offer.agency.isnot(None), Offer.url.isnot(None), Offer.agency != '', Offer.url != '').all()
    result = {}
    for offer in offers:
        if offer.country_code in result:
            result[offer.country_code] += 1
        else:
            result[offer.country_code] = 1
    return jsonify({"status": "success", "results": result}), 200

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
