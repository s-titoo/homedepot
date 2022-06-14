# /////////////////////////////////////////////////////////////////////////////////////////////////////////

# INSTRUCTION

# Sub department
# Adding a new sub department for search is currently not supported

# Brand
# To add a new brand for search visit links from "sub_deps", find brand name and add it to "brands"
# Do not worry about letter case, unicode characters (like ®), accented letters - write everything in plain English
# I.e., both "Café" and "Cafe" and "cafe" is suitable

# /////////////////////////////////////////////////////////////////////////////////////////////////////////

# CONFIGURATION

# Path to chromedriver.exe for Selenium
# Download here: https://chromedriver.chromium.org/downloads
chromedriver = r"path\to\driver\chromedriver.exe"

# Sub departments to parse
sub_deps = {"Dishwasher": r"https://www.homedepot.com/b/Appliances-Dishwashers/N-5yc1vZc3po",
            "Refrigerator": r"https://www.homedepot.com/b/Appliances-Refrigerators/N-5yc1vZc3pi",
            "Mattress": r"https://www.homedepot.com/b/Furniture-Bedroom-Furniture-Mattresses/N-5yc1vZc7oe"}

# Brands to parse
brands = {"Dishwasher": ["LG", "Samsung"],
          "Refrigerator": ["Whirlpool", "GE Appliances"],
          "Mattress": ["Sealy"]}

# /////////////////////////////////////////////////////////////////////////////////////////////////////////
