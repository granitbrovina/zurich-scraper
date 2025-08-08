#!/usr/bin/env python3
"""
API Client for Swiss Real Estate Data Sources
=============================================

This module provides a unified interface for accessing various Swiss
real estate and building data APIs including geo.admin.ch, maps.zh.ch,
and other government data sources.
"""

import requests
import time
import json
import logging
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import xml.etree.ElementTree as ET
from urllib.parse import urlencode
import random

from config import (
    API_ENDPOINTS, ZURICH_BOUNDS, SCRAPING_CONFIG, 
    DATABASE_CONFIG, USER_AGENTS
)

logger = logging.getLogger(__name__)

class SwissGeoAPIClient:
    """
    Client for Swiss Federal Geo API (api3.geo.admin.ch)
    """
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': random.choice(USER_AGENTS)
        })
        self.base_url = API_ENDPOINTS['geo_admin']
        self.last_request_time = 0
        
        # Initialize cache database
        self.init_cache_db()
    
    def init_cache_db(self):
        """Initialize SQLite database for caching API responses"""
        if not DATABASE_CONFIG['enable_caching']:
            return
            
        conn = sqlite3.connect(DATABASE_CONFIG['cache_db_name'])
        conn.execute('''
            CREATE TABLE IF NOT EXISTS api_cache (
                cache_key TEXT PRIMARY KEY,
                response_data TEXT,
                created_at TIMESTAMP,
                expires_at TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()
    
    def rate_limit(self):
        """Implement rate limiting"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < SCRAPING_CONFIG['request_delay']:
            time.sleep(SCRAPING_CONFIG['request_delay'] - time_since_last)
        self.last_request_time = time.time()
    
    def get_cached_response(self, cache_key: str) -> Optional[Dict]:
        """Get cached API response if available and not expired"""
        if not DATABASE_CONFIG['enable_caching']:
            return None
            
        try:
            conn = sqlite3.connect(DATABASE_CONFIG['cache_db_name'])
            cursor = conn.execute(
                "SELECT response_data FROM api_cache WHERE cache_key = ? AND expires_at > ?",
                (cache_key, datetime.now())
            )
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return json.loads(result[0])
        except Exception as e:
            logger.error(f"Error reading cache: {e}")
        
        return None
    
    def cache_response(self, cache_key: str, response_data: Dict):
        """Cache API response"""
        if not DATABASE_CONFIG['enable_caching']:
            return
            
        try:
            expires_at = datetime.now() + timedelta(days=SCRAPING_CONFIG['cache_expiry_days'])
            conn = sqlite3.connect(DATABASE_CONFIG['cache_db_name'])
            conn.execute(
                "INSERT OR REPLACE INTO api_cache (cache_key, response_data, created_at, expires_at) VALUES (?, ?, ?, ?)",
                (cache_key, json.dumps(response_data), datetime.now(), expires_at)
            )
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Error caching response: {e}")
    
    def fetch_building_register_data(self, limit: int = 1000) -> List[Dict]:
        """
        Fetch building register data for Canton Zurich
        """
        logger.info(f"Fetching building register data (limit: {limit})")
        
        cache_key = f"building_register_zh_{limit}"
        cached_data = self.get_cached_response(cache_key)
        if cached_data:
            logger.info(f"Using cached building register data ({len(cached_data)} buildings)")
            return cached_data
        
        try:
            # Use WFS service to get building data
            wfs_url = f"{self.base_url}/wfs"
            params = {
                'service': 'WFS',
                'version': '1.1.0',
                'request': 'GetFeature',
                'typeName': API_ENDPOINTS['building_register'],
                'srsName': 'EPSG:2056',
                'outputFormat': 'GeoJSON',
                'bbox': ZURICH_BOUNDS['bbox_string'],
                'maxFeatures': limit
            }
            
            self.rate_limit()
            response = self.session.get(wfs_url, params=params, timeout=SCRAPING_CONFIG['timeout_seconds'])
            response.raise_for_status()
            
            data = response.json()
            buildings = []
            
            # Extract building features
            features = data.get('features', [])
            for feature in features:
                properties = feature.get('properties', {})
                geometry = feature.get('geometry', {})
                
                building_data = {
                    'egid': properties.get('egid'),
                    'building_category': properties.get('gklas'),
                    'construction_year': properties.get('gbauj'),
                    'building_area': properties.get('garea'),
                    'num_floors': properties.get('gastw'),
                    'num_apartments': properties.get('ganzwhg'),
                    'address': properties.get('strname_deinr'),
                    'zip_code': properties.get('dplz4'),
                    'municipality': properties.get('gdename'),
                    'coordinates': geometry.get('coordinates', []) if geometry.get('type') == 'Point' else None
                }
                
                # Only include valid buildings with EGID
                if building_data['egid']:
                    buildings.append(building_data)
            
            logger.info(f"Retrieved {len(buildings)} buildings from register")
            
            # Cache the results
            self.cache_response(cache_key, buildings)
            
            return buildings
            
        except Exception as e:
            logger.error(f"Error fetching building register data: {e}")
            return []
    
    def get_building_details(self, egid: str) -> Dict:
        """
        Get detailed building information by EGID
        """
        cache_key = f"building_details_{egid}"
        cached_data = self.get_cached_response(cache_key)
        if cached_data:
            return cached_data
        
        try:
            find_url = f"{self.base_url}/find"
            params = {
                'layer': API_ENDPOINTS['building_register'],
                'searchText': egid,
                'searchField': 'egid',
                'returnGeometry': 'false',
                'contains': 'false',
                'lang': 'en',
                'sr': '2056'
            }
            
            self.rate_limit()
            response = self.session.get(find_url, params=params, timeout=SCRAPING_CONFIG['timeout_seconds'])
            response.raise_for_status()
            data = response.json()
            
            building_details = {}
            results = data.get('results', [])
            
            if results:
                attrs = results[0].get('attributes', {})
                building_details = {
                    'construction_year': attrs.get('gbauj'),
                    'building_area': attrs.get('garea'),
                    'num_floors': attrs.get('gastw'),
                    'num_apartments': attrs.get('ganzwhg'),
                    'building_category': attrs.get('gklas'),
                    'address': attrs.get('strname_deinr'),
                    'zip_code': attrs.get('dplz4'),
                    'municipality': attrs.get('gdename'),
                    'coordinates': [attrs.get('gkoor_e'), attrs.get('gkoor_n')]
                }
                
                # Cache the result
                self.cache_response(cache_key, building_details)
            
            return building_details
            
        except Exception as e:
            logger.error(f"Error fetching building details for EGID {egid}: {e}")
            return {}
    
    def get_zoning_information(self, coordinates: Tuple[float, float]) -> Dict:
        """
        Get zoning information for given coordinates
        """
        x, y = coordinates
        cache_key = f"zoning_{x}_{y}"
        cached_data = self.get_cached_response(cache_key)
        if cached_data:
            return cached_data
        
        try:
            identify_url = f"{self.base_url}/identify"
            params = {
                'geometry': f'{x},{y}',
                'geometryType': 'esriGeometryPoint',
                'layers': f'all:{API_ENDPOINTS["zoning_layer"]}',
                'mapExtent': f'{x-100},{y-100},{x+100},{y+100}',
                'imageDisplay': '1,1,96',
                'tolerance': '10',
                'lang': 'en',
                'sr': '2056'
            }
            
            self.rate_limit()
            response = self.session.get(identify_url, params=params, timeout=SCRAPING_CONFIG['timeout_seconds'])
            response.raise_for_status()
            data = response.json()
            
            zoning_info = {}
            results = data.get('results', [])
            
            if results:
                attrs = results[0].get('attributes', {})
                zoning_info = {
                    'zone_type': attrs.get('zone_type'),
                    'max_floors': attrs.get('max_floors'),
                    'utilization_factor': attrs.get('utilization_factor'),
                    'building_coverage': attrs.get('building_coverage'),
                    'zone_description': attrs.get('zone_description')
                }
                
                # Cache the result
                self.cache_response(cache_key, zoning_info)
            
            return zoning_info
            
        except Exception as e:
            logger.error(f"Error fetching zoning info for {x},{y}: {e}")
            return {}

class ZurichMapsAPIClient:
    """
    Client for Zurich Canton Maps API (maps.zh.ch)
    """
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': random.choice(USER_AGENTS)
        })
        self.base_url = API_ENDPOINTS['maps_zh']
        self.last_request_time = 0
    
    def rate_limit(self):
        """Implement rate limiting"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < SCRAPING_CONFIG['request_delay']:
            time.sleep(SCRAPING_CONFIG['request_delay'] - time_since_last)
        self.last_request_time = time.time()
    
    def get_detailed_zoning_data(self, coordinates: Tuple[float, float]) -> Dict:
        """
        Get detailed zoning data from Zurich canton maps
        """
        try:
            x, y = coordinates
            
            # This would be the actual API call to maps.zh.ch
            # For now, simulate the response based on coordinates
            
            zoning_data = {
                'bauzonen': self._simulate_bauzonen_data(x, y),
                'max_floors_allowed': random.randint(3, 8),
                'current_utilization': random.uniform(0.4, 0.9),
                'expansion_potential': random.uniform(0.1, 0.5),
                'heritage_protection': random.choice([True, False]),
                'building_height_limit': random.randint(15, 30)
            }
            
            return zoning_data
            
        except Exception as e:
            logger.error(f"Error fetching Zurich zoning data: {e}")
            return {}
    
    def _simulate_bauzonen_data(self, x: float, y: float) -> str:
        """Simulate bauzonen data - replace with actual API call"""
        bauzonen_types = [
            'Wohnzonen 3 Vollgeschosse',
            'Wohnzonen 4 Vollgeschosse',
            'Wohnzonen 5 und mehr Vollgeschosse',
            'Wohnzonen mit Gewerbeerleichterung 3 Vollgeschosse',
            'Wohnzonen mit Gewerbeerleichterung 4 Vollgeschosse',
            'Kernzonen',
            'Zentrumszonen'
        ]
        return random.choice(bauzonen_types)

class PropertyDataEnricher:
    """
    Orchestrates data enrichment from multiple API sources
    """
    
    def __init__(self):
        self.geo_client = SwissGeoAPIClient()
        self.zurich_client = ZurichMapsAPIClient()
    
    def enrich_property_data(self, basic_property_data: Dict) -> Dict:
        """
        Enrich basic property data with information from multiple sources
        """
        try:
            enriched_data = basic_property_data.copy()
            
            egid = basic_property_data.get('egid')
            if not egid:
                return enriched_data
            
            # Get detailed building information
            building_details = self.geo_client.get_building_details(egid)
            enriched_data.update(building_details)
            
            # Get coordinates for spatial queries
            coordinates = building_details.get('coordinates')
            if coordinates and len(coordinates) == 2:
                # Get zoning information
                zoning_info = self.geo_client.get_zoning_information(tuple(coordinates))
                enriched_data.update(zoning_info)
                
                # Get detailed Zurich-specific data
                zurich_data = self.zurich_client.get_detailed_zoning_data(tuple(coordinates))
                enriched_data.update(zurich_data)
            
            # Calculate derived metrics
            enriched_data.update(self._calculate_derived_metrics(enriched_data))
            
            return enriched_data
            
        except Exception as e:
            logger.error(f"Error enriching property data: {e}")
            return basic_property_data
    
    def _calculate_derived_metrics(self, property_data: Dict) -> Dict:
        """Calculate derived metrics from raw data"""
        derived_metrics = {}
        
        try:
            # Calculate average unit size
            building_area = float(property_data.get('building_area', 0) or 0)
            num_apartments = int(property_data.get('num_apartments', 0) or 0)
            
            if num_apartments > 0 and building_area > 0:
                derived_metrics['avg_unit_size'] = building_area / num_apartments
            
            # Calculate zoning utilization factor
            current_floors = int(property_data.get('num_floors', 0) or 0)
            max_floors = int(property_data.get('max_floors_allowed', 0) or 0)
            
            if max_floors > 0:
                utilization = current_floors / max_floors
                derived_metrics['zoning_utilization_factor'] = max(0, 1 - utilization)  # Potential for expansion
            
            # Estimate construction era
            construction_year = int(property_data.get('construction_year', 0) or 0)
            if construction_year > 0:
                if construction_year < 1950:
                    derived_metrics['construction_era'] = 'pre_war'
                elif construction_year < 1980:
                    derived_metrics['construction_era'] = 'post_war'
                elif construction_year < 2000:
                    derived_metrics['construction_era'] = 'modern'
                else:
                    derived_metrics['construction_era'] = 'contemporary'
            
        except Exception as e:
            logger.error(f"Error calculating derived metrics: {e}")
        
        return derived_metrics

class APIRateLimiter:
    """
    Centralized rate limiting for all API clients
    """
    
    def __init__(self):
        self.request_times = {}
    
    def wait_if_needed(self, api_name: str):
        """Wait if needed to respect rate limits"""
        current_time = time.time()
        last_time = self.request_times.get(api_name, 0)
        
        time_since_last = current_time - last_time
        if time_since_last < SCRAPING_CONFIG['request_delay']:
            sleep_time = SCRAPING_CONFIG['request_delay'] - time_since_last
            time.sleep(sleep_time)
        
        self.request_times[api_name] = time.time()

# Global rate limiter instance
rate_limiter = APIRateLimiter()
