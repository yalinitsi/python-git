# This file is for running a Scrapy spider directly for development/testing purposes.
# In production, use the Scrapy CLI: scrapy crawl lottoweb

import scrapy
from scrapy.crawler import CrawlerProcess
import io
import urllib.request
import PyPDF2
import re
from datetime import datetime

timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S") 

fname = f"results_{timestamp}.html" 

class LottoSpider(scrapy.Spider):
    name = "lottoweb"
    start_urls = [
        'https://www.statelottery.kerala.gov.in/English/index.php/lottery-result-view/'
    ]


    def parse(self, response):
        hrefs = response.xpath('//tr[1]/td[3]/a/@href').extract()
        if not hrefs:
            self.logger.warning("No PDF links found on the page.")
            return
        pdf_url = response.urljoin(hrefs[0])
        self.logger.info(f"Downloading PDF: {pdf_url}")
        yield scrapy.Request(pdf_url, callback=self.parse_pdf)

    def parse_pdf(self, response):
        reader = PyPDF2.PdfReader(io.BytesIO(response.body))
        page1 = ''
        for page_num in range(len(reader.pages)):
            page = reader.pages[page_num].extract_text()
            page1 += page
        filtered = self.filter_text(page1)
        html_content = self.convert_text_to_html(filtered)
        with open(fname, 'w', encoding='utf-8') as f:
            f.write(html_content)
        self.logger.info("Saved lottopage1.html")

    def filter_text(self, text):
        lines = text.split('\n')
        exclude_pattern = [r"kerala", r".in", r".com", r"Department", r"page"]
        filtered_lines = []
        for line in lines:
            if any(re.search(pattern, line, re.IGNORECASE) for pattern in exclude_pattern):
                continue
            filtered_lines.append(line)
        return '\n'.join(filtered_lines)

    def convert_text_to_html(self, filtered_text):
        html = "<html><head><title>PDF to HTML</title></head><body>"
        html += "<h1>Converted PDF Text</h1>"
        html += "<div>"
        html += f"<p>{filtered_text.replace('\n', '<br>')}</p>"
        html += "</div>"
        html += "</body></html>"
        return html

# For direct script execution (not needed if using 'scrapy crawl lottoweb')
if __name__ == "__main__":
    process = CrawlerProcess()
    process.crawl(LottoSpider)
    process.start()
