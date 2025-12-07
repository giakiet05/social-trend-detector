"""
Business Metrics stage: Calculate marketing-relevant metrics for trends.
"""

from typing import List, Dict
import logging
from datetime import datetime, timedelta
from collections import Counter
import statistics

from .base_stage import BaseStage
from consumer.models.schemas import Trend

logger = logging.getLogger(__name__)


class BusinessMetricsStage(BaseStage):
    """Calculate business metrics for marketing applications."""

    def __init__(self):
        super().__init__("BusinessMetricsStage")

    def execute(self, trends: List[Trend]) -> List[Trend]:
        """
        Add business metrics to each trend.

        Args:
            trends: List of analyzed trends

        Returns:
            Trends enriched with business metrics
        """
        self.log_start()

        if not trends:
            self.log_skip("No trends to enrich")
            return []

        enriched_trends = []

        for trend in trends:
            try:
                # Calculate core metrics
                trend.viral_score = self._calculate_viral_score(trend)
                trend.growth_rate = self._calculate_growth_rate(trend)
                trend.estimated_reach = self._calculate_estimated_reach(trend)
                trend.engagement_rate = self._calculate_engagement_rate(trend)
                trend.peak_hours = self._analyze_peak_hours(trend)
                trend.audience_demographics = self._analyze_demographics(trend)
                trend.content_insights = self._generate_content_insights(trend)
                trend.hashtag_performance = self._analyze_hashtag_performance(trend)

                enriched_trends.append(trend)

                logger.info(f"   ✅ {trend.topic}: viral_score={trend.viral_score:.1f}, "
                           f"reach={trend.estimated_reach:,}, engagement={trend.engagement_rate:.1%}")

            except Exception as e:
                logger.error(f"Failed to calculate metrics for '{trend.topic}': {e}")
                # Add trend with default metrics
                enriched_trends.append(trend)

        self.log_complete(f"Enriched {len(enriched_trends)} trends with business metrics")
        return enriched_trends

    def _calculate_viral_score(self, trend: Trend) -> float:
        """
        Calculate viral potential score (1-10).
        
        Factors:
        - Engagement rate (40%)
        - Cross-platform spread (30%) 
        - Content volume (20%)
        - Audience reach (10%)
        """
        try:
            # Factor 1: Engagement rate (0-1 → 0-4 points)
            engagement_score = min(4.0, trend.engagement_rate * 40)
            
            # Factor 2: Cross-platform spread (0-3 points)
            platform_count = len(trend.source_counts)
            platform_score = min(3.0, platform_count)
            
            # Factor 3: Content volume (0-2 points)  
            volume_score = min(2.0, trend.video_count / 25)  # 25+ videos = max score
            
            # Factor 4: Audience reach (0-1 points)
            reach_score = min(1.0, trend.estimated_reach / 1000000)  # 1M+ = max score
            
            total_score = engagement_score + platform_score + volume_score + reach_score
            
            # Scale to 1-10
            viral_score = max(1.0, min(10.0, total_score))
            
            logger.debug(f"   Viral score breakdown - engagement: {engagement_score:.1f}, "
                        f"platforms: {platform_score:.1f}, volume: {volume_score:.1f}, "
                        f"reach: {reach_score:.1f} → total: {viral_score:.1f}")
            
            return round(viral_score, 1)
            
        except Exception as e:
            logger.warning(f"Viral score calculation failed: {e}")
            return 1.0

    def _calculate_growth_rate(self, trend: Trend) -> float:
        """
        Calculate growth rate (simplified - based on recency of content).
        
        Note: Real implementation would need historical data comparison.
        """
        try:
            if not trend.sample_videos:
                return 0.0
                
            # Analyze timestamps to estimate growth velocity
            now = datetime.utcnow()
            recent_count = 0
            
            for video in trend.sample_videos:
                if 'timestamp' in video or 'published_at' in video:
                    timestamp_str = video.get('timestamp') or video.get('published_at')
                    try:
                        if isinstance(timestamp_str, str):
                            # Parse various timestamp formats
                            pub_time = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                            hours_ago = (now - pub_time).total_seconds() / 3600
                            
                            # Count content from last 24 hours
                            if hours_ago <= 24:
                                recent_count += 1
                    except:
                        continue
            
            # Simple growth estimation: % of content that's recent
            if trend.video_count > 0:
                recency_ratio = recent_count / trend.video_count
                # Scale to percentage
                growth_rate = recency_ratio * 100
                return round(growth_rate, 1)
            
            return 0.0
            
        except Exception as e:
            logger.warning(f"Growth rate calculation failed: {e}")
            return 0.0

    def _calculate_estimated_reach(self, trend: Trend) -> int:
        """
        Estimate potential audience reach.
        
        Based on:
        - Author follower counts (if available)
        - Platform multipliers
        - Content virality factors
        """
        try:
            total_reach = 0
            
            for video in trend.sample_videos:
                # Extract author followers if available
                author_followers = 0
                if 'author_followers' in video:
                    author_followers = video.get('author_followers', 0)
                elif 'metadata' in video and 'author_fans' in video['metadata']:
                    author_followers = video['metadata'].get('author_fans', 0)
                
                total_reach += author_followers
            
            # If no follower data, estimate from engagement
            if total_reach == 0:
                # Rough estimate: views * platform multiplier
                platform_multiplier = {
                    'tiktok': 1.5,   # TikTok has good organic reach
                    'youtube': 1.2,  # YouTube moderate organic reach  
                    'vnexpress': 2.0 # News can spread wide
                }
                
                for source, count in trend.source_counts.items():
                    multiplier = platform_multiplier.get(source, 1.0)
                    total_reach += trend.total_views * multiplier * 0.1  # 10% reach-to-view ratio
            
            # Cap at reasonable maximum
            estimated_reach = min(10_000_000, int(total_reach))
            
            return estimated_reach
            
        except Exception as e:
            logger.warning(f"Reach estimation failed: {e}")
            return trend.total_views  # Fallback

    def _calculate_engagement_rate(self, trend: Trend) -> float:
        """Calculate overall engagement rate."""
        try:
            if trend.total_views == 0:
                return 0.0
                
            # Include all engagement types
            total_engagement = trend.total_likes
            
            # Add comments and shares if available in sample videos
            total_comments = 0
            total_shares = 0
            
            for video in trend.sample_videos:
                total_comments += video.get('comments', 0)
                total_shares += video.get('shares', 0)
            
            total_engagement += total_comments + total_shares
            
            engagement_rate = total_engagement / trend.total_views
            return min(1.0, engagement_rate)  # Cap at 100%
            
        except Exception as e:
            logger.warning(f"Engagement rate calculation failed: {e}")
            return 0.0

    def _analyze_peak_hours(self, trend: Trend) -> List[str]:
        """Analyze peak engagement hours from sample videos."""
        try:
            hours = []
            
            for video in trend.sample_videos:
                timestamp_str = video.get('timestamp') or video.get('published_at')
                if timestamp_str:
                    try:
                        if isinstance(timestamp_str, str):
                            pub_time = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                            hours.append(pub_time.hour)
                    except:
                        continue
            
            if not hours:
                return ["19:00", "20:00"]  # Default peak hours
                
            # Find top 3 most common hours
            hour_counts = Counter(hours)
            top_hours = hour_counts.most_common(3)
            
            # Format as time strings
            peak_hours = [f"{hour:02d}:00" for hour, count in top_hours]
            
            return peak_hours[:3]  # Max 3 peak hours
            
        except Exception as e:
            logger.warning(f"Peak hours analysis failed: {e}")
            return ["19:00", "20:00"]  # Default

    def _analyze_demographics(self, trend: Trend) -> Dict:
        """Analyze audience demographics (simplified version)."""
        try:
            demographics = {
                "primary_platforms": [],
                "content_sources": len(trend.source_counts),
                "geographic_spread": "Vietnam",  # Default for Vietnamese content
                "estimated_age_groups": {
                    "18-24": 30,
                    "25-34": 40,
                    "35-44": 20,
                    "45+": 10
                }
            }
            
            # Analyze platform distribution
            total_content = sum(trend.source_counts.values())
            for source, count in trend.source_counts.items():
                if count / total_content >= 0.3:  # 30%+ presence
                    demographics["primary_platforms"].append(source)
            
            return demographics
            
        except Exception as e:
            logger.warning(f"Demographics analysis failed: {e}")
            return {}

    def _generate_content_insights(self, trend: Trend) -> Dict:
        """Generate actionable content insights."""
        try:
            insights = {
                "optimal_content_length": "Short-form preferred",
                "trending_formats": [],
                "engagement_drivers": [],
                "posting_strategy": {
                    "frequency": "2-3 posts per day",
                    "timing": "Peak hours: " + ", ".join(self._analyze_peak_hours(trend)),
                    "platforms": list(trend.source_counts.keys())
                }
            }
            
            # Analyze content formats from source distribution
            if 'tiktok' in trend.source_counts:
                insights["trending_formats"].append("Short videos")
            if 'youtube' in trend.source_counts:
                insights["trending_formats"].append("Long-form videos")
            if 'vnexpress' in trend.source_counts:
                insights["trending_formats"].append("News articles")
                
            # Determine engagement drivers
            if trend.engagement_rate > 0.05:  # 5%+
                insights["engagement_drivers"].append("High shareability")
            if trend.video_count > 50:
                insights["engagement_drivers"].append("High content volume")
            if len(trend.source_counts) > 2:
                insights["engagement_drivers"].append("Cross-platform appeal")
            
            return insights
            
        except Exception as e:
            logger.warning(f"Content insights generation failed: {e}")
            return {}

    def _analyze_hashtag_performance(self, trend: Trend) -> List[Dict]:
        """Analyze hashtag performance and trends."""
        try:
            hashtag_performance = []
            
            # Analyze trend keywords as hashtag potential
            for i, keyword in enumerate(trend.keywords[:5]):  # Top 5 keywords
                performance = {
                    "hashtag": f"#{keyword.replace(' ', '')}",
                    "relevance_score": max(1, 10 - i),  # Higher score for top keywords
                    "estimated_reach": int(trend.estimated_reach * (0.8 - i * 0.1)),  # Diminishing reach
                    "competition_level": "medium"  # Default
                }
                hashtag_performance.append(performance)
            
            return hashtag_performance
            
        except Exception as e:
            logger.warning(f"Hashtag performance analysis failed: {e}")
            return []