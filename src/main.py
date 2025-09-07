#!/usr/bin/env python3
"""
News to Image Automation Pipeline
Main application entry point for automated news fetching and image generation.
"""

import argparse
import logging
import sys
from pathlib import Path

# Add src to path for imports
sys.path.append(str(Path(__file__).parent))

from news_fetcher import NewsFetcher
from image_generator import ImageGenerator
from news_image_composer import NewsImageComposer
from summary_generator import SummaryGenerator
from scheduler import NewsImageScheduler
from utils import setup_logging, load_config


def main():
    """Main application entry point."""
    parser = argparse.ArgumentParser(description='News to Image Automation Pipeline')
    parser.add_argument('--mode', choices=['manual', 'schedule'], default='schedule',
                       help='Run mode: manual (one-time) or schedule (continuous)')
    parser.add_argument('--headline', type=str, help='Custom headline for manual image generation')
    parser.add_argument('--config', type=str, default='config/config.yaml',
                       help='Path to configuration file')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    setup_logging(log_level)
    logger = logging.getLogger(__name__)
    
    try:
        # Load configuration
        config = load_config(args.config)
        logger.info("Configuration loaded successfully")
        
        # Initialize components
        news_fetcher = NewsFetcher(config['news'])
        image_generator = ImageGenerator(config['comfyui'])
        news_composer = NewsImageComposer(config)
        summary_generator = SummaryGenerator()
        
        if args.mode == 'manual':
            if args.headline:
                # Generate image for custom headline
                logger.info(f"Generating image with summary for custom headline: {args.headline}")
                summary = summary_generator.generate_summary(args.headline)
                image_path = news_composer.generate_news_image_with_summary(args.headline, summary)
                logger.info(f"Composite image generated: {image_path}")
            else:
                # Fetch latest news and generate one image
                logger.info("Fetching latest news for manual generation")
                headlines = news_fetcher.get_latest_headlines()
                if headlines:
                    headline = headlines[0]
                    logger.info(f"Generating image with summary for: {headline}")
                    summary = summary_generator.generate_summary(headline)
                    image_path = news_composer.generate_news_image_with_summary(headline, summary)
                    logger.info(f"Composite image generated: {image_path}")
                else:
                    logger.error("No headlines found")
        
        elif args.mode == 'schedule':
            # Start scheduled automation
            logger.info("Starting scheduled news-to-image automation")
            scheduler = NewsImageScheduler(news_fetcher, image_generator, config['scheduler'])
            scheduler.start()
            
    except KeyboardInterrupt:
        logger.info("Application stopped by user")
    except Exception as e:
        logger.error(f"Application error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
