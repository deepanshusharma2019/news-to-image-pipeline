"""
Scheduler Module
Handles automated scheduling of news fetching and image generation.
"""

import logging
import time
import threading
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from typing import Dict, List


class NewsImageScheduler:
    """Scheduler for automated news-to-image generation."""
    
    def __init__(self, news_fetcher, image_generator, config: Dict):
        """Initialize scheduler with news fetcher, image generator, and config."""
        self.news_fetcher = news_fetcher
        self.image_generator = image_generator
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Scheduler configuration
        self.scheduler = BackgroundScheduler()
        self.interval_hours = config.get('interval_hours', 1)
        self.max_images_per_run = config.get('max_images_per_run', 3)
        self.styles = config.get('styles', ['news illustration', 'funny', 'artistic'])
        
        # Tracking
        self.last_headlines = set()
        self.generation_history = []
        
    def start(self):
        """Start the scheduled automation."""
        try:
            self.logger.info("Starting news-to-image automation scheduler")
            
            # Add scheduled job
            if self.config.get('use_cron', False):
                # Use cron expression if specified
                cron_expr = self.config.get('cron_expression', '0 * * * *')  # Every hour
                trigger = CronTrigger.from_crontab(cron_expr)
            else:
                # Use interval trigger
                trigger = IntervalTrigger(hours=self.interval_hours)
            
            self.scheduler.add_job(
                func=self.run_generation_cycle,
                trigger=trigger,
                id='news_image_generation',
                name='News to Image Generation',
                replace_existing=True
            )
            
            # Start scheduler
            self.scheduler.start()
            
            # Run initial generation
            if self.config.get('run_immediately', True):
                self.logger.info("Running initial generation cycle")
                threading.Thread(target=self.run_generation_cycle, daemon=True).start()
            
            # Keep main thread alive
            self._keep_alive()
            
        except KeyboardInterrupt:
            self.logger.info("Scheduler stopped by user")
            self.stop()
        except Exception as e:
            self.logger.error(f"Scheduler error: {e}")
            self.stop()
    
    def stop(self):
        """Stop the scheduler."""
        self.logger.info("Stopping scheduler")
        self.scheduler.shutdown()
    
    def run_generation_cycle(self):
        """Run one complete generation cycle."""
        try:
            start_time = datetime.now()
            self.logger.info(f"Starting generation cycle at {start_time}")
            
            # Fetch latest headlines
            headlines = self.news_fetcher.get_latest_headlines(limit=20)
            if not headlines:
                self.logger.warning("No headlines fetched, skipping cycle")
                return
            
            # Filter out headlines we've already processed
            new_headlines = [h for h in headlines if h not in self.last_headlines]
            if not new_headlines:
                self.logger.info("No new headlines found, using latest headlines")
                new_headlines = headlines[:self.max_images_per_run]
            
            # Select headlines for generation
            selected_headlines = self._select_headlines_for_generation(new_headlines)
            
            # Generate images
            generated_count = 0
            for i, headline in enumerate(selected_headlines):
                try:
                    # Choose style for this headline
                    style = self._choose_style_for_headline(headline, i)
                    
                    self.logger.info(f"Generating image {i+1}/{len(selected_headlines)}: {headline[:50]}...")
                    
                    # Generate image
                    image_path = self.image_generator.generate_from_headline(headline, style)
                    
                    if image_path:
                        generated_count += 1
                        self._record_generation(headline, style, image_path)
                        self.logger.info(f"Successfully generated: {image_path}")
                    else:
                        self.logger.error(f"Failed to generate image for: {headline[:50]}")
                    
                    # Small delay between generations
                    if i < len(selected_headlines) - 1:
                        time.sleep(self.config.get('generation_delay', 5))
                        
                except Exception as e:
                    self.logger.error(f"Error generating image for headline '{headline[:50]}': {e}")
            
            # Update tracking
            self.last_headlines.update(headlines[:50])  # Keep last 50 headlines in memory
            
            # Log cycle completion
            duration = datetime.now() - start_time
            self.logger.info(f"Generation cycle completed: {generated_count}/{len(selected_headlines)} "
                           f"images generated in {duration.total_seconds():.1f}s")
            
            # Cleanup if configured
            if self.config.get('cleanup_enabled', False):
                self._cleanup_old_images()
                
        except Exception as e:
            self.logger.error(f"Error in generation cycle: {e}")
    
    def _select_headlines_for_generation(self, headlines: List[str]) -> List[str]:
        """Select the most interesting headlines for image generation."""
        # Priority keywords for more interesting headlines
        priority_keywords = self.config.get('priority_keywords', [
            'breakthrough', 'discover', 'amazing', 'incredible', 'shocking',
            'bizarre', 'unusual', 'first', 'largest', 'smallest', 'record'
        ])
        
        # Score headlines
        scored_headlines = []
        for headline in headlines:
            score = 0
            headline_lower = headline.lower()
            
            # Boost score for priority keywords
            for keyword in priority_keywords:
                if keyword in headline_lower:
                    score += 10
            
            # Boost score for longer headlines (more descriptive)
            score += min(len(headline) // 10, 5)
            
            # Penalize very short headlines
            if len(headline) < 30:
                score -= 5
            
            scored_headlines.append((score, headline))
        
        # Sort by score and take top headlines
        scored_headlines.sort(reverse=True)
        selected = [headline for _, headline in scored_headlines[:self.max_images_per_run]]
        
        return selected
    
    def _choose_style_for_headline(self, headline: str, index: int) -> str:
        """Choose appropriate style for a headline."""
        headline_lower = headline.lower()
        
        # Determine style based on content
        if any(word in headline_lower for word in ['funny', 'bizarre', 'weird', 'unusual', 'odd']):
            return 'funny'
        elif any(word in headline_lower for word in ['art', 'culture', 'design', 'creative']):
            return 'artistic'
        elif any(word in headline_lower for word in ['breaking', 'urgent', 'news', 'report']):
            return 'news illustration'
        else:
            # Cycle through styles
            return self.styles[index % len(self.styles)]
    
    def _record_generation(self, headline: str, style: str, image_path: str):
        """Record a successful generation."""
        record = {
            'timestamp': datetime.now(),
            'headline': headline,
            'style': style,
            'image_path': image_path
        }
        
        self.generation_history.append(record)
        
        # Limit history size
        max_history = self.config.get('max_history', 1000)
        if len(self.generation_history) > max_history:
            self.generation_history = self.generation_history[-max_history:]
    
    def _cleanup_old_images(self):
        """Clean up old generated images."""
        try:
            max_age_days = self.config.get('max_image_age_days', 7)
            cutoff_date = datetime.now() - timedelta(days=max_age_days)
            
            output_dir = self.image_generator.output_dir
            deleted_count = 0
            
            for image_file in output_dir.glob('*.png'):
                try:
                    file_time = datetime.fromtimestamp(image_file.stat().st_mtime)
                    if file_time < cutoff_date:
                        image_file.unlink()
                        deleted_count += 1
                except Exception as e:
                    self.logger.warning(f"Could not delete {image_file}: {e}")
            
            if deleted_count > 0:
                self.logger.info(f"Cleaned up {deleted_count} old images")
                
        except Exception as e:
            self.logger.error(f"Cleanup error: {e}")
    
    def _keep_alive(self):
        """Keep the main thread alive while scheduler runs."""
        try:
            while True:
                time.sleep(60)  # Check every minute
                
                # Log status periodically
                if datetime.now().minute == 0:  # Every hour
                    self._log_status()
                    
        except KeyboardInterrupt:
            self.logger.info("Received interrupt signal")
    
    def _log_status(self):
        """Log current scheduler status."""
        next_run = self.scheduler.get_job('news_image_generation').next_run_time
        history_count = len(self.generation_history)
        
        self.logger.info(f"Scheduler status - Next run: {next_run}, "
                        f"Total images generated: {history_count}")
    
    def get_generation_stats(self) -> Dict:
        """Get generation statistics."""
        now = datetime.now()
        today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        today_count = len([r for r in self.generation_history if r['timestamp'] >= today])
        total_count = len(self.generation_history)
        
        return {
            'total_generated': total_count,
            'generated_today': today_count,
            'last_generation': self.generation_history[-1]['timestamp'] if self.generation_history else None,
            'scheduler_running': self.scheduler.running
        }
