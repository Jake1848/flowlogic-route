"""
Enterprise Integration Module for FlowLogic RouteAI
Connects with major TMS platforms: Descartes, SAP TM, Oracle OTM, Manhattan Associates
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel
import requests
import json
import logging

logger = logging.getLogger(__name__)

class EnterpriseIntegration:
    """Base class for enterprise TMS integrations"""
    
    def __init__(self, platform: str, config: Dict[str, Any]):
        self.platform = platform
        self.config = config
        
    async def sync_routes(self, routes: List[Dict]) -> Dict[str, Any]:
        """Sync optimized routes back to enterprise system"""
        raise NotImplementedError
        
    async def import_orders(self) -> List[Dict]:
        """Import orders/shipments from enterprise system"""
        raise NotImplementedError

class DescartesIntegration(EnterpriseIntegration):
    """Descartes GLN and Route Planner integration"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("descartes", config)
        self.api_base = config.get("api_url", "https://api.descartes.com")
        self.api_key = config.get("api_key")
        
    async def sync_routes(self, routes: List[Dict]) -> Dict[str, Any]:
        """Send optimized routes to Descartes Route Planner"""
        try:
            # Transform FlowLogic routes to Descartes format
            descartes_routes = []
            for route in routes:
                descartes_route = {
                    "vehicle_id": route.get("truck_id"),
                    "driver_id": route.get("driver_id", "AUTO"),
                    "stops": [
                        {
                            "sequence": i + 1,
                            "address": stop.get("address"),
                            "latitude": stop.get("latitude"),
                            "longitude": stop.get("longitude"),
                            "time_window_start": stop.get("time_window_start"),
                            "time_window_end": stop.get("time_window_end"),
                            "service_time": stop.get("service_time_minutes", 15),
                            "order_ids": [stop.get("order_id")]
                        }
                        for i, stop in enumerate(route.get("stops", []))
                    ]
                }
                descartes_routes.append(descartes_route)
            
            # Send to Descartes API
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            response = requests.post(
                f"{self.api_base}/v1/routes/import",
                headers=headers,
                json={"routes": descartes_routes}
            )
            
            return {
                "success": response.status_code == 200,
                "message": f"Synced {len(routes)} routes to Descartes",
                "external_ids": response.json().get("route_ids", [])
            }
            
        except Exception as e:
            logger.error(f"Descartes sync error: {e}")
            return {"success": False, "error": str(e)}
    
    async def import_orders(self) -> List[Dict]:
        """Import pending orders from Descartes"""
        try:
            headers = {"Authorization": f"Bearer {self.api_key}"}
            response = requests.get(f"{self.api_base}/v1/orders/pending", headers=headers)
            
            orders = response.json().get("orders", [])
            
            # Transform to FlowLogic format
            flowlogic_orders = []
            for order in orders:
                flowlogic_order = {
                    "order_id": order.get("id"),
                    "address": order.get("delivery_address"),
                    "latitude": order.get("delivery_lat"),
                    "longitude": order.get("delivery_lng"),
                    "pallets": order.get("weight", 1) // 100,  # Estimate pallets from weight
                    "time_window_start": order.get("earliest_delivery"),
                    "time_window_end": order.get("latest_delivery"),
                    "special_requirements": order.get("handling_instructions"),
                    "external_system": "descartes",
                    "external_id": order.get("id")
                }
                flowlogic_orders.append(flowlogic_order)
            
            return flowlogic_orders
            
        except Exception as e:
            logger.error(f"Descartes import error: {e}")
            return []

