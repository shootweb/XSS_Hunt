import sys
import os
import time
import random
import logging
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs, urljoin
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from queue import Queue

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class XSSTester:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
        })
        self.driver = None

    # Sitemap Crawler Functions
    def get_domain(self, url):
        parsed_url = urlparse(url)
        return f"{parsed_url.scheme}://{parsed_url.netloc}"

    def get_urls_from_source(self, url):
        try:
            response = self.session.get(url)
            response.raise_for_status()
            content = response.text
            domain = self.get_domain(url)

            urls = re.findall(r'<loc>(.*?)<\/loc>', content)
            if not urls:
                urls = re.findall(r'href=["\'](.*?)["\']', content, re.IGNORECASE)
                urls = [url if url.startswith("http") else f"{domain}/{url.lstrip('/')}" for url in urls]

            return list(set([u.strip() for u in urls if "javascript:void(0)" not in u and not u.endswith("#") and "?" not in u]))
        except requests.RequestException as e:
            logging.error(f"Error fetching URLs from {url}: {e}")
            return []

    def extract_sitemaps_from_index(self, sitemap_index_url):
        try:
            response = self.session.get(sitemap_index_url)
            return re.findall(r'<loc>\s*(https?://.*?sitemap[^<]*\.xml)\s*</loc>', response.text, re.IGNORECASE)
        except requests.RequestException as e:
            logging.error(f"Error fetching sitemap index {sitemap_index_url}: {e}")
            return []

    def search_for_sitemap(self, domain):
        base_url = self.get_domain(domain)
        initial_sitemap_url = f"{base_url}/sitemap.xml"
        try:
            response = self.session.get(initial_sitemap_url)
            response.raise_for_status()
            return initial_sitemap_url
        except requests.RequestException:
            robots_url = f"{base_url}/robots.txt"
            try:
                response = self.session.get(robots_url)
                sitemap_urls = re.findall(r'Sitemap:\s*(https?://\S+)', response.text, re.IGNORECASE)
                return sitemap_urls[0] if sitemap_urls else None
            except requests.RequestException:
                return None

    def crawl_sitemap(self, domain_or_sitemap, output_file="mappedsites.txt"):
        if os.path.exists(output_file):
            os.remove(output_file)
        
        starting_sitemap = domain_or_sitemap if domain_or_sitemap.endswith(".xml") else self.search_for_sitemap(domain_or_sitemap)
        if not starting_sitemap:
            logging.error("No sitemap found.")
            return False

        all_urls = set()
        processed_sitemaps = set()
        sitemap_queue = Queue()
        sitemap_queue.put(starting_sitemap)

        while not sitemap_queue.empty():
            current_sitemap = sitemap_queue.get()
            if current_sitemap in processed_sitemaps:
                continue

            processed_sitemaps.add(current_sitemap)
            urls = self.get_urls_from_source(current_sitemap)
            all_urls.update(urls)

            nested_sitemaps = self.extract_sitemaps_from_index(current_sitemap)
            for nested_sitemap in nested_sitemaps:
                if nested_sitemap not in processed_sitemaps:
                    sitemap_queue.put(nested_sitemap)

            if len(all_urls) > 1000:
                self.write_to_file(all_urls, output_file)
                all_urls.clear()

        if all_urls:
            self.write_to_file(all_urls, output_file)
        logging.info(f"URLs written to {output_file}")
        return True

    # Parameter Extraction Functions
    def fetch_page_content(self, url):
        try:
            response = self.session.get(url)
            return response.text if response.status_code == 200 else None
        except requests.RequestException as e:
            logging.error(f"Error fetching {url}: {e}")
            return None

    def extract_parameters(self, html_content, base_url):
        parameters = set()
        soup = BeautifulSoup(html_content, "html.parser")

        for tag in soup.find_all(["input", "textarea", "select", "form"]):
            if param_name := tag.get("name"):
                parameters.add(param_name)

        for link in soup.find_all("a", href=True):
            parsed_url = urlparse(link["href"])
            query_params = parse_qs(parsed_url.query)
            parameters.update(query_params.keys())

        for script in soup.find_all("script"):
            js_content = self.fetch_page_content(urljoin(base_url, script.get("src"))) if script.get("src") else script.text
            if js_content:
                parameters.update(re.findall(r'[?&]([a-zA-Z0-9_]+)=', js_content))
                parameters.update(re.findall(r'([a-zA-Z0-9_]+)\s*\(', js_content))

        return {p for p in parameters if not re.match(r'.*\[.*\]', p)}

    def process_url_parameters(self, target_url):
        html_content = self.fetch_page_content(target_url)
        return {} if not html_content else {param: f"{target_url}?{param}=" for param in self.extract_parameters(html_content, target_url)}

    def extract_parameters_from_urls(self, urls_file, output_file="parameters.txt"):
        urls = self.read_file_lines(urls_file)
        all_parameters = {}
        with ThreadPoolExecutor(max_workers=10) as executor:
            results = list(executor.map(self.process_url_parameters, urls))
        for result in results:
            all_parameters.update(result)

        domain_parameter_map = {}
        for param, url in all_parameters.items():
            domain = urlparse(url).netloc
            domain_parameter_map.setdefault(domain, {}).setdefault(param, url)

        unique_parameters = {param: url for domain_params in domain_parameter_map.values() for param, url in domain_params.items()}
        self.write_to_file([url for url in unique_parameters.values()], output_file)
        logging.info(f"Parameters written to {output_file}")

    # XSS Testing Functions
    def setup_driver(self):
        chrome_options = Options()
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        self.driver = webdriver.Chrome(options=chrome_options)

    def fetch_page_content_selenium(self, url):
        try:
            self.driver.get(url)
            WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, 'body')))
            return self.driver.page_source
        except Exception as e:
            logging.error(f"Error fetching {url}: {e}")
            return None

    def process_xss_combination(self, target_url, modifier, payload, processed):
        combination = f"{target_url}{modifier}{payload}"
        if combination in processed:
            return None
        try:
            self.fetch_page_content_selenium(combination)
            logging.info(f"Tested XSS: {combination}")
            time.sleep(random.uniform(0.15, 0.17))
            return combination
        except Exception as e:
            logging.error(f"Error testing {combination}: {e}")
            return None

    def test_xss(self, urls_file, payloads_file, save_file="xss_results.txt"):
        if not self.driver:
            self.setup_driver()
        
        urls = self.read_file_lines(urls_file)
        payloads = self.read_file_lines(payloads_file)
        processed = set(self.read_file_lines(save_file)) if os.path.exists(save_file) else set()

        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = []
            batch_save = []

            for url in urls:
                for modifier in ['', '">']:
                    for payload in payloads:
                        futures.append(executor.submit(self.process_xss_combination, url, modifier, payload, processed))

            for future in as_completed(futures):
                if result := future.result():
                    batch_save.append(result)
                    processed.add(result)

                if len(batch_save) >= 50:
                    self.write_to_file(batch_save, save_file, append=True)
                    batch_save.clear()

            if batch_save:
                self.write_to_file(batch_save, save_file, append=True)
        logging.info(f"XSS test results saved to {save_file}")

    # Utility Functions
    def read_file_lines(self, file_path):
        try:
            with open(file_path, "r", encoding='utf-8') as file:
                return [line.strip() for line in file.read().splitlines()]
        except Exception as e:
            logging.error(f"Error reading {file_path}: {e}")
            return []

    def write_to_file(self, items, filename, append=False):
        mode = 'a' if append else 'w'
        try:
            with open(filename, mode, encoding='utf-8') as file:
                file.writelines(f"{item}\n" for item in items)
        except Exception as e:
            logging.error(f"Error writing to {filename}: {e}")

    def cleanup(self):
        if self.driver:
            self.driver.quit()
            logging.info("WebDriver closed.")

def main():
    if len(sys.argv) < 2:
        print("Usage: python script.py <mode> [args]")
        print("Modes: full <domain_or_sitemap> | params <urls_file> <output_file> | xss <urls_file> <payloads_file>")
        sys.exit(1)

    tester = XSSTester()
    mode = sys.argv[1].lower()

    try:
        if mode == "full" and len(sys.argv) == 3:
            domain_or_sitemap = sys.argv[2]
            if tester.crawl_sitemap(domain_or_sitemap, "mappedsites.txt"):
                tester.extract_parameters_from_urls("mappedsites.txt", "parameters.txt")
                tester.test_xss("parameters.txt", "payloads.txt")
        elif mode == "params" and len(sys.argv) == 4:
            tester.extract_parameters_from_urls(sys.argv[2], sys.argv[3])
        elif mode == "xss" and len(sys.argv) == 4:
            tester.test_xss(sys.argv[2], sys.argv[3])
        else:
            print("Invalid mode or arguments.")
            sys.exit(1)
    except KeyboardInterrupt:
        logging.info("Interrupted by user.")
    finally:
        tester.cleanup()

if __name__ == "__main__":
    main()
