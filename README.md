# Design

[Scrapy](https://doc.scrapy.org/en/latest/intro/tutorial.html)
was chosen for convenience and speed
(i.e. handling several requests at a time, ignoring duplicated requests,
no browser interaction), which was mentioned as one of the key requirements.

But Scrapy cannot work with dynamically generated website content, so it was used
in conjunction with Selenium through the 
[scrapy-selenium](https://github.com/clemfromspace/scrapy-selenium) middleware.
There are [other ways](https://docs.scrapy.org/en/latest/topics/dynamic-content.html)
to parse JS web content, but they take time to implement, so given time
constraint I went with Selenium.

There are a few things I didn't have time to finish.
Details are at the bottom in ***TODOs*** section.

# Installation

1. Install [Google Chrome](https://www.google.com/intl/en/chrome/) web browser.
2. Check your browser version (`Help => About Google Chrome`).
3. Download [chromedriver](https://chromedriver.chromium.org/downloads)
compatible with your browser. Place it in root `homedepot` directory.
4. Make sure that you fulfill [prerequisites](https://docs.scrapy.org/en/latest/intro/install.html)
for using Scrapy. There are some if you use Windows and install Scrapy not through Anaconda.
5. Create a new python virtual environment and install libraries
from `requirements.txt`.
6. In case smth isn't working double check configuration for
[scrapy-selenium](https://github.com/clemfromspace/scrapy-selenium) (`settings.py`).

# Usage

1. Update CONFIGURATION in `homedepot/config.py`:
   * Provide path to chromedriver.exe
   * Make sure sub department links are relevant
   * Update list of brand names for each sub department
   * Use the same keys in `sub_deps` and `brands` dictionaries (e.g. "Dishwasher")
2. Run Scrapy from the root `webscraper` folder using terminal:
   * `scrapy crawl homedepot -O products.csv -a sub_dep=dishwasher --logile homedepot_log.txt`
   * Run`homedepot` spider for `dishwashers` sub department and save results into
   `products.csv`. Optionally you can also redirect logs to `homedepot_log.txt`.
3. Scrapy saves results to a csv file:
    * **Description**:
      * product_brand
      * product_title
      * product_model
      * product_url
    * **Price**:
      * product_price
      * product_price_original
      * product_discount
      * product_discount_percentage
    * **Rating**:
      * product_rating_average
      * product_reviews
      * product_rating_[1,2,3,4,5]

# TODOs

I haven't implemented few things in my code, mostly due to time constrains and some
initial design decisions.

1. **Different products**. Each product variation (by color, size etc.) has its
own webpage. But these webpages are not present in html (even dynamic part). So,
I need to click product switches to get web links. scrapy-selenium doesn't provide
convenient option to do so, and I didn't have time to write my own middleware.

2. **Stores pick-up**. The same reason - I need to program browser to pick up
store from top-left menu and scrapy-selenium doesn't seem the best option for
that. Not sure if relevant, but while I was changing shops the number of returned
results remained the same - I expected it to change.

3. **Product availability**. This one is on me - closer to end realized that it's JS
generated content, while scraper was pretty much done. But adding it to the output
is straighforward - send request to product pages using Selenium (as opposed to
standard Scrapy request used now) and getting content of ***How to Get It*** section.
Script will slow down because of that, though, so maybe worth exploring other options.

4. **Miscellaneous**. Possibly worth to spend some time to make selectors more robust.
In one place I use `await sleep(3000)`, which ideally must be replaced - I tried a few
`expected_conditions` but that didn't work. Plus tests and proper error handling. But
this is just a test case, so hopefully fast & dirty will do for now.
