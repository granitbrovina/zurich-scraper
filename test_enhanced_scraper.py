#!/usr/bin/env python3
"""
Test script for Enhanced Zurich Real Estate Investment Scraper
============================================================

This script tests the core functionality of the enhanced scraper
with sample data to verify all components work correctly.
"""

import sys
import logging
from datetime import datetime

# Test imports
try:
    from modules.api_client import PropertyDataEnricher
    from modules.filters import ComprehensiveFilter
    from modules.web_scrapers import GEAKEnergyScrapingTBD
    from config import LOCATION_FILTERS, SCORING_WEIGHTS
    print("✅ All modules imported successfully")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

def test_property_data_structure():
    """Test PropertyData class"""
    print("\n🧪 Testing PropertyData structure...")
    
    from zurich_investment_scraper import PropertyData
    
    # Test with sample data
    sample_data = {
        'address': 'Bahnhofstrasse 123, 8001 Zürich',
        'zip_code': '8001',
        'building_area': 1500,
        'construction_year': 1970,
        'num_apartments': 10,
        'energy_rating': 'F'
    }
    
    prop = PropertyData(sample_data)
    assert prop.address == 'Bahnhofstrasse 123, 8001 Zürich'
    assert prop.building_area == 1500
    assert prop.energy_rating == 'F'
    
    print("   ✅ PropertyData creation and attribute access")
    
    # Test to_dict conversion
    prop_dict = prop.to_dict()
    assert isinstance(prop_dict, dict)
    assert 'address' in prop_dict
    
    print("   ✅ PropertyData to_dict conversion")

def test_location_filters():
    """Test location filtering logic"""
    print("\n🧪 Testing location filters...")
    
    from modules.filters import LocationFilter
    
    # Test passing property
    good_property = {
        'zip_code': '8001',
        'building_area': 1500,
        'construction_year': 1975
    }
    
    result = LocationFilter.apply_location_filters(good_property)
    assert result.passed == True
    print("   ✅ Property passing all location filters")
    
    # Test failing property (wrong ZIP)
    bad_zip_property = {
        'zip_code': '9000',  # Outside target range
        'building_area': 1500,
        'construction_year': 1975
    }
    
    result = LocationFilter.apply_location_filters(bad_zip_property)
    assert result.passed == False
    assert 'ZIP code' in str(result.red_flags)
    print("   ✅ Property failing ZIP code filter")
    
    # Test failing property (too new)
    new_property = {
        'zip_code': '8001',
        'building_area': 1500,
        'construction_year': 1990  # Too new
    }
    
    result = LocationFilter.apply_location_filters(new_property)
    assert result.passed == False
    print("   ✅ Property failing construction year filter")

def test_scoring_system():
    """Test the comprehensive scoring system"""
    print("\n🧪 Testing scoring system...")
    
    from modules.filters import ComprehensiveFilter
    
    filter_system = ComprehensiveFilter()
    
    # Test high-scoring property
    high_score_property = {
        'zip_code': '8001',
        'building_area': 1500,
        'construction_year': 1960,  # Old building
        'energy_rating': 'F',  # Poor energy rating
        'recent_renovations': False,  # No recent renovations
        'heating_system': 'oil',  # Old heating system
        'rent_per_sqm': 20,  # Low rent
        'market_rent_per_sqm': 30,  # Market rent higher
        'owner_type': 'Stiftung',  # Institutional owner
        'num_apartments': 8,
        'heritage_protection': False,
        'fire_safety_compliant': False
    }
    
    score, analysis, passes = filter_system.evaluate_property(high_score_property)
    assert passes == True
    assert score >= 6.0  # Should be a good investment opportunity
    assert 'energy rating' in analysis.lower() or 'poor' in analysis.lower()
    
    print(f"   ✅ High-opportunity property scored {score:.1f}")
    print(f"      Analysis: {analysis[:80]}...")

def test_api_client():
    """Test API client functionality"""
    print("\n🧪 Testing API client...")
    
    from modules.api_client import SwissGeoAPIClient
    
    client = SwissGeoAPIClient()
    
    # Test cache database initialization
    assert hasattr(client, 'init_cache_db')
    client.init_cache_db()  # Should not raise errors
    
    print("   ✅ API client initialization")
    print("   ⚠️ Full API testing requires internet connection")

def test_configuration():
    """Test configuration loading"""
    print("\n🧪 Testing configuration...")
    
    # Test that all required config sections exist
    assert 'zip_code_range' in LOCATION_FILTERS
    assert 'energy_rating_poor' in SCORING_WEIGHTS
    
    # Test value types
    assert isinstance(LOCATION_FILTERS['zip_code_range'], tuple)
    assert isinstance(SCORING_WEIGHTS['energy_rating_poor'], int)
    
    print("   ✅ Configuration structure and types")

def test_web_scrapers():
    """Test web scraper initialization"""
    print("\n🧪 Testing web scrapers...")
    
    # Test scraper initialization
    energy_scraper = GEAKEnergyScrapingTBD()
    assert hasattr(energy_scraper, 'get_energy_certificate')
    
    # Test with sample data (should not crash)
    result = energy_scraper.get_energy_certificate("Test Address", "123456")
    assert isinstance(result, dict)
    
    print("   ✅ Web scraper initialization and basic functionality")

def run_integration_test():
    """Run a simplified end-to-end test"""
    print("\n🧪 Running integration test...")
    
    from zurich_investment_scraper import ZurichRealEstateScraper
    
    # Create scraper instance
    scraper = ZurichRealEstateScraper()
    
    # Test with sample building data
    sample_building = {
        'egid': '123456',
        'address': 'Teststrasse 1, 8001 Zürich',
        'zip_code': '8001',
        'building_area': 1500,
        'construction_year': 1970,
        'num_apartments': 8,
        'building_category': 'residential'
    }
    
    # Test property enrichment (will use mock data)
    enriched_property = scraper.enrich_property_data(sample_building)
    assert enriched_property is not None
    assert enriched_property.address != ""
    
    print("   ✅ Property data enrichment")
    
    # Test scoring
    score, analysis, passes = scraper.filter_system.evaluate_property(
        enriched_property.to_dict()
    )
    assert isinstance(score, (int, float))
    assert isinstance(analysis, str)
    assert isinstance(passes, bool)
    
    print(f"   ✅ Property scoring: {score:.1f} ({'PASS' if passes else 'FAIL'})")

def main():
    """Run all tests"""
    print("🧪" + "=" * 60 + "🧪")
    print("    ENHANCED ZURICH SCRAPER - FUNCTIONALITY TEST")
    print("🧪" + "=" * 60 + "🧪")
    
    start_time = datetime.now()
    
    try:
        test_property_data_structure()
        test_location_filters()
        test_scoring_system()
        test_api_client()
        test_configuration()
        test_web_scrapers()
        run_integration_test()
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        print("\n🎉" + "=" * 60 + "🎉")
        print("              ALL TESTS PASSED!")
        print("🎉" + "=" * 60 + "🎉")
        print(f"\n✅ Test Duration: {duration:.2f} seconds")
        print("✅ Enhanced scraper is ready for production use!")
        print("\n🚀 Run 'python zurich_investment_scraper.py' to start analysis")
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 UNEXPECTED ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
