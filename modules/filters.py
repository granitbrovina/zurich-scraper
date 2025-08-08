#!/usr/bin/env python3
"""
Advanced Filtering System for Real Estate Investment Analysis
============================================================

This module implements sophisticated filtering logic for identifying
investment opportunities based on location, condition, economic performance,
and ownership signals.
"""

import logging
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import re

from config import (
    LOCATION_FILTERS, CONDITION_CRITERIA, ECONOMIC_THRESHOLDS,
    OWNERSHIP_SIGNALS, SCORING_WEIGHTS, SIZE_PREFERENCES, AGE_SCORING
)

logger = logging.getLogger(__name__)

@dataclass
class FilterResult:
    """Result of applying filters to a property"""
    passed: bool
    score: float
    reasons: List[str]
    red_flags: List[str]
    opportunities: List[str]

class LocationFilter:
    """
    A. Mandatory Location Filters
    These are hard filters - properties must pass ALL to be considered
    """
    
    @staticmethod
    def apply_location_filters(property_data: Dict) -> FilterResult:
        """
        Apply mandatory location-based filters
        
        Returns:
            FilterResult with pass/fail and reasoning
        """
        reasons = []
        red_flags = []
        
        # ZIP Code Filter (8000-8099)
        zip_code = LocationFilter._extract_zip_code(property_data.get('zip_code', ''))
        if not zip_code or not (LOCATION_FILTERS['zip_code_range'][0] <= zip_code <= LOCATION_FILTERS['zip_code_range'][1]):
            red_flags.append(f"ZIP code {zip_code} outside target range {LOCATION_FILTERS['zip_code_range']}")
            return FilterResult(False, 0.0, reasons, red_flags, [])
        else:
            reasons.append(f"Prime Zurich location (ZIP {zip_code})")
        
        # Building Area Filter (1,200-2,500 m²)
        building_area = float(property_data.get('building_area', 0))
        if not (LOCATION_FILTERS['building_area_range'][0] <= building_area <= LOCATION_FILTERS['building_area_range'][1]):
            red_flags.append(f"Building area {building_area}m² outside target range {LOCATION_FILTERS['building_area_range']}")
            return FilterResult(False, 0.0, reasons, red_flags, [])
        else:
            reasons.append(f"Optimal building size ({building_area}m²)")
        
        # Construction Year Filter (≤1980)
        construction_year = int(property_data.get('construction_year', 0))
        if construction_year == 0 or construction_year > LOCATION_FILTERS['max_construction_year']:
            red_flags.append(f"Construction year {construction_year} too recent (after {LOCATION_FILTERS['max_construction_year']})")
            return FilterResult(False, 0.0, reasons, red_flags, [])
        else:
            age_category = "very old" if construction_year < AGE_SCORING['very_old_threshold'] else "old"
            reasons.append(f"{age_category.title()} building ({construction_year}) - renovation opportunity")
        
        return FilterResult(True, 1.0, reasons, red_flags, [])
    
    @staticmethod
    def _extract_zip_code(zip_string: str) -> Optional[int]:
        """Extract ZIP code number from string"""
        try:
            # Extract 4-digit number from ZIP string
            match = re.search(r'\b(\d{4})\b', str(zip_string))
            if match:
                return int(match.group(1))
        except (ValueError, AttributeError):
            pass
        return None

