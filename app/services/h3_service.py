# app/services/h3_service.py

import h3
from typing import List, Tuple, Dict
from app.core.config import settings


class H3Service:
    """Servicio para trabajar con hexágonos H3"""
    
    def __init__(self, resolution: int = None):
        self.resolution = resolution or settings.DEFAULT_H3_RESOLUTION
    
    def lat_lng_to_cell(self, lat: float, lng: float) -> str:
        """Convertir coordenadas a H3 index"""
        return h3.latlng_to_cell(lat, lng, self.resolution)
    
    def cell_to_lat_lng(self, h3_index: str) -> Tuple[float, float]:
        """Obtener centro del hexágono"""
        lat, lng = h3.cell_to_latlng(h3_index)
        return lat, lng
    
    def cell_to_boundary(self, h3_index: str) -> List[Tuple[float, float]]:
        """Obtener vértices del hexágono para dibujar en mapa"""
        boundary = h3.cell_to_boundary(h3_index)
        return [(lat, lng) for lat, lng in boundary]
    
    def polyline_to_cells(self, polyline: str) -> List[str]:
        """
        Convertir polyline (de actividad) a lista de H3 cells
        Polyline es el formato codificado de Google Maps
        """
        # Decodificar polyline
        points = self._decode_polyline(polyline)
        
        # Convertir cada punto a H3 cell
        cells = set()
        for lat, lng in points:
            cell = self.lat_lng_to_cell(lat, lng)
            cells.add(cell)
        
        return list(cells)
    
    def get_neighbors(self, h3_index: str, k: int = 1) -> List[str]:
        """Obtener hexágonos vecinos (útil para expansión de territorio)"""
        return list(h3.grid_disk(h3_index, k))
    
    def get_area_cells(
        self, 
        center_lat: float, 
        center_lng: float, 
        radius_km: float
    ) -> List[str]:
        """
        Obtener todos los hexágonos en un radio dado
        Útil para inicializar zonas de una ciudad
        """
        center_cell = self.lat_lng_to_cell(center_lat, center_lng)
        
        # Calcular k-ring necesario
        # Área de hexágono en resolución 9 es ~0.1 km²
        hex_area = h3.cell_area(center_cell, unit='km^2')
        k_rings = int((radius_km ** 2) / hex_area) + 1
        
        return list(h3.grid_disk(center_cell, k_rings))
    
    def cells_distance(self, h3_index1: str, h3_index2: str) -> int:
        """Distancia en hexágonos entre dos cells"""
        return h3.grid_distance(h3_index1, h3_index2)
    
    def is_valid_cell(self, h3_index: str) -> bool:
        """Validar si un H3 index es válido"""
        return h3.is_valid_cell(h3_index)
    
    @staticmethod
    def _decode_polyline(polyline: str) -> List[Tuple[float, float]]:
        """
        Decodificar polyline de Google Maps
        Formato: https://developers.google.com/maps/documentation/utilities/polylinealgorithm
        """
        points = []
        index = 0
        lat = 0
        lng = 0
        
        while index < len(polyline):
            # Decodificar latitud
            result = 0
            shift = 0
            while True:
                b = ord(polyline[index]) - 63
                index += 1
                result |= (b & 0x1f) << shift
                shift += 5
                if b < 0x20:
                    break
            
            dlat = ~(result >> 1) if result & 1 else result >> 1
            lat += dlat
            
            # Decodificar longitud
            result = 0
            shift = 0
            while True:
                b = ord(polyline[index]) - 63
                index += 1
                result |= (b & 0x1f) << shift
                shift += 5
                if b < 0x20:
                    break
            
            dlng = ~(result >> 1) if result & 1 else result >> 1
            lng += dlng
            
            points.append((lat / 1e5, lng / 1e5))
        
        return points
    
    def get_city_stats(self, h3_indexes: List[str]) -> Dict:
        """Estadísticas de una colección de zonas"""
        if not h3_indexes:
            return {
                "total_zones": 0,
                "total_area_km2": 0,
                "resolution": self.resolution
            }
        
        total_area = sum(
            h3.cell_area(cell, unit='km^2') 
            for cell in h3_indexes
        )
        
        return {
            "total_zones": len(h3_indexes),
            "total_area_km2": round(total_area, 2),
            "resolution": self.resolution
        }


# Instancia global
h3_service = H3Service()

