HOURLY_RATE_EUR = 80.0          # €80/hr default — overridable via carrier_settings
CO2_KG_PER_IDLE_HOUR = 2.5     # kg CO₂ per hour of idle/delay for a diesel HGV


def revenue_lost_eur(total_delay_minutes: int) -> float:
    """Convert total delay minutes into revenue lost in euros."""
    return round(total_delay_minutes / 60 * HOURLY_RATE_EUR, 2)


def co2_kg(total_delay_minutes: int) -> float:
    """Convert total delay minutes into kg CO₂ from idle burn."""
    return round(total_delay_minutes / 60 * CO2_KG_PER_IDLE_HOUR, 2)
