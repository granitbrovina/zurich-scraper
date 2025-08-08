#!/usr/bin/env python3
"""
Configuration file for Zurich Real Estate Investment Scraper
===========================================================

This file contains all configuration parameters, API endpoints,
scoring weights, and filter criteria for the investment analysis.
"""

# API Endpoints and Data Sources
API_ENDPOINTS = {
    'geo_admin': 'https://api3.geo.admin.ch/rest/services/api/MapServer',
    'building_register': 'ch.bfs.gebaeude_wohnungs_register',
    'zoning_layer': 'ch.are.bauzonen',
    'maps_zh': 'https://maps.zh.ch/services',
    'geak_certificates': 'https://www.geak.ch',  # Placeholder - actual API needed
    'building_permits': 'https://www.zh.ch/de/planen-bauen/baugesuche.html'
}

# Rental Market Platforms
RENTAL_PLATFORMS = {
    'comparis': 'https://www.comparis.ch/immobilien/mieten',
    'homegate': 'https://www.homegate.ch/mieten',
    'immoscout24': 'https://www.immoscout24.ch/de/mieten',
    'tutti': 'https://www.tutti.ch/de/immobilien/wohnung-mieten'
}

# A. Mandatory Location Filters
LOCATION_FILTERS = {
    'zip_code_range': (8000, 8099),  # Central Zurich ZIP codes
    'building_area_range': (1200, 2500),  # Building area in m²
    'max_construction_year': 1980,  # Older buildings for redevelopment
    'min_building_area': 1200,
    'max_building_area': 2500
}

# B. Condition-Based Filter Criteria
CONDITION_CRITERIA = {
    'target_energy_ratings': ['E', 'F', 'G'],  # Poor energy ratings
    'max_years_since_renovation': 20,  # No major works in 20+ years
    'problematic_heating_systems': ['oil', 'electric_old', 'coal'],
    'fire_safety_red_flags': ['no_sprinklers', 'no_fire_separation', 'old_escape_routes']
}

# C. Economic Underperformance Thresholds
ECONOMIC_THRESHOLDS = {
    'rent_below_market_threshold': 0.7,  # 30% below market
    'high_vacancy_days': 120,  # More than 4 months on market
    'low_tax_value_ratio': 0.6,  # Tax value much lower than market
    'photo_quality_threshold': 3  # Poor online presentation score
}

# D. Ownership/Transaction Signal Indicators
OWNERSHIP_SIGNALS = {
    'frequent_ownership_changes': 2,  # 2+ sales in 10 years
    'target_owner_types': ['Stiftung', 'family', 'elderly'],
    'mortgage_free_indicators': ['no_mortgage', 'unencumbered'],
    'zoning_underutilization_threshold': 0.3,  # 30%+ expansion potential
    'small_unit_threshold': 35  # Average unit size < 35 m²
}

# Scoring Weights and Points
SCORING_WEIGHTS = {
    # Condition-based scoring (renovation pressure)
    'energy_rating_poor': 3,  # GEAK rating E, F, or G
    'no_recent_renovations': 2,  # No major works in 20+ years
    'old_heating_system': 3,  # Oil heating or no heat pump
    'fire_safety_issues': 2,  # Non-compliance indicators
    
    # Economic underperformance scoring
    'rent_below_market': 3,  # Rent >30% below market
    'high_vacancy': 1,  # Long time on market
    'low_value_ratio': 2,  # Tax value << market value
    'poor_presentation': 1,  # No/poor photos
    
    # Ownership/transaction signals
    'frequent_changes': 1,  # Multiple ownership changes
    'institutional_owner': 1,  # Stiftung or family ownership
    'no_mortgage': 1,  # Unencumbered property
    'zoning_potential': 2,  # Can increase building volume 25%+
    'small_units': 1,  # Reconfigurable layout
    
    # Building characteristics
    'very_old_building': 2,  # Pre-1950 construction
    'old_building': 1,  # Pre-1980 construction
    'optimal_size': 1,  # Ideal building size
    
    # Negative factors
    'heritage_protection': -3,  # Major restriction
    'too_many_units': -2,  # >50 units (management complexity)
    'recent_renovation': -1  # Recently renovated (less opportunity)
}

# Building Size Optimization
SIZE_PREFERENCES = {
    'optimal_range': (1200, 2500),  # Required range for filtering
    'ideal_range': (1500, 2000),   # Bonus points range
    'manageable_max': 3000,        # Upper manageable limit
    'minimum_viable': 800          # Minimum for consideration
}

# Age-based Scoring
AGE_SCORING = {
    'very_old_threshold': 1950,    # Pre-1950 = maximum opportunity
    'old_threshold': 1980,         # Pre-1980 = good opportunity
    'modern_threshold': 2000,      # Post-2000 = limited opportunity
    'very_old_bonus': 2,
    'old_bonus': 1
}

# Rate Limiting and Performance
SCRAPING_CONFIG = {
    'request_delay': 0.1,          # Minimum delay between API calls (seconds)
    'max_concurrent_threads': 5,   # Maximum concurrent scraping threads
    'timeout_seconds': 10,         # Request timeout
    'retry_attempts': 3,           # Number of retry attempts
    'cache_expiry_days': 7,        # Days to cache API responses
    'max_properties_per_run': 1000 # Limit for testing/development
}

# Output Configuration
OUTPUT_CONFIG = {
    'min_score_for_output': 6.0,   # Minimum score to include in results
    'top_results_count': 50,       # Number of top results to highlight
    'csv_separator': ';',          # CSV file separator
    'include_debug_info': True,    # Include debugging information
    'generate_summary_report': True
}

# Geographic Bounds for Canton Zurich (CH1903+ / LV95 coordinates)
ZURICH_BOUNDS = {
    'min_x': 2485000,
    'min_y': 1075000,
    'max_x': 2825000,
    'max_y': 1295000,
    'bbox_string': "2485000,1075000,2825000,1295000"
}

# Database Configuration
DATABASE_CONFIG = {
    'cache_db_name': 'property_cache.db',
    'enable_caching': True,
    'cache_cleanup_days': 30
}

# Logging Configuration
LOGGING_CONFIG = {
    'log_level': 'INFO',
    'log_file': 'zurich_scraper.log',
    'max_log_size_mb': 10,
    'backup_count': 5
}

# User Agent Strings for Web Scraping
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
]

# Selenium Configuration
SELENIUM_CONFIG = {
    'headless': True,
    'window_size': (1920, 1080),
    'page_load_timeout': 30,
    'implicit_wait': 10
}

# Validation Rules
VALIDATION_RULES = {
    'min_zip_code': 8000,
    'max_zip_code': 8099,
    'min_building_area': 1200,
    'max_building_area': 2500,
    'max_construction_year': 1980,
    'max_score': 10.0,
    'min_score': 0.0
}