class ConditionFilter:
    """
    B. Condition-Based Filters
    Identify properties with renovation pressure (scoring, not elimination)
    """
    
    @staticmethod
    def analyze_building_condition(property_data: Dict) -> FilterResult:
        """
        Analyze building condition indicators for investment potential
        """
        score = 0.0
        reasons = []
        opportunities = []
        
        # Energy Rating Analysis
        energy_rating = property_data.get('energy_rating', '').upper()
        if energy_rating in CONDITION_CRITERIA['target_energy_ratings']:
            points = SCORING_WEIGHTS['energy_rating_poor']
            score += points
            reasons.append(f"Poor energy rating ({energy_rating}) - renovation pressure")
            opportunities.append(f"Energy efficiency upgrade potential (+{points} points)")
        
        # Renovation History Analysis
        recent_renovations = property_data.get('recent_renovations', False)
        if not recent_renovations:
            points = SCORING_WEIGHTS['no_recent_renovations']
            score += points
            reasons.append("No recent major renovations")
            opportunities.append(f"Full renovation potential (+{points} points)")
        
        # Check years since last renovation
        last_renovation_year = property_data.get('last_renovation_year', 0)
        current_year = datetime.now().year
        if last_renovation_year > 0 and (current_year - last_renovation_year) > CONDITION_CRITERIA['max_years_since_renovation']:
            score += 1
            reasons.append(f"Last renovation {current_year - last_renovation_year} years ago")
            opportunities.append("Modernization needed - negotiation leverage")
        
        # Heating System Analysis
        heating_system = property_data.get('heating_system', '').lower()
        if heating_system in CONDITION_CRITERIA['problematic_heating_systems']:
            points = SCORING_WEIGHTS['old_heating_system']
            score += points
            reasons.append(f"Outdated heating system ({heating_system})")
            opportunities.append(f"Heating system upgrade required (+{points} points)")
        
        # Fire Safety Compliance
        fire_safety_compliant = property_data.get('fire_safety_compliant', True)
        if not fire_safety_compliant:
            points = SCORING_WEIGHTS['fire_safety_issues']
            score += points
            reasons.append("Fire safety compliance issues")
            opportunities.append(f"Safety upgrades required - renovation pressure (+{points} points)")
        
        return FilterResult(True, score, reasons, [], opportunities)

class EconomicFilter:
    """
    C. Economic Underperformance Filters
    Identify properties with economic distress signals
    """
    
    @staticmethod
    def analyze_economic_performance(property_data: Dict) -> FilterResult:
        """
        Analyze economic underperformance indicators
        """
        score = 0.0
        reasons = []
        opportunities = []
        red_flags = []
        
        # Rent Analysis
        current_rent = float(property_data.get('rent_per_sqm', 0))
        market_rent = float(property_data.get('market_rent_per_sqm', 0))
        
        if current_rent > 0 and market_rent > 0:
            rent_ratio = current_rent / market_rent
            if rent_ratio < ECONOMIC_THRESHOLDS['rent_below_market_threshold']:
                points = SCORING_WEIGHTS['rent_below_market']
                score += points
                below_market_pct = (1 - rent_ratio) * 100
                reasons.append(f"Rent {below_market_pct:.0f}% below market")
                opportunities.append(f"Immediate rent increase potential (+{points} points)")
        
        # Vacancy / Days on Market Analysis
        days_on_market = int(property_data.get('days_on_market', 0))
        if days_on_market > ECONOMIC_THRESHOLDS['high_vacancy_days']:
            points = SCORING_WEIGHTS['high_vacancy']
            score += points
            reasons.append(f"Long time on market ({days_on_market} days)")
            opportunities.append(f"Motivated seller potential (+{points} points)")
        
        # Value vs Tax Assessment Analysis
        market_value = float(property_data.get('market_value', 0))
        tax_value = float(property_data.get('tax_value', 0))
        
        if market_value > 0 and tax_value > 0:
            value_ratio = tax_value / market_value
            if value_ratio < ECONOMIC_THRESHOLDS['low_tax_value_ratio']:
                points = SCORING_WEIGHTS['low_value_ratio']
                score += points
                reasons.append(f"Tax value significantly below market estimate")
                opportunities.append(f"Potential undervaluation (+{points} points)")
        
        # Presentation Quality Analysis
        photos_available = property_data.get('photos_available', True)
        photo_quality = property_data.get('photo_quality_score', 5)
        
        if not photos_available or photo_quality < ECONOMIC_THRESHOLDS['photo_quality_threshold']:
            points = SCORING_WEIGHTS['poor_presentation']
            score += points
            reasons.append("Poor online presentation")
            opportunities.append(f"Marketing improvement potential (+{points} points)")
        
        return FilterResult(True, score, reasons, red_flags, opportunities)

