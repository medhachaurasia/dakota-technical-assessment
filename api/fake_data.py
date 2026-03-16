import random
import math
from datetime import datetime


def generate_enrichment(date: str, region: str) -> dict:
    dt = datetime.strptime(date, "%Y-%m-%d")
    month = dt.month

    # deterministic randomness for same date + region
    rng = random.Random(f"{date}-{region}")

    # temperature follows seasonality
    seasonal_temp = 15 + 20 * math.sin((2 * math.pi * (month - 3)) / 12)
    temperature_c = round(seasonal_temp + rng.uniform(-3, 3), 1)

    # demand increases when temperature moves away from a comfortable level
    temp_stress = abs(temperature_c - 18)
    demand_index = 0.45 + min(temp_stress / 35, 0.45) + rng.uniform(-0.05, 0.05)
    demand_index = round(max(0.40, min(demand_index, 1.00)), 2)

    # renewable share also has mild seasonality
    renewable_base = 35 + 10 * math.sin((2 * math.pi * (month - 1)) / 12)
    renewable_share_pct = round(max(10, min(60, renewable_base + rng.uniform(-5, 5))), 1)

    # grid stress based on demand
    if demand_index >= 0.85:
        grid_stress_level = "high"
    elif demand_index >= 0.65:
        grid_stress_level = "medium"
    else:
        grid_stress_level = "low"

    return {
        "date": date,
        "region": region,
        "temperature_c": temperature_c,
        "demand_index": demand_index,
        "grid_stress_level": grid_stress_level,
        "renewable_share_pct": renewable_share_pct,
    }