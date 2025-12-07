"""
Action Planning stage: Generate actionable marketing recommendations for trends.
"""

from typing import List, Dict
import logging
from datetime import datetime, timedelta

from .base_stage import BaseStage
from consumer.models.schemas import Trend

logger = logging.getLogger(__name__)


class ActionPlanningStage(BaseStage):
    """Generate actionable marketing recommendations for each trend."""

    def __init__(self):
        super().__init__("ActionPlanningStage")

    def execute(self, trends: List[Trend]) -> List[Trend]:
        """
        Add action plans to each trend.

        Args:
            trends: List of trends with business metrics

        Returns:
            Trends enriched with action plans
        """
        self.log_start()

        if not trends:
            self.log_skip("No trends to plan actions for")
            return []

        planned_trends = []

        for trend in trends:
            try:
                # Generate comprehensive action plan
                trend.action_plan = {
                    "priority_level": self._calculate_priority(trend),
                    "urgency": self._assess_urgency(trend),
                    "immediate_actions": self._get_immediate_actions(trend),
                    "content_strategy": self._generate_content_strategy(trend),
                    "platform_strategies": self._get_platform_strategies(trend),
                    "timeline": self._generate_timeline(trend),
                    "budget_recommendations": self._suggest_budget_allocation(trend),
                    "risk_factors": self._identify_risks(trend),
                    "success_metrics": self._define_success_metrics(trend)
                }

                planned_trends.append(trend)

                # Log key recommendations
                priority = trend.action_plan["priority_level"]
                urgency = trend.action_plan["urgency"]
                action_count = len(trend.action_plan["immediate_actions"])
                
                logger.info(f"   📋 {trend.topic}: {priority} priority, {urgency} urgency, "
                           f"{action_count} actions recommended")

            except Exception as e:
                logger.error(f"Failed to generate action plan for '{trend.topic}': {e}")
                # Add trend with empty action plan
                trend.action_plan = {"error": "Action planning failed"}
                planned_trends.append(trend)

        self.log_complete(f"Generated action plans for {len(planned_trends)} trends")
        return planned_trends

    def _calculate_priority(self, trend: Trend) -> str:
        """
        Calculate marketing priority level.
        
        Based on viral score, growth rate, and reach.
        """
        try:
            # Scoring algorithm
            score = 0
            
            # Viral score contribution (50%)
            score += trend.viral_score * 5
            
            # Growth rate contribution (30%)
            score += min(30, trend.growth_rate * 0.3)
            
            # Reach contribution (20%)  
            reach_score = min(20, trend.estimated_reach / 50000)  # 1M reach = 20 points
            score += reach_score
            
            # Priority thresholds
            if score >= 70:
                return "critical"
            elif score >= 50:
                return "high"
            elif score >= 30:
                return "medium" 
            else:
                return "low"
                
        except Exception:
            return "medium"  # Default fallback

    def _assess_urgency(self, trend: Trend) -> str:
        """Assess time-sensitive urgency for action."""
        try:
            # High urgency factors
            if (trend.viral_score >= 8.0 or 
                trend.growth_rate >= 50 or
                trend.engagement_rate >= 0.08):
                return "immediate"  # Act within 24 hours
                
            elif (trend.viral_score >= 6.0 or
                  trend.growth_rate >= 25):
                return "this_week"  # Plan for this week
                
            elif trend.viral_score >= 4.0:
                return "this_month"  # Monitor and plan
                
            else:
                return "monitor_only"  # Track for future
                
        except Exception:
            return "this_week"  # Safe default

    def _get_immediate_actions(self, trend: Trend) -> List[Dict]:
        """Generate list of immediate actionable steps."""
        actions = []
        
        try:
            priority = self._calculate_priority(trend)
            urgency = self._assess_urgency(trend)
            
            # Urgency-based actions
            if urgency == "immediate":
                actions.append({
                    "action": "Tạo nội dung ngay lập tức",
                    "description": f"Xu hướng '{trend.topic}' đang viral với điểm {trend.viral_score}/10",
                    "deadline": "24 giờ tới",
                    "priority": "critical"
                })
                
                actions.append({
                    "action": "Thiết lập monitoring alerts", 
                    "description": "Theo dõi mentions và sentiment realtime",
                    "deadline": "Ngay bây giờ",
                    "priority": "high"
                })
                
            elif urgency == "this_week":
                actions.append({
                    "action": "Lập kế hoạch content chi tiết",
                    "description": f"Chuẩn bị series content về '{trend.topic}'",
                    "deadline": "2-3 ngày tới", 
                    "priority": "high"
                })
                
            elif urgency == "this_month":
                actions.append({
                    "action": "Nghiên cứu xu hướng sâu hơn",
                    "description": "Phân tích competitor và tìm góc độ độc đáo",
                    "deadline": "Tuần tới",
                    "priority": "medium"
                })
                
            # Platform-specific actions
            platform_actions = self._get_platform_actions(trend)
            actions.extend(platform_actions)
            
            # Risk-based actions
            risk_actions = self._get_risk_mitigation_actions(trend)
            actions.extend(risk_actions)
            
            return actions[:8]  # Limit to top 8 actions
            
        except Exception as e:
            logger.warning(f"Failed to generate immediate actions: {e}")
            return [{
                "action": "Theo dõi xu hướng",
                "description": "Monitor trend development", 
                "deadline": "Continuous",
                "priority": "medium"
            }]

    def _get_platform_actions(self, trend: Trend) -> List[Dict]:
        """Generate platform-specific action items."""
        actions = []
        
        try:
            for platform, count in trend.source_counts.items():
                platform_percentage = count / trend.video_count
                
                if platform == 'tiktok' and platform_percentage >= 0.3:
                    actions.append({
                        "action": f"Chiến lược TikTok cho '{trend.topic}'",
                        "description": "Tạo video 15-30s, sử dụng trending effects và hashtags",
                        "platform": "tiktok",
                        "best_times": ", ".join(trend.peak_hours),
                        "priority": "high" if trend.viral_score >= 7 else "medium"
                    })
                    
                elif platform == 'youtube' and platform_percentage >= 0.3:
                    actions.append({
                        "action": f"Chiến lược YouTube cho '{trend.topic}'",
                        "description": "Tạo video dài 5-15 phút, tối ưu SEO và thumbnail",
                        "platform": "youtube", 
                        "content_type": "Long-form analysis/tutorial",
                        "priority": "medium"
                    })
                    
                elif platform == 'vnexpress' and count >= 1:
                    actions.append({
                        "action": f"PR/Media strategy cho '{trend.topic}'",
                        "description": "Liên hệ báo chí, tạo press release hoặc expert commentary",
                        "platform": "media",
                        "priority": "low"
                    })
                    
            return actions
            
        except Exception as e:
            logger.warning(f"Failed to generate platform actions: {e}")
            return []

    def _get_risk_mitigation_actions(self, trend: Trend) -> List[Dict]:
        """Generate risk mitigation actions."""
        actions = []
        
        try:
            # Negative sentiment risks
            if trend.sentiment == 'negative':
                actions.append({
                    "action": "Chuẩn bị crisis response plan",
                    "description": "Xu hướng có sentiment tiêu cực, cần cẩn trọng khi tham gia", 
                    "risk_type": "reputation",
                    "priority": "high"
                })
                
            # High competition warning
            if trend.viral_score >= 8.0:
                actions.append({
                    "action": "Phân tích competitive landscape", 
                    "description": "Trend rất hot, nhiều brand sẽ tham gia. Cần góc độ độc đáo",
                    "risk_type": "competition",
                    "priority": "medium"
                })
                
            # Low engagement warning
            if trend.engagement_rate < 0.02:  # 2%
                actions.append({
                    "action": "Đánh giá lại audience fit",
                    "description": "Engagement thấp, có thể không phù hợp với target audience",
                    "risk_type": "low_engagement", 
                    "priority": "low"
                })
                
            return actions
            
        except Exception as e:
            logger.warning(f"Failed to generate risk actions: {e}")
            return []

    def _generate_content_strategy(self, trend: Trend) -> Dict:
        """Generate content strategy recommendations."""
        try:
            strategy = {
                "recommended_formats": [],
                "content_angles": [],
                "posting_frequency": "",
                "hashtag_strategy": [],
                "collaboration_opportunities": []
            }
            
            # Format recommendations based on platforms
            if 'tiktok' in trend.source_counts:
                strategy["recommended_formats"].append("Short-form videos (15-30s)")
                strategy["content_angles"].append("Trends, challenges, quick tips")
                
            if 'youtube' in trend.source_counts:
                strategy["recommended_formats"].append("Long-form videos (5-15 mins)")
                strategy["content_angles"].append("Deep analysis, tutorials, reviews")
                
            # Posting frequency based on urgency
            urgency = self._assess_urgency(trend)
            if urgency == "immediate":
                strategy["posting_frequency"] = "Hàng ngày trong tuần đầu"
            elif urgency == "this_week":
                strategy["posting_frequency"] = "3-4 posts/tuần"
            else:
                strategy["posting_frequency"] = "2-3 posts/tuần"
                
            # Hashtag strategy
            for hashtag_data in trend.hashtag_performance[:3]:
                strategy["hashtag_strategy"].append({
                    "hashtag": hashtag_data.get("hashtag", ""),
                    "reach": hashtag_data.get("estimated_reach", 0)
                })
                
            return strategy
            
        except Exception as e:
            logger.warning(f"Content strategy generation failed: {e}")
            return {}

    def _get_platform_strategies(self, trend: Trend) -> Dict:
        """Generate platform-specific detailed strategies."""
        try:
            strategies = {}
            
            for platform in trend.source_counts.keys():
                if platform == 'tiktok':
                    strategies[platform] = {
                        "content_type": "Short videos với trending sounds",
                        "optimal_times": trend.peak_hours,
                        "hashtag_count": "3-5 hashtags per post",
                        "engagement_tactics": ["Challenges", "Duets", "Trending effects"]
                    }
                    
                elif platform == 'youtube':
                    strategies[platform] = {
                        "content_type": "Educational/entertainment videos",
                        "optimal_length": "5-15 minutes",
                        "SEO_focus": f"Keywords: {', '.join(trend.keywords[:5])}",
                        "thumbnail_style": "Eye-catching với text overlay"
                    }
                    
                elif platform == 'vnexpress':
                    strategies[platform] = {
                        "approach": "Expert commentary hoặc data-driven insights", 
                        "angle": "Newsworthy perspective on trend",
                        "timing": "React to peak news cycle"
                    }
                    
            return strategies
            
        except Exception as e:
            logger.warning(f"Platform strategies generation failed: {e}")
            return {}

    def _generate_timeline(self, trend: Trend) -> Dict:
        """Generate implementation timeline."""
        try:
            urgency = self._assess_urgency(trend)
            timeline = {}
            
            if urgency == "immediate":
                timeline = {
                    "0-24h": "Tạo và post content đầu tiên",
                    "24-48h": "Monitor performance, adjust strategy",
                    "48-72h": "Scale successful content", 
                    "1_week": "Evaluate overall campaign performance"
                }
            elif urgency == "this_week":
                timeline = {
                    "Day_1-2": "Research và content planning",
                    "Day_3-5": "Tạo content và schedule posts",
                    "Week_2": "Optimize dựa trên performance",
                    "Week_3-4": "Scale hoặc pivot strategy"
                }
            else:
                timeline = {
                    "Week_1": "Monitor trend development",
                    "Week_2-3": "Plan content if trend remains strong", 
                    "Month_1": "Implement if opportunity still exists"
                }
                
            return timeline
            
        except Exception as e:
            logger.warning(f"Timeline generation failed: {e}")
            return {}

    def _suggest_budget_allocation(self, trend: Trend) -> Dict:
        """Suggest budget allocation recommendations."""
        try:
            priority = self._calculate_priority(trend)
            
            budget_suggestions = {
                "organic_vs_paid": {},
                "platform_allocation": {},
                "content_production": {},
                "total_recommendation": ""
            }
            
            if priority == "critical":
                budget_suggestions.update({
                    "organic_vs_paid": {"organic": 70, "paid": 30},
                    "total_recommendation": "High investment - 20-30% of monthly marketing budget",
                    "content_production": {"video": 60, "graphics": 25, "copywriting": 15}
                })
            elif priority == "high":
                budget_suggestions.update({
                    "organic_vs_paid": {"organic": 80, "paid": 20},
                    "total_recommendation": "Medium investment - 10-15% of monthly marketing budget"
                })
            else:
                budget_suggestions.update({
                    "organic_vs_paid": {"organic": 90, "paid": 10}, 
                    "total_recommendation": "Low investment - 5-10% of monthly marketing budget"
                })
                
            return budget_suggestions
            
        except Exception as e:
            logger.warning(f"Budget suggestions generation failed: {e}")
            return {}

    def _identify_risks(self, trend: Trend) -> List[str]:
        """Identify potential risks and challenges."""
        risks = []
        
        try:
            # Sentiment-based risks
            if trend.sentiment == 'negative':
                risks.append("Negative sentiment - có thể ảnh hưởng xấu đến brand image")
                
            # Competition risks
            if trend.viral_score >= 8.0:
                risks.append("High competition - nhiều brands sẽ tham gia, khó nổi bật")
                
            # Timing risks
            if trend.growth_rate < 10:
                risks.append("Declining momentum - trend có thể đang giảm nhiệt")
                
            # Platform concentration risk
            platform_count = len(trend.source_counts)
            if platform_count == 1:
                risks.append("Single platform dependency - risk nếu platform thay đổi algorithm")
                
            # Low engagement risk
            if trend.engagement_rate < 0.02:
                risks.append("Low engagement rate - có thể không resonate với audience")
                
            return risks
            
        except Exception as e:
            logger.warning(f"Risk identification failed: {e}")
            return ["Unknown risks - cần thêm analysis"]

    def _define_success_metrics(self, trend: Trend) -> Dict:
        """Define KPIs and success metrics."""
        try:
            metrics = {
                "primary_kpis": [],
                "secondary_kpis": [], 
                "benchmarks": {},
                "tracking_frequency": ""
            }
            
            # Primary KPIs based on trend characteristics
            if trend.engagement_rate > 0.05:
                metrics["primary_kpis"] = ["Engagement rate", "Share count", "Comment sentiment"]
            else:
                metrics["primary_kpis"] = ["Reach", "Impressions", "Click-through rate"]
                
            # Secondary metrics
            metrics["secondary_kpis"] = ["Follower growth", "Brand mention sentiment", "Traffic to website"]
            
            # Benchmarks
            metrics["benchmarks"] = {
                "target_engagement": f"{trend.engagement_rate * 1.2:.1%}",  # 20% improvement
                "target_reach": f"{int(trend.estimated_reach * 0.1):,}",  # 10% of trend reach
                "success_threshold": "50% above current average performance"
            }
            
            # Tracking frequency
            urgency = self._assess_urgency(trend)
            if urgency == "immediate":
                metrics["tracking_frequency"] = "Hourly for first 48h, then daily"
            else:
                metrics["tracking_frequency"] = "Daily for first week, then weekly"
                
            return metrics
            
        except Exception as e:
            logger.warning(f"Success metrics definition failed: {e}")
            return {}