class OwnershipFilter:
    """
    D. Ownership / Transaction Signal Analysis
    Identify ownership patterns that suggest investment opportunities
    """
    
    @staticmethod
    def analyze_ownership_signals(property_data: Dict) -> FilterResult:
        """
        Analyze ownership and transaction patterns
        """
        score = 0.0
        reasons = []
        opportunities = []
        
        # Ownership Change Frequency
        ownership_changes = int(property_data.get('ownership_changes_10_years', 0))
        if ownership_changes >= OWNERSHIP_SIGNALS['frequent_ownership_changes']:
            points = SCORING_WEIGHTS['frequent_changes']
            score += points
            reasons.append(f"Frequent ownership changes ({ownership_changes} in 10 years)")
            opportunities.append(f"Potential distress sale (+{points} points)")
        
        # Owner Type Analysis
        owner_type = property_data.get('owner_type', '').lower()
        if any(target_type.lower() in owner_type for target_type in OWNERSHIP_SIGNALS['target_owner_types']):
            points = SCORING_WEIGHTS['institutional_owner']
            score += points
            reasons.append(f"Owner type: {owner_type}")
            opportunities.append(f"Institutional/family seller - potentially negotiable (+{points} points)")
        
        # Mortgage Status
        mortgage_status = property_data.get('mortgage_status', '').lower()
        if any(indicator in mortgage_status for indicator in OWNERSHIP_SIGNALS['mortgage_free_indicators']):
            points = SCORING_WEIGHTS['no_mortgage']
            score += points
            reasons.append("Unencumbered property")
            opportunities.append(f"Fast transaction potential (+{points} points)")
        
        # Zoning Utilization Analysis
        zoning_utilization = float(property_data.get('zoning_utilization_factor', 0))
        if zoning_utilization >= OWNERSHIP_SIGNALS['zoning_underutilization_threshold']:
            points = SCORING_WEIGHTS['zoning_potential']
            score += points
            potential_pct = zoning_utilization * 100
            reasons.append(f"Zoning underutilization ({potential_pct:.0f}% expansion potential)")
            opportunities.append(f"Development rights value (+{points} points)")
        
        # Layout Analysis
        avg_unit_size = float(property_data.get('avg_unit_size', 50))
        if avg_unit_size < OWNERSHIP_SIGNALS['small_unit_threshold']:
            points = SCORING_WEIGHTS['small_units']
            score += points
            reasons.append(f"Small average unit size ({avg_unit_size}m²)")
            opportunities.append(f"Reconfiguration potential (+{points} points)")
        
        return FilterResult(True, score, reasons, [], opportunities)

class NegativeFactorFilter:
    """
    Identify negative factors that reduce investment attractiveness
    """
    
    @staticmethod
    def analyze_negative_factors(property_data: Dict) -> FilterResult:
        """
        Analyze factors that negatively impact investment potential
        """
        score = 0.0
        reasons = []
        red_flags = []
        
        # Heritage Protection
        heritage_protection = property_data.get('heritage_protection', False)
        if heritage_protection:
            points = SCORING_WEIGHTS['heritage_protection']  # Negative
            score += points
            red_flags.append("Heritage protection restrictions")
            reasons.append(f"Limited renovation options ({abs(points)} point penalty)")
        
        # Unit Count Analysis
        num_apartments = int(property_data.get('num_apartments', 0))
        if num_apartments > 50:
            points = SCORING_WEIGHTS['too_many_units']  # Negative
            score += points
            red_flags.append(f"High unit count ({num_apartments} apartments)")
            reasons.append(f"Management complexity ({abs(points)} point penalty)")
        
        # Recent Renovation Penalty
        recent_renovations = property_data.get('recent_renovations', False)
        recent_renovation_year = property_data.get('last_renovation_year', 0)
        current_year = datetime.now().year
        
        if recent_renovations or (recent_renovation_year > 0 and (current_year - recent_renovation_year) < 5):
            points = SCORING_WEIGHTS['recent_renovation']  # Negative
            score += points
            reasons.append("Recently renovated - limited improvement potential")
        
        return FilterResult(True, score, reasons, red_flags, [])

