# XSS Hunt

`XSS Hunt` is a tool for automating the discovery of Cross-Site Scripting (XSS) vulnerabilities. It crawls sitemaps, extracts URL parameters, and injects XSS payloads to identify potential security flaws. The tool combines `requests` for static analysis and `selenium` for JavaScript-heavy pages, allowing comprehensive testing.

## Features
- **Sitemap Crawling:** Finds and extracts URLs from `sitemap.xml` and `robots.txt`.
- **Parameter Extraction:** Identifies input fields from URLs, forms, and JavaScript sources.
- **XSS Testing:** Injects payloads into parameters and observes behavior.
- **Multithreading:** Uses concurrent processing for efficiency.

## Requirements
- `Python 3`
- `requests`
- `beautifulsoup4`
- `selenium`
- `lxml`
- `chromedriver` (matching your Chrome version: https://googlechromelabs.github.io/chrome-for-testing/#stable)

### Installing Dependencies
```bash
pip install -r requirements.txt
```
To install `chromedriver`:
```bash
sudo apt install google-chrome-stable
wget https://chromedriver.storage.googleapis.com/LATEST_RELEASE -O chromedriver_version.txt
wget https://chromedriver.storage.googleapis.com/$(cat chromedriver_version.txt)/chromedriver_linux64.zip
unzip chromedriver_linux64.zip
sudo mv chromedriver /usr/local/bin/
```

## Usage
### 1. **Full Scan** (Crawl sitemap, extract parameters, and test XSS)
```bash
python script.py full <domain_or_sitemap>
```
Example:
```bash
python script.py full https://example.com
```

### 2. **Extract Parameters** (From a list of URLs)
```bash
python script.py params <urls_file> <output_file>
```
Example:
```bash
python script.py params mappedsites.txt parameters.txt
```

### 3. **XSS Testing** (Test extracted parameters with payloads)
```bash
python script.py xss <urls_file> <payloads_file>
```
Example:
```bash
python script.py xss parameters.txt payloads.txt
```

## How It Works
### **1. Sitemap Crawling**
- Searches for `sitemap.xml` or extracts URLs from `robots.txt`.
- Collects all valid URLs and saves them to `mappedsites.txt`.
- Filters out non-relevant URLs and duplicate entries.

### **2. Parameter Extraction**
- Analyzes HTML and JavaScript for URL parameters.
- Detects parameters in forms, links, and inline scripts.
- Saves discovered parameters to `parameters.txt`.

### **3. XSS Testing**
- Loads URLs and injects predefined XSS payloads.
- Uses `selenium` to render pages and detect potential XSS.
- Logs tested URLs and results in `xss_results.txt`.

## Output Files
- `mappedsites.txt` → Extracted URLs from the sitemap.
- `parameters.txt` → Discovered parameters from URLs and forms.
- `xss_results.txt` → URLs tested for XSS vulnerabilities.

## Example Payload File (`payloads.txt`)
```
<script>alert(1)</script>
"><img src=x onerror=alert(1)>
<svg/onload=alert(1)>
```

## Notes
- Uses **ThreadPoolExecutor** for parallel execution.
- Can be stopped anytime with `CTRL+C`.
- Logs errors and successful tests with timestamps.

## Disclaimer
This tool is for **educational and ethical security testing** only. Unauthorized use against systems you do not own is illegal.

## License
MIT License
