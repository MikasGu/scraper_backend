**Travel Offers API**

This repository hosts a Python Flask web application that serves as an API for scraping travel offers from three prominent travel agencies: Makalius, Air Guru, and TezTour. The application utilizes a SQLite database for storing scraped offers, with data accessible through various API endpoints. The scraping process employs BeautifulSoup for HTML parsing and Selenium for dynamic content interaction.

---

**Key Features:**
- Scraping offers from Makalius, Air Guru, and TezTour.
- SQLite database integration to store and manage scraped data.
- API endpoints for initiating scraping, retrieving offers by country codes, and obtaining total offer counts for each country.
- Predefined country codes available in the COUNTRY_CODES dictionary.
- Support for Cross-Origin Resource Sharing (CORS).
- Basic web interface accessible at the root endpoint.

---

**How to Use:**
1. Run the application.
2. Access the API endpoints for scraping and retrieving travel offers.

---

**Endpoints:**

1. **Root Endpoint ("/")**
   - **Method:** GET
   - **Description:** Welcome message and status of the API.
   - **Usage Example:** Accessing the root URL.

2. **Scrape Endpoint ("/scrape")**
   - **Method:** POST
   - **Description:** Initiates the scraping process for travel offers based on the specified country.
   - **Request Format:** JSON with the "country" parameter.
   - **Response:** Provides scraped travel offers sorted by price.
   - **Usage Example:** 
      ```bash
      curl -X POST -H "Content-Type: application/json" -d '{"country": "United States"}' http://localhost:5000/scrape
      ```

3. **Get Offers Endpoint ("/offers/<country_code>")**
   - **Method:** GET
   - **Description:** Retrieves travel offers for a specific country based on the country code.
   - **Response:** List of serialized offers for the specified country.
   - **Usage Example:** 
      ```bash
      curl http://localhost:5000/offers/US
      ```

4. **Total Offers Endpoint ("/total_offers/all")**
   - **Method:** GET
   - **Description:** Retrieves the total number of offers for each country.
   - **Response:** JSON object with country codes and corresponding offer counts.
   - **Usage Example:** 
      ```bash
      curl http://localhost:5000/total_offers/all
      ```

**Dependencies:**
- Flask
- BeautifulSoup
- Selenium
- Flask-SQLAlchemy
- Flask-CORS
- ChromeDriver (webdriver_manager)

---

**Note:**
- Ensure you have the necessary dependencies installed before running the application.
- The SQLite database is initialized using `db.create_all()` when the application is run as the main module.
