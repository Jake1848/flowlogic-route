import pandas as pd
from datetime import time
from typing import List, Tuple, Optional
from models.models import Stop, Truck, SpecialConstraint, TruckType
from services.natural_language import NaturalLanguageProcessor
import logging

logger = logging.getLogger(__name__)


def parse_time_window(time_str: str) -> Tuple[time, time]:
    """Parse time window string like '08:00-12:00' into time objects"""
    try:
        start_str, end_str = time_str.split('-')
        start_hour, start_min = map(int, start_str.split(':'))
        end_hour, end_min = map(int, end_str.split(':'))
        return time(start_hour, start_min), time(end_hour, end_min)
    except Exception as e:
        logger.error(f"Error parsing time window '{time_str}': {e}")
        raise ValueError(f"Invalid time window format: {time_str}")


def parse_time(time_str: str) -> time:
    """Parse time string like '08:00' into time object"""
    try:
        hour, minute = map(int, time_str.split(':'))
        return time(hour, minute)
    except Exception as e:
        logger.error(f"Error parsing time '{time_str}': {e}")
        raise ValueError(f"Invalid time format: {time_str}")


def parse_stops_csv(file_content: str, auto_enrich: bool = True) -> List[Stop]:
    """Enhanced stops CSV parser with AI data enrichment"""
    nlp = NaturalLanguageProcessor() if auto_enrich else None
    
    try:
        df = pd.read_csv(pd.io.common.StringIO(file_content))
        
        # Flexible column detection - handle various naming conventions
        column_mapping = _detect_column_mapping(df.columns.tolist())
        logger.info(f"Detected column mapping: {column_mapping}")
        
        # Validate required columns
        if 'address' not in column_mapping:
            raise ValueError("Address column is required but not found")
        
        stops = []
        enrichment_stats = {"enriched": 0, "warnings": []}
        
        for idx, row in df.iterrows():
            try:
                # Extract data with fallbacks
                stop_id = _extract_stop_id(row, column_mapping, idx)
                address = row[column_mapping['address']].strip()
                
                # AI-powered data enrichment
                enriched_data = {}
                if auto_enrich and nlp:
                    enriched_data = nlp.enrich_stop_data(address)
                    if enriched_data.get("ai_reasoning"):
                        enrichment_stats["enriched"] += 1
                
                # Parse time window with AI fallback
                time_start, time_end = _parse_time_window_flexible(
                    row, column_mapping, enriched_data
                )
                
                # Parse pallets with AI estimation
                pallets = _parse_pallets_flexible(
                    row, column_mapping, enriched_data
                )
                
                # Parse special constraints with AI inference
                special_constraint = _parse_constraint_flexible(
                    row, column_mapping, enriched_data, address
                )
                
                stop = Stop(
                    stop_id=stop_id,
                    address=address,
                    time_window_start=time_start,
                    time_window_end=time_end,
                    pallets=pallets,
                    special_constraint=special_constraint,
                    service_time_minutes=enriched_data.get("service_time_minutes", 15)
                )
                stops.append(stop)
                
            except Exception as e:
                warning = f"Row {idx + 1}: {str(e)}"
                enrichment_stats["warnings"].append(warning)
                logger.warning(warning)
                continue
        
        if enrichment_stats["enriched"] > 0:
            logger.info(f"AI enriched {enrichment_stats['enriched']} stops")
        
        if enrichment_stats["warnings"]:
            logger.warning(f"Skipped {len(enrichment_stats['warnings'])} rows due to errors")
        
        logger.info(f"Successfully parsed {len(stops)} stops with {enrichment_stats['enriched']} AI enrichments")
        return stops
    
    except Exception as e:
        logger.error(f"Error parsing stops CSV: {e}")
        raise


def _detect_column_mapping(columns: List[str]) -> dict:
    """Detect column mappings for flexible CSV parsing"""
    columns_lower = [col.lower() for col in columns]
    mapping = {}
    
    # Address detection
    for i, col in enumerate(columns_lower):
        if any(keyword in col for keyword in ['address', 'addr', 'location', 'destination']):
            mapping['address'] = columns[i]
            break
    
    # Stop ID detection
    for i, col in enumerate(columns_lower):
        if any(keyword in col for keyword in ['stopid', 'stop_id', 'id', 'stop']):
            mapping['stop_id'] = columns[i]
            break
    
    # Time window detection
    for i, col in enumerate(columns_lower):
        if any(keyword in col for keyword in ['timewindow', 'time_window', 'window', 'time']):
            mapping['time_window'] = columns[i]
            break
    
    # Pallets detection
    for i, col in enumerate(columns_lower):
        if any(keyword in col for keyword in ['pallets', 'pallet', 'quantity', 'qty', 'units']):
            mapping['pallets'] = columns[i]
            break
    
    # Special constraints detection
    for i, col in enumerate(columns_lower):
        if any(keyword in col for keyword in ['special', 'constraint', 'type', 'handling']):
            mapping['special'] = columns[i]
            break
    
    return mapping


