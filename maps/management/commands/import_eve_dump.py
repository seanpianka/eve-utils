import math
import sqlite3

from django.db import transaction
from django.core.management.base import LabelCommand

from static_dump.models import *

import networkx
import progressbar

class Command(LabelCommand):
    help = "Given the filename of an eve online static dump in sqlite format, import the solar system data for use by the application"
    
    @transaction.atomic
    def handle_label(self, label, **options):
        self.import_data(label)
        
            
    def create_temp_collections(self):
        #create a collection to store regions, for use by the autocomplete ajax
        #fields: _id (region id), name, name_lower (lowercase)
        db.create_collection("dev_region")
        db.dev_region.create_index([("name_lower", pymongo.ASCENDING), ("name", pymongo.ASCENDING)])
        
        #create a collection to store solar systems, for use by the autocomplete ajax
        #fields: _id (system id), name, name_lower (lowercase), region_id, constellation_name, region_name
        db.create_collection("dev_system")
        db.dev_system.create_index([("name_lower", pymongo.ASCENDING), ("name", pymongo.ASCENDING)])
        db.dev_system.create_index([("region_id", pymongo.ASCENDING)])
        
        #create a collection to store stations, for use by the autocomplete ajax
        #fields: _id (station id), name, name_lower (lowercase)
        db.create_collection("dev_station")
        db.dev_station.create_index([("name_lower", pymongo.ASCENDING), ("name", pymongo.ASCENDING)])
        
        #create a collection to store graph nodes
        #fields: _id (denormalize id), system_id, type ("gate" or "station"), system security, 
        db.create_collection("dev_map_node")
        
        #create a collection to store graph edges
        #instead of fields, each document represents the neighbor of a fiven node. the keys are node IDs, and the values are distance
        #when an edge goes between two "ends" of a gate, the distance is None
        db.create_collection("dev_map_edge")
        
        
    def import_data(self, filename):
        con = sqlite3.connect(filename)
        con.row_factory = sqlite3.Row
        cursor = con.cursor()
        
        #create a mapping from system id to a list of gates and a list of stations
        systems = {row['solarSystemID']:{'security':row['security'], 'objects':[]} for row in cursor.execute("SELECT solarSystemID, security FROM mapsolarsystems")}

        print(list(systems.values())[0])
        
        #load the gates
        for row in cursor.execute("SELECT j.stargateID, j.destinationID, d.solarSystemID, d.x, d.y, d.z FROM mapjumps AS j JOIN mapdenormalize AS d ON d.itemID = j.stargateID"):
            
            gate_entry = {
                'denormalize_id':row['stargateID'], #the "origin" denormalize entry for this jump. this is the physical gate located in space in the system
                'destination_denormalize_id':row['destinationID'], #the "destination" denormalize entry for this jump
                'position':(row['x'], row['y'], row['z'])
            }
            systems[row['solarSystemID']]['objects'].append(gate_entry)
        
        #load the stations
        for row in cursor.execute("SELECT stationID, solarSystemID, x, y, z FROM stastations"):
            
            station_entry = {
                'denormalize_id':row['stationID'],
                'destination_denormalize_id':None,
                'position':(row['x'], row['y'], row['z'])
            }
            systems[row['solarSystemID']]['objects'].append(station_entry)
            
        
        #create a networkx graph to store the data in
        map_graph = networkx.Graph()
        
        #first add all the nodes
        print("Generating nodes")
        for system_id, system_data in systems.items():
            
            for item in system_data['objects']:
                map_graph.add_node(item['denormalize_id'], system_id=system_id, security=system_data['security'])
            
        #add edges
        print("Generating edges")
        for system_id, system_data in systems.items():
            
            for item in system_data['objects']:
                
                #if destination is not None, this is a gate, so create an edge from this "side" of the gate to the other "side"
                #make the distance None, because didtance doesn't really make sense here
                if(item['destination_denormalize_id'] is not None):
                    map_graph.add_edge(item['denormalize_id'], item['destination_denormalize_id'], distance=None)
                    
                #make an edge from this item to every other item in this system
                for other in system_data['objects']:
                    if(item != other):
                        
                        #compute the distance from 'item' to 'other'
                        px,py,pz = item['position']
                        nx,ny,nz = other['position']
                        
                        dx = px - nx
                        dy = py - ny
                        dz = pz - nz
                        
                        distance = math.sqrt(dx*dx + dy*dy + dz*dz)
                        
                        map_graph.add_edge(item['denormalize_id'], other['denormalize_id'], distance=distance)
                        
        
        #find the largest connected subgraph. this will weed out the wormhole systems and jove regions
        print("Removing unconnected components")
        main_map = list(networkx.connected_component_subgraphs(map_graph))[0]
        
        #keep a set to keep track of which systems are in our connected component
        connected_systems = set()
        
        #insert the nodes from main_map into the database

        print("Inserting nodes and edges")
        with progressbar.ProgressBar(max_value=len(main_map.nodes())) as bar:
            for i, (node_id, data) in enumerate(main_map.nodes_iter(data=True)):
                bar.update(i)

                connected_systems.add(data['system_id'])
                GraphNode.objects.create(id=node_id, system_id=data['system_id'])
                
                #build the edge document for this node too
                edge_document = {}
                for neighbor_id, data in main_map[node_id].items():
                    GraphEdge.objects.create(origin_id=node_id, destination_id=neighbor_id, distance=data['distance'])
            
        
        #we need to gather a list of non wormhole and non jove regions
        connected_regions = set()
        connected_constellations = set()
        
        print("Inserting systems")
        for row in cursor.execute("""
                SELECT 
                    s.solarSystemID AS system_id, s.solarSystemName AS name, s.security AS security,
                    s.constellationID AS constellation_id, 
                    s.regionID AS region_id
                FROM mapsolarsystems AS s 
                JOIN mapconstellations AS c ON s.constellationID = c.constellationID
                JOIN mapregions AS r ON s.regionID = r.regionID
                """):
            if(row['system_id'] in connected_systems):
                connected_regions.add(row['region_id'])
                connected_constellations.add(row['constellation_id'])

                MapSolarSystem.objects.create(id=row['system_id'], region_id=row['region_id'], constellation_id=row['constellation_id'], name=row['name'], security_level=row['security'])


        print("Inserting constellations")
        for row in cursor.execute("""
                SELECT 
                    c.constellationID AS contellation_id, c.constellationName AS name, 
                    c.regionID AS region_id, r.regionName AS region_name
                FROM mapconstellations AS c 
                JOIN mapregions AS r ON c.regionID = r.regionID
                """):
            if(row['contellation_id'] in connected_constellations):
                MapConstellation.objects.create(id=row['contellation_id'], region_id=row['region_id'], name=row['name'])


        print("Inserting constellations")
        for row in cursor.execute("""
                SELECT 
                    r.regionID AS region_id, r.regionName AS name
                FROM mapregions AS r
                """):
            if(row['region_id'] in connected_regions):
                MapRegion.objects.create(id=row['region_id'], name=row['name'])


        print("Inserting stations")
        for row in cursor.execute("SELECT stationID, stationName, solarSystemID FROM stastations"):
            if(row['solarSystemID'] in connected_systems):
                Station.objects.create(id=row['stationID'], system_id=row['solarSystemID'], name=row['stationName'])
                
    def save_temp_collections(self):
        db.dev_region.rename("region", dropTarget=True)
        db.dev_system.rename("solar_system", dropTarget=True)
        db.dev_station.rename("station", dropTarget=True)
        db.dev_map_node.rename("map_node", dropTarget=True)
        db.dev_map_edge.rename("map_edge", dropTarget=True)
    
    def drop_temp_collections(self):
        db.drop_collection("dev_region")
        db.drop_collection("dev_system")
        db.drop_collection("dev_station")
        db.drop_collection("dev_map_node")
        db.drop_collection("dev_map_edge")
        
        
        
        