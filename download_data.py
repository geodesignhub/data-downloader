import requests, json, GeodesignHub
from pick import pick
from shapely.geometry import shape, mapping, shape, asShape
from fiona import collection
import fiona
import os, sys
import time
import logging
from fiona.crs import from_string
import logging.handlers
from json.decoder import JSONDecodeError

class ScriptLogger():
    def __init__(self):
        self.log_file_name = 'logs/latest.log'
        self.path = os.getcwd()
        self.logpath = os.path.join(self.path, 'logs')
        self.outputpath = os.path.join(self.path, 'output')
        if not os.path.exists(self.logpath):
            os.mkdir(self.logpath)
        if not os.path.exists(self.outputpath):
            os.mkdir(self.outputpath)
        self.logging_level = logging.INFO
        # set TimedRotatingFileHandler for root
        self.formatter = logging.Formatter('%(asctime)s %(name)s %(levelname)s %(message)s')
        # use very short interval for this example, typical 'when' would be 'midnight' and no explicit interval
        self.handler = logging.handlers.TimedRotatingFileHandler(self.log_file_name, when="S", interval=30, backupCount=10)
        self.handler.setFormatter(self.formatter)
        self.logger = logging.getLogger() # or pass string to give it a name
        self.logger.addHandler(self.handler)
        self.logger.setLevel(self.logging_level)
    def getLogger(self):
        return self.logger




if __name__ == "__main__":

    myLogger = ScriptLogger()
    logger = myLogger.getLogger()
    session = requests.Session()
    logger.info("Starting job")
    def hex_to_rgb(value):
        value = value.lstrip('#')
        lv = len(value)
        return tuple(int(value[i:i + lv // 3], 16) for i in range(0, lv, lv // 3))
    try: 
      with open('config.json') as config:
        c = json.load(config)
    except JSONDecodeError as je: 
      print("Error reading config file")
      logger.info("Error reading config file")
      sys.exit(1)

    except Exception as e: 
      print("Error reading config file")
      logger.error("Error reading config file")
      sys.exit(1)

    try:
      assert c.keys() ==set(['serviceurl', 'projectid', 'apitoken'])
    except AssertionError as ae: 
      logger.error("Error in config file parameters")
      sys.exit(1)

    myAPIHelper = GeodesignHub.GeodesignHubClient(url = c['serviceurl'], project_id=c['projectid'], token=c['apitoken'])
    counter =0


    change_teams = myAPIHelper.get_changeteams()
    change_team_id = 0
    selected_design_id = 0
    if change_teams.status_code == 200:
      change_teams_output = json.loads(change_teams.text)
      if change_teams_output:
        def get_change_team(option): return option.get('title')
        change_team_selected = pick(change_teams_output, 'Pick a Design Team', indicator='*', options_map_func=get_change_team)
        change_team_id = change_team_selected[0]['id']      

    else:
      print("Please review your projectid and apitoken in the config.py file")

    try: 
      assert change_team_id is not 0
      change_team_synthesis = myAPIHelper.get_changeteam(teamid= change_team_id)
      if change_team_synthesis.status_code == 200:
        cteam_designs = json.loads(change_team_synthesis.text)
        cteam_designs = cteam_designs["synthesis"]
        if cteam_designs: 
          title = 'Please choose an design: '
          options = cteam_designs
          def get_label(option): return option.get('description')
          selected_design = pick(options, title, indicator='*', options_map_func=get_label)
          selected_design_id = selected_design[0]['id']

        else:
          print("No designs available for this team")


    except AssertionError as ae: 
        print("No change team selected")
        logger.error("No change team selected")

    try: 
      assert selected_design_id is not 0
      design = myAPIHelper.get_synthesis(teamid = change_team_id, synthesisid = selected_design_id)

      if(design.status_code == 200):
        geojson = json.loads(design.text)

        polygons = []
        lines = []

        geojson_features = geojson["features"]

        crs = from_string("+datum=WGS84 +ellps=WGS84 +no_defs +proj=longlat")
        for feature in geojson_features: 
          if feature['geometry']['type'] in ['Polygon', 'MultiPolygon']:
            shp = asShape(feature['geometry'])
            polygons.append({'properties': feature['properties'], 'shape': shp})
          elif feature['geometry']['type'] in ['LineString', 'MultiLineString']:
            shp = asShape(feature['geometry'])
            lines.append({'properties': feature['properties'], 'shape': shp})

        polygon_schema = {'geometry': 'Polygon','properties': {'diagramid':'str', 'author':'str','desc':'str','sysname':'str','type':'str','color':'str','rgbcolor':'str'}}
        polyline_schema = {'geometry': 'LineString','properties': {'diagramid':'str','author':'str','desc':'str','sysname':'str','type':'str','color':'str','rgbcolor':'str'}}

        cwd = os.getcwd()

        logger.info("Writing Shapefiles")
        if polygons:
          shape_file = os.path.join(cwd, 'output' ,'polygons.shp')
          with collection(shape_file, 'w', driver='ESRI Shapefile',crs=crs, schema=polygon_schema) as c:
            
              ## If there are multiple geometries, put the "for" loop here
            for current_polygon in polygons:
              rgb_color = json.dumps(hex_to_rgb(current_polygon['properties']['color']))

              c.write({
                  'geometry': mapping(current_polygon['shape']),
                  'properties': {'diagramid': current_polygon['properties']['diagramid'], 'author':current_polygon['properties']['author'], 'desc':current_polygon['properties']['description'], 'sysname':current_polygon['properties']['sysname'],'type':current_polygon['properties']['areatype'],'color':current_polygon['properties']['color'],'rgbcolor':rgb_color}
              })
          

        if lines:
          shape_file = os.path.join(cwd, 'output' ,'linestring.shp')
          with collection(shape_file, 'w', driver='ESRI Shapefile',crs=crs, schema=polyline_schema) as c:
            
              ## If there are multiple geometries, put the "for" loop here
            for current_line in lines:
              rgb_color = json.dumps(hex_to_rgb(current_line['properties']['color']))
              
              c.write({
                  'geometry': mapping(current_line['shape']),
                  'properties': {'diagramid': current_line['properties']['diagramid'], 'author':current_line['properties']['author'], 'desc':current_line['properties']['description'], 'sysname':current_line['properties']['sysname'],'type':current_line['properties']['areatype'],'color':current_line['properties']['color'],'rgbcolor':rgb_color}
              })
        logger.info("Shapefiles written in output directory")
        print("Shapefiles written in output directory")
      else:
        print("Please review your projectid and apitoken in the config.py file")
        logger.error("Please review your projectid and apitoken in the config.py file")

    except AssertionError as ae:
      print("No design selected")
