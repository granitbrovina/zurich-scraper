#!/usr/bin/env python3
"""
Comprehensive Zurich Real Estate Investment Opportunity Scraper
================================================================

This script implements an advanced web scraping and analysis system to identify
the most profitable real estate investment opportunities in Canton Zurich, Switzerland.

The system uses multiple data sources and sophisticated scoring algorithms to evaluate
properties based on:
- Location and zoning potential (ZIP 8000-8099, 1200-2500m², ≤1980)
- Building condition and renovation needs (energy rating, permits, heating, fire safety)
- Economic performance indicators (rent analysis, vacancy, value ratios)
- Ownership patterns and transaction signals (ownership changes, institutional owners)

NEW FEATURES:
- Advanced scoring system with weighted points (+3 for poor energy rating, etc.)
- Comprehensive filtering pipeline with mandatory location filters
- Multi-source data integration (geo.admin.ch, maps.zh.ch, rental platforms)
- Sophisticated opportunity detection (renovation pressure, zoning potential)

Author: Real Estate Investment Analysis Tool
Version: 3.0 - Enhanced with Advanced Filtering & Scoring
"""

import pandas as pd
import logging
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional
from pathlib import Path

# Import our custom modules
from modules.api_client import PropertyDataEnricher
from modules.filters import ComprehensiveFilter
from modules.web_scrapers import (
    GEAKEnergyScrapingTBD, BuildingPermitScraper, RentalMarketScraper,
    OwnershipDataScraper, FireSafetyComplianceChecker, ZoningDataScraper
)
from config import (
    LOCATION_FILTERS, SCRAPING_CONFIG, OUTPUT_CONFIG, 
    LOGGING_CONFIG, VALIDATION_RULES
)

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOGGING_CONFIG['log_level']),
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOGGING_CONFIG['log_file']),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class PropertyData:
    """
    Enhanced data structure for comprehensive property analysis
    """
    
    def __init__(self, data_dict: Dict = None):
        if data_dict is None:
            data_dict = {}
        
        # Basic property information
        self.address = data_dict.get('address', '')
        self.zip_code = str(data_dict.get('zip_code', ''))
        self.egid = str(data_dict.get('egid', ''))
        self.building_area = float(data_dict.get('building_area', 0) or 0)
        self.construction_year = int(data_dict.get('construction_year', 0) or 0)
        self.num_floors = int(data_dict.get('num_floors', 0) or 0)
        self.num_apartments = int(data_dict.get('num_apartments', 0) or 0)
        
        # Zoning and regulatory
        self.bauzonen = data_dict.get('bauzonen', '')
        self.max_floors_allowed = int(data_dict.get('max_floors_allowed', 0) or 0)
        self.zoning_utilization_factor = float(data_dict.get('zoning_utilization_factor', 0) or 0)
        self.heritage_protection = data_dict.get('heritage_protection', False)
        
        # Building condition indicators
        self.energy_rating = data_dict.get('energy_rating', 'Unknown')
        self.heating_system = data_dict.get('heating_system', 'Unknown')
        self.recent_renovations = data_dict.get('recent_renovations', False)
        self.last_renovation_year = int(data_dict.get('last_renovation_year', 0) or 0)
        self.fire_safety_compliant = data_dict.get('fire_safety_compliant', True)
        
        # Economic indicators
        self.rent_per_sqm = float(data_dict.get('rent_per_sqm', 0) or 0)
        self.market_rent_per_sqm = float(data_dict.get('market_rent_per_sqm', 0) or 0)
        self.days_on_market = int(data_dict.get('days_on_market', 0) or 0)
        self.tax_value = float(data_dict.get('tax_value', 0) or 0)
        self.market_value = float(data_dict.get('market_value', 0) or 0)
        self.photos_available = data_dict.get('photos_available', True)
        
        # Ownership signals
        self.ownership_changes_10_years = int(data_dict.get('ownership_changes_10_years', 0) or 0)
        self.owner_type = data_dict.get('owner_type', 'Unknown')
        self.mortgage_status = data_dict.get('mortgage_status', 'Unknown')
        
        # Derived metrics
        self.avg_unit_size = float(data_dict.get('avg_unit_size', 0) or 0)
        if self.avg_unit_size == 0 and self.num_apartments > 0 and self.building_area > 0:
            self.avg_unit_size = self.building_area / self.num_apartments
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for processing"""
        return {
            'address': self.address,
            'zip_code': self.zip_code,
            'egid': self.egid,
            'building_area': self.building_area,
            'construction_year': self.construction_year,
            'num_floors': self.num_floors,
            'num_apartments': self.num_apartments,
            'bauzonen': self.bauzonen,
            'max_floors_allowed': self.max_floors_allowed,
            'zoning_utilization_factor': self.zoning_utilization_factor,
            'heritage_protection': self.heritage_protection,
            'energy_rating': self.energy_rating,
            'heating_system': self.heating_system,
            'recent_renovations': self.recent_renovations,
            'last_renovation_year': self.last_renovation_year,
            'fire_safety_compliant': self.fire_safety_compliant,
            'rent_per_sqm': self.rent_per_sqm,
            'market_rent_per_sqm': self.market_rent_per_sqm,
            'days_on_market': self.days_on_market,
            'tax_value': self.tax_value,
            'market_value': self.market_value,
            'photos_available': self.photos_available,
            'ownership_changes_10_years': self.ownership_changes_10_years,
            'owner_type': self.owner_type,
            'mortgage_status': self.mortgage_status,
            'avg_unit_size': self.avg_unit_size
        }

class ZurichRealEstateScraper:
    """
    Enhanced main scraper class implementing the new filtering and scoring methodology
    """
    
    def __init__(self):
        # Initialize core components
        self.data_enricher = PropertyDataEnricher()
        self.filter_system = ComprehensiveFilter()
        
        # Initialize specialized scrapers
        self.energy_scraper = GEAKEnergyScrapingTBD()
        self.permit_scraper = BuildingPermitScraper()
        self.rental_scraper = RentalMarketScraper()
        self.ownership_scraper = OwnershipDataScraper()
        self.fire_safety_checker = FireSafetyComplianceChecker()
        self.zoning_scraper = ZoningDataScraper()
        
        # Results storage
        self.properties = []
        self.results = []
        
        logger.info("Enhanced Zurich Real Estate Scraper initialized")
        
    def fetch_building_data(self, limit: int = None) -> List[Dict]:
        """
        Fetch building data from Swiss Federal Building Register
        """
        if limit is None:
            limit = SCRAPING_CONFIG['max_properties_per_run']
        
        logger.info(f"Fetching building data for Canton Zurich (limit: {limit})")
        
        # Use the API client to get building data
        buildings = self.data_enricher.geo_client.fetch_building_register_data(limit)
        
        # Filter for residential buildings only
        residential_buildings = []
        for building in buildings:
            building_category = building.get('building_category', '').lower()
            if any(res_type in building_category for res_type in ['residential', 'wohnen', 'residential']):
                residential_buildings.append(building)
        
        logger.info(f"Found {len(residential_buildings)} residential buildings")
        return residential_buildings

    def enrich_property_data(self, basic_property: Dict) -> PropertyData:
        """
        Enrich a single property with comprehensive data from all sources
        """
        try:
            # Start with basic property data
            enriched_data = basic_property.copy()
            
            # Enrich with API data
            api_enriched = self.data_enricher.enrich_property_data(basic_property)
            enriched_data.update(api_enriched)
            
            # Get energy certificate data
            energy_data = self.energy_scraper.get_energy_certificate(
                enriched_data.get('address', ''),
                enriched_data.get('egid', '')
            )
            enriched_data.update(energy_data)
            
            # Get renovation/permit history
            permit_data = self.permit_scraper.get_renovation_history(
                enriched_data.get('address', ''),
                enriched_data.get('egid', '')
            )
            enriched_data.update(permit_data)
            
            # Get fire safety compliance
            fire_safety_data = self.fire_safety_checker.check_fire_safety_compliance(
                enriched_data.get('address', ''),
                enriched_data.get('construction_year', 0)
            )
            enriched_data.update(fire_safety_data)
            
            # Get rental market data
            rental_data = self.rental_scraper.get_rental_market_data(
                enriched_data.get('address', ''),
                enriched_data.get('zip_code', ''),
                enriched_data.get('building_area', 0)
            )
            enriched_data.update(rental_data)
            
            # Get ownership data
            ownership_data = self.ownership_scraper.get_ownership_data(
                enriched_data.get('address', '')
            )
            enriched_data.update(ownership_data)
            
            # Calculate zoning potential if coordinates available
            coordinates = enriched_data.get('coordinates')
            if coordinates and len(coordinates) == 2:
                zoning_potential = self.zoning_scraper.get_zoning_potential(
                    tuple(coordinates),
                    enriched_data.get('num_floors', 0),
                    enriched_data.get('building_area', 0)
                )
                enriched_data.update(zoning_potential)
            
            return PropertyData(enriched_data)
            
        except Exception as e:
            logger.error(f"Error enriching property data: {e}")
            return PropertyData(basic_property)

    def process_properties(self, buildings: List[Dict]) -> List[Dict]:
        """
        Process a list of buildings through the complete analysis pipeline
        """
        logger.info(f"Processing {len(buildings)} buildings through analysis pipeline")
        
        results = []
        
        # Use ThreadPoolExecutor for concurrent processing
        with ThreadPoolExecutor(max_workers=SCRAPING_CONFIG['max_concurrent_threads']) as executor:
            # Submit all property enrichment tasks
            future_to_building = {
                executor.submit(self.enrich_property_data, building): building 
                for building in buildings
            }
            
            # Process completed tasks
            for future in as_completed(future_to_building):
                try:
                    property_data = future.result()
                    
                    # Apply comprehensive filtering and scoring
                    score, analysis, passes_filters = self.filter_system.evaluate_property(
                        property_data.to_dict()
                    )
                    
                    # Only include properties that pass filters and meet minimum score
                    if passes_filters and score >= OUTPUT_CONFIG['min_score_for_output']:
                        result = {
                            'Investment Score': round(score, 2),
                            'Address': property_data.address,
                            'ZIP Code': property_data.zip_code,
                            'Building Area (m²)': property_data.building_area,
                            'Construction Year': property_data.construction_year,
                            'Number of Floors': property_data.num_floors,
                            'Number of Apartments': property_data.num_apartments,
                            'Energy Rating': property_data.energy_rating,
                            'Heating System': property_data.heating_system,
                            'Recent Renovations': 'Yes' if property_data.recent_renovations else 'No',
                            'Zoning Potential': f"{property_data.zoning_utilization_factor*100:.0f}%" if property_data.zoning_utilization_factor > 0 else "Unknown",
                            'Rent vs Market': f"{(property_data.rent_per_sqm/property_data.market_rent_per_sqm)*100:.0f}%" if property_data.market_rent_per_sqm > 0 else "Unknown",
                            'Days on Market': property_data.days_on_market,
                            'Owner Type': property_data.owner_type,
                            'Investment Analysis': analysis,
                            'EGID': property_data.egid
                        }
                        results.append(result)
                        
                        if len(results) % 10 == 0:
                            logger.info(f"Processed {len(results)} qualifying properties")
                            
                except Exception as e:
                    logger.error(f"Error processing property: {e}")
        
        logger.info(f"Analysis complete. {len(results)} properties qualify for investment consideration")
        return results

    def run_comprehensive_analysis(self, max_properties: int = None) -> pd.DataFrame:
        """
        Run the complete enhanced analysis pipeline
        """
        logger.info("🏢 Starting ENHANCED Zurich Real Estate Investment Analysis")
        logger.info("📋 New Features:")
        logger.info("   ✅ Mandatory location filters (ZIP 8000-8099, 1200-2500m², ≤1980)")
        logger.info("   🔍 Advanced condition analysis (energy rating, renovations, heating)")
        logger.info("   💰 Economic underperformance detection (rent analysis, vacancy)")
        logger.info("   🏛️ Ownership signal analysis (institutional owners, mortgage status)")
        logger.info("   📊 Weighted scoring system (+3 poor energy, +2 zoning potential, etc.)")
        print()
        
        try:
            # Step 1: Fetch building data
            buildings = self.fetch_building_data(max_properties)
            if not buildings:
                logger.error("❌ No building data retrieved")
                return pd.DataFrame()
            
            logger.info(f"📊 Processing {len(buildings)} residential buildings through enhanced pipeline")
            
            # Step 2: Process through comprehensive analysis
            results = self.process_properties(buildings)
            
            if not results:
                logger.warning("⚠️ No properties met the investment criteria")
                return pd.DataFrame()
            
            # Step 3: Create and sort results DataFrame
            results_df = pd.DataFrame(results)
            results_df = results_df.sort_values('Investment Score', ascending=False)
            
            # Step 4: Log summary statistics
            logger.info("=" * 60)
            logger.info("🎯 ANALYSIS RESULTS SUMMARY")
            logger.info("=" * 60)
            logger.info(f"📈 Total Investment Opportunities: {len(results_df)}")
            logger.info(f"🏆 Average Investment Score: {results_df['Investment Score'].mean():.2f}")
            logger.info(f"⭐ Highest Score: {results_df['Investment Score'].max():.2f}")
            logger.info(f"📊 Score Distribution:")
            logger.info(f"   🥇 Exceptional (8.0-10.0): {len(results_df[results_df['Investment Score'] >= 8.0])}")
            logger.info(f"   🥈 Excellent (7.0-7.9): {len(results_df[(results_df['Investment Score'] >= 7.0) & (results_df['Investment Score'] < 8.0)])}")
            logger.info(f"   🥉 Good (6.0-6.9): {len(results_df[(results_df['Investment Score'] >= 6.0) & (results_df['Investment Score'] < 7.0)])}")
            
            return results_df
            
        except Exception as e:
            logger.error(f"❌ Analysis failed: {e}")
            return pd.DataFrame()

    def save_results(self, results_df: pd.DataFrame):
        """
        Save comprehensive results to CSV files with detailed reporting
        """
        if results_df.empty:
            logger.warning("⚠️ No results to save")
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save all results
        all_results_file = f"enhanced_zurich_investments_{timestamp}.csv"
        results_df.to_csv(all_results_file, index=False, sep=OUTPUT_CONFIG['csv_separator'])
        logger.info(f"💾 All results saved to: {all_results_file}")
        
        # Save top opportunities
        top_count = min(OUTPUT_CONFIG['top_results_count'], len(results_df))
        top_results = results_df.head(top_count)
        top_results_file = f"top_{top_count}_zurich_investments_{timestamp}.csv"
        top_results.to_csv(top_results_file, index=False, sep=OUTPUT_CONFIG['csv_separator'])
        logger.info(f"🏆 Top {top_count} results saved to: {top_results_file}")
        
        # Generate summary report
        if OUTPUT_CONFIG['generate_summary_report']:
            self.generate_enhanced_summary_report(results_df, f"investment_analysis_report_{timestamp}.txt")
    
    def generate_enhanced_summary_report(self, results_df: pd.DataFrame, filename: str):
        """
        Generate a comprehensive analysis report
        """
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("ENHANCED ZURICH REAL ESTATE INVESTMENT ANALYSIS REPORT\n")
            f.write("=" * 65 + "\n\n")
            
            f.write(f"📅 Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"🏢 Total Investment Opportunities Found: {len(results_df)}\n")
            f.write(f"📊 Analysis Method: Enhanced Multi-Factor Scoring System\n\n")
            
            if not results_df.empty:
                # Score statistics
                f.write("📈 INVESTMENT SCORE STATISTICS:\n")
                f.write("-" * 40 + "\n")
                f.write(f"Average Score: {results_df['Investment Score'].mean():.2f}\n")
                f.write(f"Median Score: {results_df['Investment Score'].median():.2f}\n")
                f.write(f"Highest Score: {results_df['Investment Score'].max():.2f}\n")
                f.write(f"Lowest Score: {results_df['Investment Score'].min():.2f}\n")
                f.write(f"Standard Deviation: {results_df['Investment Score'].std():.2f}\n\n")
                
                # Score distribution
                f.write("🎯 SCORE DISTRIBUTION:\n")
                f.write("-" * 40 + "\n")
                exceptional = len(results_df[results_df['Investment Score'] >= 8.0])
                excellent = len(results_df[(results_df['Investment Score'] >= 7.0) & (results_df['Investment Score'] < 8.0)])
                good = len(results_df[(results_df['Investment Score'] >= 6.0) & (results_df['Investment Score'] < 7.0)])
                
                f.write(f"🥇 Exceptional (8.0-10.0): {exceptional} properties ({exceptional/len(results_df)*100:.1f}%)\n")
                f.write(f"🥈 Excellent (7.0-7.9): {excellent} properties ({excellent/len(results_df)*100:.1f}%)\n")
                f.write(f"🥉 Good (6.0-6.9): {good} properties ({good/len(results_df)*100:.1f}%)\n\n")
                
                # Geographic distribution
                f.write("🗺️ GEOGRAPHIC DISTRIBUTION:\n")
                f.write("-" * 40 + "\n")
                zip_counts = results_df['ZIP Code'].value_counts().head(10)
                for zip_code, count in zip_counts.items():
                    f.write(f"ZIP {zip_code}: {count} properties\n")
                f.write("\n")
                
                # Construction year analysis
                f.write("🏗️ CONSTRUCTION YEAR ANALYSIS:\n")
                f.write("-" * 40 + "\n")
                pre_1950 = len(results_df[results_df['Construction Year'] < 1950])
                pre_1980 = len(results_df[(results_df['Construction Year'] >= 1950) & (results_df['Construction Year'] <= 1980)])
                f.write(f"Pre-1950 (Maximum opportunity): {pre_1950} properties\n")
                f.write(f"1950-1980 (Good opportunity): {pre_1980} properties\n\n")
                
                # Top 10 opportunities
                f.write("🏆 TOP 10 INVESTMENT OPPORTUNITIES:\n")
                f.write("-" * 60 + "\n")
                for i, (_, row) in enumerate(results_df.head(10).iterrows(), 1):
                    f.write(f"{i:2d}. Score {row['Investment Score']:.1f} | {row['Address']}\n")
                    f.write(f"    {row['Building Area (m²)']}m² | {row['Construction Year']} | {row['Number of Apartments']} units\n")
                    f.write(f"    Analysis: {row['Investment Analysis'][:100]}...\n\n")
                
                # Key investment themes
                f.write("🔍 KEY INVESTMENT THEMES IDENTIFIED:\n")
                f.write("-" * 50 + "\n")
                f.write("• Energy Efficiency Upgrades: Properties with poor GEAK ratings\n")
                f.write("• Zoning Potential: Buildings with expansion opportunities\n")
                f.write("• Rental Market Underperformance: Below-market rent properties\n")
                f.write("• Institutional Ownership: Stiftung and family-owned properties\n")
                f.write("• Fire Safety Compliance: Buildings requiring safety upgrades\n")
                f.write("• Heating System Modernization: Oil heating replacement opportunities\n\n")
        
        logger.info(f"📋 Comprehensive analysis report saved to: {filename}")



def main():
    """Enhanced main execution function with comprehensive analysis"""
    print()
    print("🏢" + "=" * 70 + "🏢")
    print("    ENHANCED ZURICH REAL ESTATE INVESTMENT SCRAPER v3.0")
    print("    Advanced Multi-Factor Investment Opportunity Analysis")
    print("🏢" + "=" * 70 + "🏢")
    print()
    print("🎯 NEW ADVANCED FEATURES:")
    print("   ✅ Mandatory Location Filters (ZIP 8000-8099, 1200-2500m², ≤1980)")
    print("   🔍 Condition-Based Analysis (energy rating, renovations, heating, fire safety)")
    print("   💰 Economic Underperformance Detection (rent analysis, vacancy, value ratios)")
    print("   🏛️ Ownership Signal Analysis (institutional owners, mortgage status)")
    print("   📊 Sophisticated Scoring System (weighted points: +3 poor energy, +2 zoning)")
    print("   🌐 Multi-Source Data Integration (APIs, web scraping, public records)")
    print()
    print("📋 ANALYSIS METHODOLOGY:")
    print("   Instead of hard filtering, properties receive distress + opportunity scores:")
    print("   • +3 GEAK rating F or G")
    print("   • +3 Rent 30% below market") 
    print("   • +2 Can increase building volume 25%+")
    print("   • +2 No renovation permits in 25 years")
    print("   • +1 Long Days-on-Market")
    print("   • +1 Owned by Stiftung")
    print("   • -3 Heritage protection")
    print("   • -2 Over 50 units (management complexity)")
    print()
    
    try:
        scraper = ZurichRealEstateScraper()
        
        # Ask user for analysis scope
        print("🔧 ANALYSIS CONFIGURATION:")
        try:
            max_properties = int(input("Enter maximum properties to analyze (default 500): ") or "500")
        except ValueError:
            max_properties = 500
            
        print(f"📊 Analyzing up to {max_properties} properties...")
        print("⏱️ This may take several minutes depending on data sources...")
        print()
        
        # Run enhanced analysis
        results = scraper.run_comprehensive_analysis(max_properties=max_properties)
        
        # Process and save results
        if not results.empty:
            scraper.save_results(results)
            
            # Display summary
            print()
            print("🎉" + "=" * 60 + "🎉")
            print("                  ANALYSIS COMPLETE!")
            print("🎉" + "=" * 60 + "🎉")
            print()
            print(f"📈 Investment Opportunities Found: {len(results)}")
            print(f"🏆 Average Investment Score: {results['Investment Score'].mean():.2f}/10")
            print(f"⭐ Highest Score: {results['Investment Score'].max():.2f}/10")
            print()
            
            # Show score distribution
            exceptional = len(results[results['Investment Score'] >= 8.0])
            excellent = len(results[(results['Investment Score'] >= 7.0) & (results['Investment Score'] < 8.0)])
            good = len(results[results['Investment Score'] >= 6.0])
            
            print("📊 INVESTMENT QUALITY DISTRIBUTION:")
            print(f"   🥇 Exceptional (8.0-10.0): {exceptional} properties")
            print(f"   🥈 Excellent (7.0-7.9): {excellent} properties") 
            print(f"   🥉 Good (6.0-6.9): {good} properties")
            print()
            
            # Show top 5 opportunities
            print("🏆 TOP 5 INVESTMENT OPPORTUNITIES:")
            print("-" * 60)
            for i, (_, row) in enumerate(results.head(5).iterrows(), 1):
                print(f"{i}. Score {row['Investment Score']:.1f} | {row['Address']}")
                print(f"   {row['Building Area (m²)']}m² | {row['Construction Year']} | {row['Number of Apartments']} units")
                analysis = row['Investment Analysis']
                if len(analysis) > 80:
                    analysis = analysis[:80] + "..."
                print(f"   💡 {analysis}")
                print()
            
            print("📁 FILES CREATED:")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            print(f"   📊 enhanced_zurich_investments_{timestamp}.csv")
            print(f"   🏆 top_50_zurich_investments_{timestamp}.csv")
            print(f"   📋 investment_analysis_report_{timestamp}.txt")
            print()
            print("✅ Analysis complete! Check the generated files for detailed results.")
            
        else:
            print()
            print("⚠️" + "=" * 60 + "⚠️")
            print("           NO INVESTMENT OPPORTUNITIES FOUND")
            print("⚠️" + "=" * 60 + "⚠️")
            print()
            print("🔍 This could mean:")
            print("   • No properties in Canton Zurich meet the strict criteria")
            print("   • API data sources are currently unavailable")
            print("   • Network connectivity issues")
            print("   • Consider adjusting the filtering criteria")
            
    except KeyboardInterrupt:
        print("\n🛑 Analysis interrupted by user")
        print("💾 Partial results may be available in log files")
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        print(f"\n❌ ANALYSIS FAILED: {e}")
        print("📋 Check the log file 'zurich_scraper.log' for detailed error information")
        print("🔧 Common issues:")
        print("   • Internet connection problems")
        print("   • API rate limiting")
        print("   • Missing dependencies")

if __name__ == "__main__":
    main()