def _extract_stop_id(row, column_mapping: dict, fallback_idx: int) -> int:
    """Extract stop ID with fallback to row index"""
    if 'stop_id' in column_mapping:
        try:
            return int(row[column_mapping['stop_id']])
        except (ValueError, TypeError):
            pass
    
    return fallback_idx + 1


def _parse_time_window_flexible(row, column_mapping: dict, enriched_data: dict) -> Tuple[time, time]:
    """Parse time window with AI enrichment fallback"""
    if 'time_window' in column_mapping and pd.notna(row[column_mapping['time_window']]):
        try:
            return parse_time_window(str(row[column_mapping['time_window']]))
        except ValueError:
            logger.warning(f"Invalid time window format: {row[column_mapping['time_window']]}")
    
    # Use AI enriched time window
    if "suggested_time_window" in enriched_data:
        try:
            return parse_time_window(enriched_data["suggested_time_window"])
        except ValueError:
            pass
    
    # Default time window
    logger.info(f"Using default time window 08:00-17:00 for address: {row[column_mapping['address']]}")
    return time(8, 0), time(17, 0)


def _parse_pallets_flexible(row, column_mapping: dict, enriched_data: dict) -> int:
    """Parse pallets with AI estimation fallback"""
    if 'pallets' in column_mapping and pd.notna(row[column_mapping['pallets']]):
        try:
            return int(float(row[column_mapping['pallets']]))
        except (ValueError, TypeError):
            logger.warning(f"Invalid pallets value: {row[column_mapping['pallets']]}")
    
    # Use AI estimated pallets
    if "estimated_pallets" in enriched_data:
        logger.info(f"Using AI estimated pallets: {enriched_data['estimated_pallets']}")
        return enriched_data["estimated_pallets"]
    
    # Default pallet count
    logger.info(f"Using default 3 pallets for address: {row[column_mapping['address']]}")
    return 3


def _parse_constraint_flexible(row, column_mapping: dict, enriched_data: dict, address: str) -> SpecialConstraint:
    """Parse special constraints with AI inference"""
    if 'special' in column_mapping and pd.notna(row[column_mapping['special']]):
        constraint_str = str(row[column_mapping['special']]).strip()
        try:
            return SpecialConstraint(constraint_str)
        except ValueError:
            logger.warning(f"Unknown special constraint '{constraint_str}', using AI inference")
    
    # Use AI inferred constraint
    if "special_constraint" in enriched_data:
        try:
            constraint = SpecialConstraint(enriched_data["special_constraint"])
            logger.info(f"Using AI inferred constraint '{constraint.value}' for {address}")
            return constraint
        except ValueError:
            pass
    
    return SpecialConstraint.NONE


def parse_trucks_csv(file_content: str) -> List[Truck]:
    """Parse trucks CSV content into Truck objects"""
    try:
        df = pd.read_csv(pd.io.common.StringIO(file_content))
        
        required_columns = ['TruckID', 'Depot', 'MaxPallets', 'Type', 'ShiftStart', 'ShiftEnd']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")
        
        trucks = []
        for _, row in df.iterrows():
            truck_type = row['Type'].strip()
            if truck_type not in [e.value for e in TruckType]:
                logger.warning(f"Unknown truck type '{truck_type}', defaulting to DRY")
                truck_type = TruckType.DRY
            else:
                truck_type = TruckType(truck_type)
            
            truck = Truck(
                truck_id=str(row['TruckID']).strip(),
                depot_address=row['Depot'].strip(),
                max_pallets=int(row['MaxPallets']),
                truck_type=truck_type,
                shift_start=parse_time(row['ShiftStart']),
                shift_end=parse_time(row['ShiftEnd'])
            )
            trucks.append(truck)
        
        logger.info(f"Successfully parsed {len(trucks)} trucks")
        return trucks
    
    except Exception as e:
        logger.error(f"Error parsing trucks CSV: {e}")
        raise