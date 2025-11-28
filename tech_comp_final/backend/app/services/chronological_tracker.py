# backend/app/services/chronological_tracker.py
from collections import defaultdict
from typing import Dict, Any
import pandas as pd
import matplotlib.pyplot as plt
import os
from ..config import PLOTS_DIR
import logging

logger = logging.getLogger(__name__)
os.makedirs(PLOTS_DIR, exist_ok=True)

class ChronologicalTracker:
    def __init__(self):
        pass

    def track_progress(self, country: str, domain: str, country_data: Dict, time_range: int = None) -> Dict[str, Any]:
        counts = defaultdict(int)
        items_by_year = defaultdict(list)

        for bucket in ("publications", "patents", "news", "tim", "aspi"):
            for item in country_data.get(bucket, []):
                y = item.get("year")
                if not y:
                    continue
                try:
                    y = int(y)
                except Exception:
                    continue
                if time_range:
                    import datetime
                    if y < (pd.Timestamp.now().year - time_range + 1):
                        continue
                counts[y] += 1
                items_by_year[y].append(item)

        timeline = []
        for year in sorted(counts.keys(), reverse=True):
            timeline.append({
                "year": year,
                "total_events": counts[year],
                "highlights": [f"{it.get('title')[:250]} ({it.get('source')})" for it in items_by_year[year][:6]],
                "items": items_by_year[year][:15]
            })

        years_sorted = sorted(counts.keys())
        if years_sorted:
            most_active_year = max(counts.items(), key=lambda x: x[1])[0]
            activity_trend = "increasing" if len(years_sorted)>=2 and counts[years_sorted[-1]] > counts[years_sorted[-2]] else "stable_or_decreasing"
            trends = {
                "activity_trend": activity_trend,
                "acceleration": "increasing" if activity_trend=="increasing" else "flat",
                "most_active_year": most_active_year
            }
        else:
            trends = {"activity_trend": "no_data", "acceleration": "no_data", "most_active_year": None}

        # create simple plot
        plot_path = None
        try:
            years = sorted(counts.keys())
            values = [counts[y] for y in years]
            if years:
                plt.figure(figsize=(7,3.5))
                plt.plot(years, values, marker='o')
                plt.fill_between(years, values, alpha=0.12)
                plt.title(f"{country} — {domain} activity by year")
                plt.xlabel("Year")
                plt.ylabel("Count")
                plt.tight_layout()
                safe_name = f"{country}_{domain}_activity".replace(" ", "_").replace("/", "_")
                plot_path = os.path.join(PLOTS_DIR, f"{safe_name}.png")
                plt.savefig(plot_path)
                plt.close()
        except Exception as e:
            logger.exception("Failed to create plot: %s", e)
            plot_path = None

        return {
            "timeline": timeline,
            "trends": trends,
            "plot_path": plot_path
        }
