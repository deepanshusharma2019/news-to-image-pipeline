import feedparser
import yaml
from summary_generator import SummaryGenerator
from news_image_composer import NewsImageComposer

BBC_RSS_URL = "http://feeds.bbci.co.uk/news/rss.xml"

def fetch_bbc_headlines():
    feed = feedparser.parse(BBC_RSS_URL)
    headlines = [entry.title for entry in feed.entries]
    return headlines

def main():
    print("Fetching BBC News headlines...")
    headlines = fetch_bbc_headlines()
    print(f"Fetched {len(headlines)} headlines.")
    summary_gen = SummaryGenerator()
    with open("config/config.yaml", "r") as f:
        config = yaml.safe_load(f)
    composer = NewsImageComposer(config)
    if headlines:
        headline = headlines[0]
        print(f"Processing headline: {headline}")
        summary = summary_gen.generate_summary(headline)
        print(f"Summary: {summary}")
        composer.generate_news_image_with_summary(headline, summary, style="news")

if __name__ == "__main__":
    main()