class ComprehensiveFilter:
    """
    Master filter that combines all filtering logic
    """
    
    def __init__(self):
        self.location_filter = LocationFilter()
        self.condition_filter = ConditionFilter()
        self.economic_filter = EconomicFilter()
        self.ownership_filter = OwnershipFilter()
        self.negative_filter = NegativeFactorFilter()
    
    def evaluate_property(self, property_data: Dict) -> Tuple[float, str, bool]:
        """
        Comprehensive evaluation of a property
        
        Returns:
            Tuple of (score, analysis_description, passes_filters)
        """
        try:
            # Step 1: Apply mandatory location filters
            location_result = LocationFilter.apply_location_filters(property_data)
            if not location_result.passed:
                return 0.0, f"Failed location filters: {'; '.join(location_result.red_flags)}", False
            
            total_score = 0.0
            all_reasons = []
            all_opportunities = []
            all_red_flags = []
            
            # Step 2: Condition analysis
            condition_result = ConditionFilter.analyze_building_condition(property_data)
            total_score += condition_result.score
            all_reasons.extend(condition_result.reasons)
            all_opportunities.extend(condition_result.opportunities)
            
            # Step 3: Economic analysis
            economic_result = EconomicFilter.analyze_economic_performance(property_data)
            total_score += economic_result.score
            all_reasons.extend(economic_result.reasons)
            all_opportunities.extend(economic_result.opportunities)
            all_red_flags.extend(economic_result.red_flags)
            
            # Step 4: Ownership analysis
            ownership_result = OwnershipFilter.analyze_ownership_signals(property_data)
            total_score += ownership_result.score
            all_reasons.extend(ownership_result.reasons)
            all_opportunities.extend(ownership_result.opportunities)
            
            # Step 5: Negative factors
            negative_result = NegativeFactorFilter.analyze_negative_factors(property_data)
            total_score += negative_result.score  # This adds negative points
            all_reasons.extend(negative_result.reasons)
            all_red_flags.extend(negative_result.red_flags)
            
            # Step 6: Building characteristics scoring
            building_score, building_reasons = self._score_building_characteristics(property_data)
            total_score += building_score
            all_reasons.extend(building_reasons)
            
            # Normalize score to 0-10 scale
            normalized_score = max(0.0, min(10.0, total_score))
            
            # Create comprehensive description
            description_parts = []
            
            if location_result.reasons:
                description_parts.extend(location_result.reasons)
            
            if all_reasons:
                description_parts.extend(all_reasons)
            
            if all_opportunities:
                description_parts.append(f"Opportunities: {'; '.join(all_opportunities[:3])}")  # Limit to top 3
            
            if all_red_flags:
                description_parts.append(f"Concerns: {'; '.join(all_red_flags)}")
            
            # Add investment category
            if normalized_score >= 8.0:
                description_parts.append("🏆 EXCEPTIONAL INVESTMENT OPPORTUNITY")
            elif normalized_score >= 7.0:
                description_parts.append("⭐ EXCELLENT INVESTMENT POTENTIAL")
            elif normalized_score >= 6.0:
                description_parts.append("✅ GOOD INVESTMENT OPPORTUNITY")
            
            analysis_description = " | ".join(description_parts)
            
            return normalized_score, analysis_description, True
            
        except Exception as e:
            logger.error(f"Error evaluating property: {e}")
            return 0.0, f"Evaluation error: {e}", False
    
    def _score_building_characteristics(self, property_data: Dict) -> Tuple[float, List[str]]:
        """
        Score basic building characteristics
        """
        score = 0.0
        reasons = []
        
        # Age-based scoring
        construction_year = int(property_data.get('construction_year', 0))
        if construction_year > 0:
            if construction_year < AGE_SCORING['very_old_threshold']:
                score += AGE_SCORING['very_old_bonus']
                reasons.append(f"Very old building ({construction_year}) - maximum renovation potential")
            elif construction_year < AGE_SCORING['old_threshold']:
                score += AGE_SCORING['old_bonus']
                reasons.append(f"Old building ({construction_year}) - good renovation potential")
        
        # Size optimization
        building_area = float(property_data.get('building_area', 0))
        if SIZE_PREFERENCES['ideal_range'][0] <= building_area <= SIZE_PREFERENCES['ideal_range'][1]:
            score += 1
            reasons.append(f"Ideal building size ({building_area}m²)")
        
        return score, reasons