class SAPTMIntegration(EnterpriseIntegration):
    """SAP Transportation Management integration"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("sap_tm", config)
        self.sap_host = config.get("sap_host")
        self.username = config.get("username")
        self.password = config.get("password")
        
    async def sync_routes(self, routes: List[Dict]) -> Dict[str, Any]:
        """Send routes to SAP TM via IDoc or REST API"""
        try:
            # SAP TM expects specific XML/JSON format
            sap_routes = {
                "FreightUnit": [
                    {
                        "FreightUnitUUID": route.get("truck_id"),
                        "TransportationMode": "01",  # Road transport
                        "TotalDistance": route.get("total_miles", 0),
                        "TotalDuration": route.get("total_time_hours", 0) * 3600,
                        "Stops": [
                            {
                                "StopUUID": f"STOP_{i}",
                                "SequenceNumber": i + 1,
                                "LocationDescription": stop.get("address"),
                                "Latitude": stop.get("latitude"),
                                "Longitude": stop.get("longitude"),
                                "PlannedArrivalDateTime": stop.get("eta"),
                                "ServiceDuration": (stop.get("service_time_minutes", 15) * 60)
                            }
                            for i, stop in enumerate(route.get("stops", []))
                        ]
                    }
                    for route in routes
                ]
            }
            
            # Send to SAP TM REST API
            auth = (self.username, self.password)
            headers = {"Content-Type": "application/json"}
            
            response = requests.post(
                f"{self.sap_host}/sap/bc/rest/flowlogic/routes",
                auth=auth,
                headers=headers,
                json=sap_routes
            )
            
            return {
                "success": response.status_code in [200, 201],
                "message": f"Synced {len(routes)} routes to SAP TM",
                "sap_response": response.json()
            }
            
        except Exception as e:
            logger.error(f"SAP TM sync error: {e}")
            return {"success": False, "error": str(e)}

class OracleOTMIntegration(EnterpriseIntegration):
    """Oracle Transportation Management integration"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("oracle_otm", config)
        self.otm_url = config.get("otm_url")
        self.username = config.get("username")
        self.password = config.get("password")
        
    async def sync_routes(self, routes: List[Dict]) -> Dict[str, Any]:
        """Send routes to Oracle OTM"""
        try:
            # Oracle OTM XML format
            otm_xml = self._build_otm_xml(routes)
            
            # Send via Oracle OTM web services
            headers = {
                "Content-Type": "text/xml",
                "SOAPAction": "updateRoutes"
            }
            
            response = requests.post(
                f"{self.otm_url}/GC3Services",
                auth=(self.username, self.password),
                headers=headers,
                data=otm_xml
            )
            
            return {
                "success": response.status_code == 200,
                "message": f"Synced {len(routes)} routes to Oracle OTM"
            }
            
        except Exception as e:
            logger.error(f"Oracle OTM sync error: {e}")
            return {"success": False, "error": str(e)}
    
    def _build_otm_xml(self, routes: List[Dict]) -> str:
        """Build Oracle OTM XML format"""
        # Simplified XML structure for Oracle OTM
        xml_content = '''<?xml version="1.0" encoding="UTF-8"?>
        <GLogXMLElement>
            <TransmissionHeader>
                <SentBy>FlowLogic</SentBy>
                <SendingApplication>RouteAI</SendingApplication>
            </TransmissionHeader>
            <GLogXML>
        '''
        
        for route in routes:
            xml_content += f'''
                <Shipment>
                    <ShipmentGid>ROUTE_{route.get("truck_id")}</ShipmentGid>
                    <TotalDistanceKm>{route.get("total_miles", 0) * 1.60934}</TotalDistanceKm>
                    <TotalDurationMinutes>{route.get("total_time_hours", 0) * 60}</TotalDurationMinutes>
            '''
            
            for i, stop in enumerate(route.get("stops", [])):
                xml_content += f'''
                    <ShipmentStop>
                        <StopNum>{i + 1}</StopNum>
                        <Location>
                            <LocationGid>LOC_{stop.get("stop_id")}</LocationGid>
                            <LocationName>{stop.get("address", "")}</LocationName>
                        </Location>
                        <ArrivalDateTime>{stop.get("eta", "")}</ArrivalDateTime>
                    </ShipmentStop>
                '''
            
            xml_content += '</Shipment>'
        
        xml_content += '''
            </GLogXML>
        </GLogXMLElement>
        '''
        
        return xml_content

class ManhattanTMIntegration(EnterpriseIntegration):
    """Manhattan Active Transportation Management integration"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("manhattan", config)
        self.api_base = config.get("api_url")
        self.tenant_id = config.get("tenant_id")
        self.api_token = config.get("api_token")
        
    async def sync_routes(self, routes: List[Dict]) -> Dict[str, Any]:
        """Send routes to Manhattan Active TM"""
        try:
            manhattan_payload = {
                "tenantId": self.tenant_id,
                "routes": [
                    {
                        "routeId": route.get("truck_id"),
                        "vehicleId": route.get("truck_id"),
                        "totalMiles": route.get("total_miles", 0),
                        "totalHours": route.get("total_time_hours", 0),
                        "stops": [
                            {
                                "stopNumber": i + 1,
                                "address": {
                                    "addressLine1": stop.get("address", ""),
                                    "latitude": stop.get("latitude"),
                                    "longitude": stop.get("longitude")
                                },
                                "timeWindow": {
                                    "startTime": stop.get("time_window_start"),
                                    "endTime": stop.get("time_window_end")
                                },
                                "serviceTimeMinutes": stop.get("service_time_minutes", 15)
                            }
                            for i, stop in enumerate(route.get("stops", []))
                        ]
                    }
                    for route in routes
                ]
            }
            
            headers = {
                "Authorization": f"Bearer {self.api_token}",
                "Content-Type": "application/json",
                "X-Tenant-ID": self.tenant_id
            }
            
            response = requests.post(
                f"{self.api_base}/transportation/v1/routes",
                headers=headers,
                json=manhattan_payload
            )
            
            return {
                "success": response.status_code in [200, 201],
                "message": f"Synced {len(routes)} routes to Manhattan Active TM"
            }
            
        except Exception as e:
            logger.error(f"Manhattan TM sync error: {e}")
            return {"success": False, "error": str(e)}

# Integration factory
def create_integration(platform: str, config: Dict[str, Any]) -> EnterpriseIntegration:
    """Factory method to create appropriate integration instance"""
    integrations = {
        "descartes": DescartesIntegration,
        "sap_tm": SAPTMIntegration,
        "oracle_otm": OracleOTMIntegration,
        "manhattan": ManhattanTMIntegration
    }
    
    if platform not in integrations:
        raise ValueError(f"Unsupported platform: {platform}")
    
    return integrations[platform](config)