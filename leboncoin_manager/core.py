#!/usr/bin/python3

"""
    Provides the LeboncoinManager class, used to manage your ads on leboncoin.fr.

    Usage:

    >>> from core import LeboncoinManager
    >>> manager = LeboncoinManager("username", "password")
    >>> manager.update("My ad title")
"""

import sys
import re
import os.path
import tempfile
import urllib.request
from urllib.parse import urlparse
from urllib.error import HTTPError, URLError

try:
    import selenium
except ImportError as e:
    sys.exit("Error during selenium import, please make sure that selenium is correctly installed: `pip install selenium`")

from selenium import webdriver
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys


class LeboncoinManager:
    def __init__(self, username=None, password=None):
        self.driver = webdriver.Firefox()
        self.wait = WebDriverWait(self.driver, 10)

        if username is not None and password is not None:
            self.login(username, password)

    def login(self, username, password, login_url="https://compteperso.leboncoin.fr/account/index.html?ca=12_s"):
        """login(username, password[, login_url="https://compteperso.leboncoin.fr/account/index.html?ca=12_s]")
        Connect to your Leboncoin account using the given credentials. Owing an account
        is mandatory to perform any action."""

        self.driver.get(login_url)
        username_field = self.driver.find_element_by_name("st_username")
        password_field = self.driver.find_element_by_name("st_passwd")

        username_field.send_keys(username)
        password_field.send_keys(password)

        submit_button = self.driver.find_element_by_id("connect_button")
        submit_button.click()

    def delete(self, ad_title, recover_ad=False, recover_images=False):
        """
        delete(ad_title[, recover_ad=False, recover_images=False])
        Delete the ad based on its title.
        recover_ad: if True, recovers information about the ad before deleting it, and
                    returns it as a dict
        recover_images: if True, the ad images of the ad are saved in a temporary
        directory, and the corresponding paths are saved in the returned dict.
        """
        ads = self.driver.find_elements_by_xpath("//form[@id='dashboard']/div[@class='list']/div[@class='element' or @class='element variant']")

        for ad in ads:
            a_tag = ad.find_element_by_tag_name("a")
            if a_tag.text in ad_title:
                break

        else:
            raise ValueError("Aucune annonce '{}' n'a été trouvée.".format(ad_title))

        try:
            price_string = getattr(ad.find_element_by_class_name("price"), "text")
            price_match = re.search(r"([0-9]+) €", price_string)

            if price_match is not None:
                price = price_match.group(1)

        except selenium.common.exceptions.NoSuchElementException as e:
            price = None
            print("Pas de prix indiqué pour l'annonce.")

        category_string = getattr(ad.find_element_by_class_name("category"), "text")
        category_match = re.search(r"catégorie : ([^\t\n\r\f\v]+)", category_string)

        if category_match is not None:
            category = category_match.group(1)

        self.driver.get(a_tag.get_attribute("href"))
        postal_code = getattr(self.driver.find_element_by_xpath("//td[@itemprop='postalCode']"), "text")
        description = getattr(self.driver.find_element_by_xpath("//div[@itemprop='description']"), "text")

        if recover_images:
            image_list = self.driver.find_elements_by_xpath("//meta[@itemprop='image']")

            image_url_list = [image.get_attribute("content") for image in image_list]
            image_path_list = []

            tempdir = tempfile.mkdtemp()
            for image_url in image_url_list:
                try:
                    file_name = os.path.basename(urlparse(image_url).path)

                    request = urllib.request.urlopen(image_url)
                    image_path = os.path.join(tempdir, file_name)

                    with open(image_path, 'wb') as f:
                        print("Saving image in {}".format(image_path))
                        f.write(request.read())

                    image_path_list.append(image_path)

                except HTTPError as e:
                        print("HTTP Error: ", e.code, url)
                except URLError as e:
                        print("URL Error: ", e.reason, url)

        buttons = self.driver.find_elements_by_xpath("//div[@class='lbc_links']/a[@onclick]")

        for delete_button in buttons:
            if delete_button.text == "Supprimer":
                break

        else:
            raise ValueError("Pas de boutton supprimer.")

        delete_button.click()

        continue_xpath = "//input[@name='continue']"
        continue_button = self.wait.until(EC.element_to_be_clickable((By.XPATH, continue_xpath)))

        continue_button.click()

        select_menu = self.driver.find_element_by_name("delete_reason")
        selector = Select(select_menu)
        selector.select_by_index(2)

        try:
            continue_button = self.driver.find_element_by_xpath("//input[@name='st_ads_continue']")
            continue_button.click()
        except selenium.common.exceptions.NoSuchElementException as e:
            print("L'annonce ci-dessous ne peut pas être supprimée, soit parce qu'elle a déjà été supprimée soit parce qu'elle est en cours de suppression ou de validation.")

        if recover_ad:
            ad_content = {"ad_title": ad_title,
                          "description": description,
                          "zipcode": postal_code,
                          "price": price,
                          "category": category}

            if recover_images:
                ad_content["image_path_list"] = image_path_list

            print(ad_content)

            return ad_content


    def publish(self, ad_title, description, category, zipcode, price=None, publish_url="http://www2.leboncoin.fr/ai?ca=22_s", image_path_list=None):
        """publish(ad_title, description, category, zipcode[, price=None, publish_url="http://www2.leboncoin.fr/ai?ca=22_s", image_path_list=None])
        Publish an add on Leboncoin.
        """
        self.driver.get(publish_url)
        select_category_menu = self.driver.find_element_by_name("category")
        selector = Select(select_category_menu)
        selector.select_by_visible_text(category)

        zipcode_field = self.driver.find_element_by_id("zipcode")
        zipcode_field.clear()
        zipcode_field.send_keys(zipcode)

        subject_field = self.driver.find_element_by_id("subject")
        subject_field.send_keys(ad_title)

        body = self.driver.find_element_by_id("body")
        body.send_keys(description)

        if price is not None:
            price_field = self.driver.find_element_by_id("price")
            price_field.send_keys(price)

        if image_path_list is not None:
            for image_nb, image_path in enumerate(image_path_list):
                if image_nb == 3:
                    print("Seulement 3 images par annonce.")
                    break

                image_field = self.driver.find_element_by_id("image{}".format(image_nb))

                image_field.send_keys(image_path)
                self.wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@id='image_box_{}']//a[@class='remove_image']".format(image_nb))))

        validate_button = self.driver.find_element_by_name("validate")
        validate_button.click()

        cgu_accept = self.driver.find_element_by_name("accept_rule")
        cgu_accept.click()

        create_button = self.driver.find_element_by_name("create")
        create_button.click()

    def update(self, ad_title, recover_images=True):
        """update(ad_title[, recover_images=True])
        Update an already existing ad on Leboncoin based on its title.
        recover_images: if True, the images of the original ad are kept
        """
        ad_parameters = self.delete(ad_title, recover_images=recover_images, recover_ad=True)
        self.publish(**ad_parameters)

    def quit(self):
        self.driver.quit()
