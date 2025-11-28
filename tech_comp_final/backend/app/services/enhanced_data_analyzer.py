# backend/app/services/enhanced_data_analyzer.py
from typing import Dict, Any
from collections import defaultdict
import math

class EnhancedDataAnalyzer:
    def __init__(self):
        pass

    def analyze_and_compare(self, country1, country2, domain, data1: Dict, data2: Dict, detail_level="standard") -> Dict:
        def summarize(country, data):
            total = len(data.get("raw_text", []))
            pubs = len(data.get("publications", []))
            patents = len(data.get("patents", []))
            news = len(data.get("news", []))
            tim = len(data.get("tim", []))
            aspi = len(data.get("aspi", []))
            top_titles = []
            for bucket in ("publications", "patents", "tim", "aspi", "news"):
                for item in data.get(bucket, [])[:5]:
                    top_titles.append(f"{item.get('title')[:180]} ({item.get('source')})")
            summary = f"{country}: {total} items — pubs:{pubs}, patents:{patents}, tim:{tim}, aspi:{aspi}, news:{news}. Top items: " + " | ".join(top_titles[:6])
            return summary

        c1s = summarize(country1, data1)
        c2s = summarize(country2, data2)

        comparison = {
            "counts": {
                country1: len(data1.get("raw_text", [])),
                country2: len(data2.get("raw_text", []))
            },
            "publications": {
                country1: len(data1.get("publications", [])),
                country2: len(data2.get("publications", []))
            },
            "tim": {
                country1: len(data1.get("tim", [])),
                country2: len(data2.get("tim", []))
            }
        }

        overall = f"Comparison {country1} vs {country2} in {domain}.\n\n"
        overall += f"{country1}: {c1s}\n\n{country2}: {c2s}\n\n"
        if comparison["counts"][country1] > comparison["counts"][country2]:
            overall += f"{country1} shows higher recorded output than {country2}.\n"
        elif comparison["counts"][country1] < comparison["counts"][country2]:
            overall += f"{country2} shows higher recorded output than {country1}.\n"
        else:
            overall += "Both countries show similar volume in the searched sources.\n"

        # simple velocity metric: growth over last two years
        def velocity(data):
            years = [it.get("year") for it in data.get("raw_text", []) if it.get("year")]
            if len(years) < 2: return 0.0
            try:
                y_sorted = sorted(map(int, years))
                if len(y_sorted) >= 2:
                    return (y_sorted[-1] - y_sorted[0]) / len(y_sorted)
            except:
                pass
            return 0.0

        v1 = velocity(data1)
        v2 = velocity(data2)
        overall += f"Velocity metric (rough): {country1}: {v1:.2f}, {country2}: {v2:.2f}\n"

        return {
            "summary": {country1: c1s, country2: c2s},
            "comparison": comparison,
            "overall_analysis": overall
        }
