"""
Utility Functions
Helper functions for logging, configuration, and common operations.
"""

import logging
import yaml
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional


def setup_logging(level: int = logging.INFO, log_file: Optional[str] = None):
    """Set up logging configuration."""
    # Create logs directory
    log_dir = Path('output/logs')
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Default log file with timestamp
    if not log_file:
        timestamp = datetime.now().strftime("%Y%m%d")
        log_file = log_dir / f"news_to_image_{timestamp}.log"
    
    # Configure logging
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    # Set specific loggers
    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('websocket').setLevel(logging.WARNING)


def load_config(config_path: str) -> Dict[str, Any]:
    """Load configuration from YAML file."""
    config_file = Path(config_path)
    
    if not config_file.exists():
        # Create default config if not exists
        default_config = create_default_config()
        save_config(default_config, config_path)
        return default_config
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as e:
        logging.error(f"Error loading config: {e}")
        return create_default_config()


def save_config(config: Dict[str, Any], config_path: str):
    """Save configuration to YAML file."""
    config_file = Path(config_path)
    config_file.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, indent=2)
    except Exception as e:
        logging.error(f"Error saving config: {e}")


def create_default_config() -> Dict[str, Any]:
    """Create default configuration."""
    return {
        'news': {
            'rss_feeds': [
                {'name': 'BBC News', 'url': 'http://feeds.bbci.co.uk/news/rss.xml'},
                {'name': 'CNN', 'url': 'http://rss.cnn.com/rss/edition.rss'},
                {'name': 'Reuters', 'url': 'http://feeds.reuters.com/reuters/topNews'},
                {'name': 'Associated Press', 'url': 'https://feeds.apnews.com/rss/apf-topnews'}
            ],
            'news_api_key': None,  # Optional: get from https://newsapi.org/
            'keywords': ['technology', 'science', 'world', 'breaking']
        },
        'comfyui': {
            'server_address': '127.0.0.1:8188',
            'workflow_path': 'workflows/news_image.json',
            'output_dir': 'output/images',
            'width': 512,
            'height': 512,
            'steps': 25,
            'cfg_scale': 7.0,
            'sampler': 'dpmpp_2m',
            'scheduler': 'karras',
            'seed': -1,
            'negative_prompt': 'ugly, deformed, blurry, bad anatomy, low quality, text, watermark',
            'prompt_templates': {
                'news': '{headline}, news illustration, professional, high quality, detailed, digital art',
                'funny': '{headline}, funny, cartoon style, humorous, meme-worthy, comedy, vibrant colors',
                'artistic': '{headline}, artistic interpretation, abstract, creative, modern art, stylized',
                'realistic': '{headline}, photorealistic, documentary style, journalistic, high resolution'
            }
        },
        'scheduler': {
            'interval_hours': 1,
            'max_images_per_run': 3,
            'styles': ['news illustration', 'funny', 'artistic'],
            'use_cron': False,
            'cron_expression': '0 * * * *',  # Every hour
            'run_immediately': True,
            'generation_delay': 5,  # seconds between generations
            'priority_keywords': [
                'breakthrough', 'discover', 'amazing', 'incredible', 'shocking',
                'bizarre', 'unusual', 'first', 'largest', 'smallest', 'record',
                'viral', 'trending', 'exclusive', 'mystery', 'secret'
            ],
            'cleanup_enabled': True,
            'max_image_age_days': 7,
            'max_history': 1000
        }
    }


def clean_text_for_filename(text: str, max_length: int = 50) -> str:
    """Clean text to be safe for use in filenames."""
    # Remove or replace problematic characters
    clean_text = "".join(c for c in text if c.isalnum() or c in (' ', '-', '_')).strip()
    clean_text = clean_text.replace(' ', '_')
    
    # Limit length
    if len(clean_text) > max_length:
        clean_text = clean_text[:max_length]
    
    return clean_text


def format_headline_for_prompt(headline: str) -> str:
    """Format headline for use in image generation prompts."""
    # Remove quotes and clean up
    clean_headline = headline.replace('"', '').replace("'", "").strip()
    
    # Remove news source attributions
    if ' - ' in clean_headline:
        parts = clean_headline.split(' - ')
        clean_headline = parts[0].strip()  # Take the part before the dash
    
    # Limit length for prompt
    if len(clean_headline) > 100:
        clean_headline = clean_headline[:100] + "..."
    
    return clean_headline


def get_timestamp_string(format_str: str = "%Y%m%d_%H%M%S") -> str:
    """Get formatted timestamp string."""
    return datetime.now().strftime(format_str)


def ensure_directory_exists(directory: Path):
    """Ensure a directory exists, create if it doesn't."""
    directory.mkdir(parents=True, exist_ok=True)


def load_json_file(file_path: str) -> Optional[Dict]:
    """Load JSON file safely."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Error loading JSON file {file_path}: {e}")
        return None


def save_json_file(data: Dict, file_path: str):
    """Save data to JSON file."""
    try:
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logging.error(f"Error saving JSON file {file_path}: {e}")


def validate_url(url: str) -> bool:
    """Validate if a URL is properly formatted."""
    try:
        from urllib.parse import urlparse
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate text to specified length with suffix."""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def get_file_size_mb(file_path: Path) -> float:
    """Get file size in megabytes."""
    try:
        return file_path.stat().st_size / (1024 * 1024)
    except Exception:
        return 0.0


def cleanup_old_files(directory: Path, max_age_days: int = 7, pattern: str = "*"):
    """Clean up old files in a directory."""
    try:
        from datetime import timedelta
        
        cutoff_date = datetime.now() - timedelta(days=max_age_days)
        deleted_count = 0
        
        for file_path in directory.glob(pattern):
            if file_path.is_file():
                try:
                    file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                    if file_time < cutoff_date:
                        file_path.unlink()
                        deleted_count += 1
                except Exception as e:
                    logging.warning(f"Could not delete {file_path}: {e}")
        
        return deleted_count
    except Exception as e:
        logging.error(f"Cleanup error: {e}")
        return 0
