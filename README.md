# XSS Hunt V0.1

`XSS Hunt` is a tool for automating the discovery of Cross-Site Scripting (XSS) vulnerabilities. It crawls sitemaps, extracts URL parameters, and injects XSS payloads to identify potential security flaws. The tool combines `requests` for static analysis and `selenium` for JavaScript-heavy pages, allowing comprehensive testing. <br>
It is basically a combination of other scripts I made when studying XSS (<a href="https://github.com/shootweb/Sitemapper">Sitemapper </a>+ <a href="https://github.com/shootweb/Parameter-grabber">Parameter Grabber </a>+ <a href="https://github.com/shootweb/XSSnium">XSSnium</a>).

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

## Usage
**Full Scan:** Will trigger all functions. Intakes a single URL/domain form where it will look for the sitemap and robots.txt.
<br>
**Extract Parameters:** Needs a URL list, it will trigger parameter grabbing and output the parameters into a list.
<br>
**XSS Testing:** Needs a URL with paremeters list and a Payloads list, it will test the Payloads into the parameters.
<br>
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
I reccomend using XSS Hunter URL in your payloads, but I'm not the XSS police.
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
<br>
Do not use this tool for skidding.

## License
MIT License
