import unicodedata
import re

import scrapy
from scrapy.exceptions import CloseSpider
from scrapy_selenium import SeleniumRequest

from ..config import sub_deps, brands, chromedriver


# Define helper functions

def normalize_str(txt):
    """
    Convert a raw string into lower case ASCII (e.g., "Café" into "cafe")
    """

    if txt is None:
        norm_txt = ""
    else:
        norm_txt = unicodedata.normalize('NFD', txt). \
            encode('ascii', 'ignore'). \
            decode("utf-8"). \
            lower()

    norm_txt = re.sub(r"[^0-9a-zA-Z]", "", norm_txt)

    return norm_txt


class HomedepotSpider(scrapy.Spider):
    """
    Spider to parse products from www.homedepot.com website.
    """
    name = "homedepot"

    def __init__(self, sub_dep=None, **kwargs):

        # What sub department to search?
        self.sub_dep = sub_dep  # dishwasher // refrigerator // mattress

        # Normalize brand and sub departments names
        self.brands_norm = {key.lower(): [normalize_str(elm) for elm in value] for (key, value) in brands.items()}
        self.sub_deps_norm = {key.lower(): value for (key, value) in sub_deps.items()}

        # What is the link for sub department?
        self.start_urls = [self.sub_deps_norm[self.sub_dep]]

        # What brands to get info for?
        self.brands_filter = self.brands_norm[self.sub_dep]

        super().__init__(**kwargs)

    def parse(self, response):
        """
        Parse webpage with brand names for a specific sub department to get URLs with a list of products.
        """

        if self.sub_dep in ["dishwasher", "refrigerator"]:

            # Get the left-hand side panel with a list of search filters
            left_side_menu = response.css("div nav p.customNav__heading")

            # Get brands' header from the left-hand side panel
            try:
                brands_header = [elm for elm in left_side_menu if "brand" in elm.css("::text").get().lower()][0]
            except IndexError:
                raise CloseSpider("No Brands submenu found on the webpage")

            # Get a list of brands under brands header
            brands_list = brands_header.css("* + ul > li")

            # Get webpage links for the brands we need
            brands_links_dict = {elm.css("a::text").get():
                                 response.urljoin(elm.css("a::attr(href)").get())
                                 for elm in brands_list
                                 if normalize_str(elm.css("a::text").get()) in self.brands_filter}
            brands_links = list(brands_links_dict.values())

        elif self.sub_dep == "mattress":
            pass

            # Get brands' header from the left-hand side filters panel
            try:
                brands_header = response.xpath("//div[@class='dimension' and contains(., 'Brand')]")
            except Exception:
                raise CloseSpider("No Brands submenu found on the webpage")

            # Get a list of brands under brands header
            brands_list = brands_header.css("a.refinement__link")

            # Get webpage links for the brands we need
            brands_links_dict = {elm.css("::text").get():
                                 response.urljoin(elm.css("::attr(href)").get())
                                 for elm in brands_list
                                 if normalize_str(elm.css("::text").get()) in self.brands_filter}
            brands_links = list(brands_links_dict.values())

        # Log info about brands and links we found
        self.logger.info(f'LOGGER => Brands links extracted ({len(brands_links)}): {brands_links_dict}')

        # Follow the brands links to get a list of goods in stock
        # yield from response.follow_all(brands_links, self.parse_brands)

        for web_link in brands_links:
            web_link = response.urljoin(web_link)
            # Use Selenium & add script (move close to middle of a page) to render second part of search results
            # ("browse-search-pods2")
            yield SeleniumRequest(
                url=web_link,
                callback=self.parse_brands,
                # wait_time=10,
                # wait_until=EC.element_to_be_clickable((By.CSS_SELECTOR, "a.hd-pagination__link[aria-label='Next']")),
                script="const sleep = ms => new Promise(r => setTimeout(r, ms));" +
                       "window.scrollTo(0, document.body.scrollHeight*1/2);" +
                       "await sleep(1000);"
            )

    def parse_brands(self, response):
        """
        Parse webpage with a list of products for a specific brand to get URLs for specific products.
        """

        # Get search results sections
        products_sections = response.xpath("//section[contains(@id, 'browse-search-pod')]")  # and contains(@id, '1')]

        # Get a list of products on the webpage
        products_list_many = [elm.css("div[data-type='product']") for elm in products_sections]
        products_list = sum(products_list_many, [])  # this is to flatten a list of lists into a single list

        # Get info about the brand we parse
        brand_parsed_list = products_list[0].css("span.product-pod__title__brand--bold::text").getall()
        brand_parsed = "".join(brand_parsed_list).strip()

        # Get the links to all the products found
        products_links_dict = {counter: response.urljoin(elm.css("a.product-pod--ie-fix::attr('href')").get())
                               for counter, elm in enumerate(products_list, 1)}
        products_links = list(products_links_dict.values())

        # Log info about products we found
        self.logger.info(f'LOGGER => Products links extracted ({brand_parsed}) ({len(products_links)}): '
                         f'{products_links_dict}')

        # Get next page link
        next_page = response.css("a[aria-label='Next']::attr('href')").get()
        # If search results are all on a single page there will be no "Next" anchor & 'next_page' will return None
        # Otherwise, we need to catch the moment when we reach the last page - in our case it means that 'href' has
        # no 'Nao=<number>' text in it
        if next_page is not None and "nao=" not in next_page.lower():
            next_page = None

        # Follow the product links to get its variations
        for web_link in products_links:
            web_link = response.urljoin(web_link)
            # Had to turn off ignoring of duplicated requests as Scrapy filtered off some uniques as well
            # Need to look into why
            yield scrapy.Request(url=web_link, callback=self.parse_products, dont_filter=True)

        self.logger.info(f'LOGGER => Next page parsed: {next_page}')

        if next_page is not None:
            next_page = response.urljoin(next_page)
            yield SeleniumRequest(
                url=next_page,
                callback=self.parse_brands,
                # wait_time=10,
                # wait_until=EC.element_to_be_clickable((By.CSS_SELECTOR, "a.hd-pagination__link[aria-label='Next']")),
                script="const sleep = ms => new Promise(r => setTimeout(r, ms));" +
                       "window.scrollTo(0, document.body.scrollHeight*1/2);" +
                       "await sleep(3000);"
            )

    def parse_products(self, response):
        """
        Parse webpage with a specific products to get details about it.
        """

        # Get product brand
        product_brand = response.css("span.product-details__brand--link::text").get()

        # Get product title
        product_title = response.css("h1.product-details__title::text").get()

        # Get product model
        try:
            product_model_list = response.css("h2.product-info-bar__detail--7va8o::text").getall()
            product_model_index = product_model_list.index("Model #")
            product_model = " ".join(product_model_list[product_model_index:product_model_index + 2])
        except Exception:
            product_model = "Model #"

        # Get product web link
        product_url = response.url

        # Get product price
        product_price_list = response.css("div.price-format__large.price-format__main-price span::text").getall()
        product_price = float(".".join(product_price_list[1:]))

        # Get original product price
        product_price_original_list = response.css("div.price-detailed__was-price span.u__strike span::text").getall()
        if product_price_original_list:
            product_price_original = float("".join(product_price_original_list[1:4]))
            product_discount = product_price_original - product_price
            product_discount_percentage = round(product_discount / product_price_original * 100, 2)
        else:
            product_price_original = product_price
            product_discount = 0.00
            product_discount_percentage = 0.00

        # Get ratings metadata about the product
        product_metadata = response.xpath("//script[contains(text(), 'APOLLO_STATE')]").get()

        # Get product rating and number of reviews
        rating_match = re.search(r'("AverageOverallRating":.*?)(\d(?:\..\d*)?)(.*?"TotalReviewCount":)(\d*)',
                                 product_metadata)

        if rating_match:
            product_rating_average = rating_match.group(2)
            product_reviews_number = rating_match.group(4)
        else:
            product_rating_average = 0.00
            product_reviews_number = 0

        try:
            product_rating_average = round(float(product_rating_average), 2)
        except Exception:
            product_rating_average = 0.00

        try:
            product_reviews_number = int(product_reviews_number)
        except Exception:
            product_reviews_number = 0

        rating_distribution_match_1 = re.search(r'("RatingValue":1.*?"Count":)(\d*)', product_metadata)
        rating_distribution_match_2 = re.search(r'("RatingValue":2.*?"Count":)(\d*)', product_metadata)
        rating_distribution_match_3 = re.search(r'("RatingValue":3.*?"Count":)(\d*)', product_metadata)
        rating_distribution_match_4 = re.search(r'("RatingValue":4.*?"Count":)(\d*)', product_metadata)
        rating_distribution_match_5 = re.search(r'("RatingValue":5.*?"Count":)(\d*)', product_metadata)

        if rating_distribution_match_1:
            product_rating_1 = rating_distribution_match_1.group(2)
        else:
            product_rating_1 = 0
        if rating_distribution_match_2:
            product_rating_2 = rating_distribution_match_2.group(2)
        else:
            product_rating_2 = 0
        if rating_distribution_match_3:
            product_rating_3 = rating_distribution_match_3.group(2)
        else:
            product_rating_3 = 0
        if rating_distribution_match_4:
            product_rating_4 = rating_distribution_match_4.group(2)
        else:
            product_rating_4 = 0
        if rating_distribution_match_5:
            product_rating_5 = rating_distribution_match_5.group(2)
        else:
            product_rating_5 = 0

        try:
            product_rating_1 = int(product_rating_1)
        except Exception:
            product_rating_1 = 0
        try:
            product_rating_2 = int(product_rating_2)
        except Exception:
            product_rating_2 = 0
        try:
            product_rating_3 = int(product_rating_3)
        except Exception:
            product_rating_3 = 0
        try:
            product_rating_4 = int(product_rating_4)
        except Exception:
            product_rating_4 = 0
        try:
            product_rating_5 = int(product_rating_5)
        except Exception:
            product_rating_5 = 0

        # Collect product metadata into a dictionary
        product_specs = {
            'product_brand': product_brand,
            'product_title': product_title,
            'product_model': product_model,
            'product_url': product_url,
            'product_price': product_price,
            'product_price_original': product_price_original,
            'product_discount': product_discount,
            'product_discount_percentage': product_discount_percentage,
            'product_rating_average': product_rating_average,
            'product_reviews_number': product_reviews_number,
            'product_rating_5': product_rating_5,
            'product_rating_4': product_rating_4,
            'product_rating_3': product_rating_3,
            'product_rating_2': product_rating_2,
            'product_rating_1': product_rating_1,
        }

        # Log metadata into a file
        yield product_specs
