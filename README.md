# Enhanced Zurich Real Estate Investment Scraper v3.0

## 🏢 Advanced Multi-Factor Investment Opportunity Analysis

This enhanced version implements sophisticated filtering and scoring algorithms to identify the most profitable real estate investment opportunities in Canton Zurich, Switzerland, based on your specific requirements.

## 🎯 New Advanced Features

### ✅ Mandatory Location Filters
- **ZIP Code Range**: 8000-8099 (Central Zurich)
- **Building Area**: 1,200-2,500 m²
- **Construction Year**: ≤ 1980 (older buildings for redevelopment potential)

### 🔍 Condition-Based Analysis
- **Energy Rating**: GEAK certificate analysis (E, F, G ratings = renovation pressure)
- **Renovation History**: Building permit database scraping (no major works in 20+ years)
- **Heating Systems**: Oil heating or outdated systems detection
- **Fire Safety**: Compliance analysis for older buildings

### 💰 Economic Underperformance Detection
- **Rent Analysis**: Rent >30% below market rate
- **Vacancy Indicators**: Listings >120 days on market
- **Value Ratios**: Tax value vs market value analysis
- **Presentation Quality**: Poor/missing photos indicating unrenovated units

### 🏛️ Ownership Signal Analysis
- **Ownership Changes**: 2+ sales in last 10 years
- **Owner Types**: Stiftung (foundations) and family ownership
- **Mortgage Status**: Unencumbered properties
- **Zoning Potential**: 30%+ building volume expansion possible

### 📊 Sophisticated Scoring System

Instead of hard filtering, properties receive weighted distress + opportunity scores:

| Factor | Points | Description |
|--------|--------|-------------|
| **GEAK rating F or G** | +3 | Energy renovation pressure |
| **Rent 30% below market** | +3 | Immediate rental income opportunity |
| **Zoning expansion 25%+** | +2 | Development rights value |
| **No renovations 25+ years** | +2 | Structural renovation pressure |
| **Long Days-on-Market** | +1 | Motivated seller indication |
| **Stiftung ownership** | +1 | Institutional seller flexibility |
| **Heritage protection** | -3 | Development restrictions |
| **50+ units** | -2 | Management complexity |

## 🏗️ System Architecture

```
zurich_investment_scraper.py     # Main orchestration script
├── modules/
│   ├── api_client.py           # Swiss government API integration
│   ├── web_scrapers.py         # Rental platforms & data scrapers
│   └── filters.py              # Advanced filtering & scoring logic
├── config.py                   # Configuration & scoring weights
└── requirements.txt            # Dependencies
```

## 🚀 Installation & Usage

### Prerequisites
```bash
pip install -r requirements.txt
```

### Running the Analysis
```bash
python zurich_investment_scraper.py
```

The system will prompt you for:
- Maximum number of properties to analyze (default: 500)

## 📊 Data Sources Integration

### Government APIs
- **geo.admin.ch**: Federal building register
- **maps.zh.ch**: Canton Zurich zoning data
- **Building permits**: Renovation history

### Real Estate Platforms
- **Comparis**: Rental market analysis
- **Homegate**: Property listings and market data
- **ImmoScout24**: Additional market intelligence

### Public Records
- **GEAK Database**: Energy certificates
- **Grundbuch**: Ownership records (where accessible)

## 📈 Output Files

The system generates comprehensive reports:

1. **`enhanced_zurich_investments_[timestamp].csv`**
   - All qualifying investment opportunities
   - Detailed scoring breakdown
   - Property characteristics

2. **`top_50_zurich_investments_[timestamp].csv`**
   - Top 50 highest-scoring opportunities
   - Priority investment targets

3. **`investment_analysis_report_[timestamp].txt`**
   - Comprehensive analysis summary
   - Score distribution statistics
   - Geographic and temporal trends
   - Key investment themes

## 🔧 Configuration

Modify `config.py` to adjust:

### Scoring Weights
```python
SCORING_WEIGHTS = {
    'energy_rating_poor': 3,
    'rent_below_market': 3,
    'zoning_potential': 2,
    # ... customize scoring
}
```

### Location Filters
```python
LOCATION_FILTERS = {
    'zip_code_range': (8000, 8099),
    'building_area_range': (1200, 2500),
    'max_construction_year': 1980
}
```

### API Rate Limiting
```python
SCRAPING_CONFIG = {
    'request_delay': 0.1,
    'max_concurrent_threads': 5,
    'timeout_seconds': 10
}
```

## 📋 Sample Output

```
🏆 TOP 5 INVESTMENT OPPORTUNITIES:
────────────────────────────────────────────────────────
1. Score 9.2 | Bahnhofstrasse 123, 8001 Zürich
   1,800m² | 1965 | 12 units
   💡 Poor energy rating (F), Rent 35% below market, Zoning expansion potential...

2. Score 8.9 | Seestrasse 456, 8002 Zürich  
   2,200m² | 1972 | 8 units
   💡 Stiftung ownership, No renovations 30 years, Oil heating system...
```

## 🎯 Investment Strategy Integration

The scoring system identifies properties with multiple "distress signals" that create:

1. **Negotiation Leverage**: Renovation pressure, poor presentation
2. **Value-Add Opportunities**: Energy upgrades, layout optimization  
3. **Market Inefficiencies**: Below-market rents, zoning underutilization
4. **Transaction Advantages**: Motivated sellers, unencumbered properties

## ⚠️ Important Notes

### Data Accuracy
- Government APIs provide official building data
- Market data is aggregated from multiple sources
- Some data sources require specific API access

### Legal Compliance
- Respects rate limits and terms of service
- Uses only publicly available data
- Caches responses to minimize API calls

### Limitations
- GEAK certificate access may be limited
- Grundbuch data requires authorized access
- Market rental data depends on platform availability

## 🔍 Troubleshooting

### Common Issues
1. **No results found**: Adjust filtering criteria in `config.py`
2. **API timeouts**: Check internet connection and reduce `max_concurrent_threads`
3. **Missing dependencies**: Run `pip install -r requirements.txt`

### Log Files
Check `zurich_scraper.log` for detailed execution information and error diagnostics.

## 📞 Support

For technical issues or feature requests:
- Review the log files for specific error messages
- Verify API connectivity and rate limits
- Check configuration parameters in `config.py`

---

**Version**: 3.0 - Enhanced Multi-Factor Analysis  
**Target**: Zurich Canton Real Estate Investment Opportunities  
**Methodology**: Weighted Distress + Opportunity Scoring
