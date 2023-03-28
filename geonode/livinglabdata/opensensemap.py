import requests
import datetime
import os
import geopandas as gpd
import pandas as pd
from shapely.geometry import Point

def get_city_bounding_box(city_name):
    """"
    Function to retrieve bounding box coordinates of a city. Input is city name as a string.
    Result can be used as input argument for function "get_box_data" which gets sensorbox data for all boxes within the given bounding box.
    """
    # Set the base URL for the API
    base_url = "https://nominatim.openstreetmap.org/search"

    # Set the search query
    query = city_name

    # Set the parameters for the API call
    params = {
        "q": query,
        "format": "json"
    }

    # Make the API call
    response = requests.get(base_url, params=params)

    # Check the status code of the response
    if response.status_code == 200:
        # If the request was successful, the data will be in the response's JSON
        data = response.json()

        # Extract the bounding box from the response
        bounding_box = data[0]["boundingbox"]

        # Shift the order of the coordinates so that it is in the correct order as used in OpenSenseMap API calls
        bounding_box_ordered = [bounding_box[2], bounding_box[0], bounding_box[3], bounding_box[1]]

        # Join the bounding box coordinates with commas
        bounding_box_string = ",".join(bounding_box_ordered)

        # Print the result
        print(f"Bounding box of {city_name} retrieved: {bounding_box_string}")

        # Return the bounding box
        return bounding_box_string
    else:
        # If the request was not successful, print and return the error message
        print(response.text)
        return response.text

def get_box_data(bounding_box, phenomenon, start_date=None, end_date=None, limit=100):
    """
    Function to retrieve data for a particular phenomenon from senseboxes within a given bounding box.
    The bounding box should be a string in the format "min_lon,min_lat,max_lon,max_lat"; the function "get_city_bounding_box" returns the coordinates in this order.
    Budapest bounding box for example usage: 18.9251057,47.3496899,19.3349258,47.6131468
    The 'phenomenon' parameter must be one of the following: "Temperatur", "Luftdruck" or "PM2.5".
    The input variables start_date and end_date need to be in RFC 3339 format. If no input is given, the function will download data from the last 24 hours.
    """

    # Validate the phenomenon parameter
    if phenomenon not in ['Temperatur', 'Luftdruck', 'PM2.5']:
        raise ValueError('Invalid phenomenon parameter. Must be one of: Temperatur, Luftdruck, PM2.5.')

    # If no start and end dates are given, set them to now-24hrs and now, respectively
    if start_date is None:
        start_date = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime('%Y-%m-%dT%H:%M:%SZ')
    if end_date is None:
        end_date = datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')

    # Set the parameters for the API call
    payload = {
        "phenomenon": phenomenon,
        "bbox": bounding_box,
        "from-date": start_date,
        "to-date": end_date,
        "limit": limit
    }

    # Set the base URL for the API
    base_url = "https://api.opensensemap.org/boxes/data"

    # Make the API call
    print(f"Downloading data for: {payload}")
    response = requests.get(base_url, params=payload)
    print(response.url)

    # If the request was successful, post the csv response content to the GeoNode API endpoint
    if response.status_code == 200:

        # Write API response of opensensemap into a csv
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        filename = f'{phenomenon}_{today}.csv'
        filepath = os.path.join('geonode', 'livinglabdata', 'data', filename)
        with open(filepath, 'wb') as f:
            f.write(response.content)

    # If the request was not successful, print and return the error message
    else:
        print(response.text)
        return response.text


# b = get_city_bounding_box("Budapest")
# get_box_data(b, "PM2.5")

filename = "PM2.5_2023-03-01.csv"
filepath = os.path.join('geonode', 'livinglabdata', 'data', filename)

def csv_to_gpkg(filename, crs=None):
     # Read the CSV file into a pandas dataframe
    df = pd.read_csv(filename)
    
    print(f"File contents to be converted: {df}")

    # Create a point geometry for each station
    geometry = [Point(xy) for xy in zip(df.lon, df.lat)]

    # Create a geopandas dataframe
    gdf = gpd.GeoDataFrame(df, geometry=geometry)

    # Use WGS84 if no other CRS is specified
    if crs is None:
        crs='EPSG:4326'

    # remove .csv and add .gpkg to filename and save as GeoPackage
    gpkg_filename = filename[:-4] + '.gpkg'  

    gdf.to_file(gpkg_filename, driver='GPKG', crs=crs)

    print(f"Succesfully converted csv into GeoPackage: file is in {gpkg_filename}")

def post_gpkg_to_geoserver(geopackage_path, layer_name):
    
    # Set GeoServer info -- posting to already existing GeoNode data store
    geoserver_username='admin'
    geoserver_password='geoserver'
    geoserver_url='http://localhost/geoserver'
    workspace_name='geonode'
    datastore_name='geonode_data'
    
    # Prepare the data for uploading
    files = {'file': open(geopackage_path, 'rb')}
    data = {
        'name': layer_name,
        'type': 'geopackage',
        'description': 'GeoPackage containing OpenSenseMap data for Budapest',
        'enabled': 'true',
        'overwrite': 'true',
        'configure': 'all'
    }

    # Set the headers for authentication and content type
    headers = {'Content-type': 'application/json'}
    auth = (geoserver_username, geoserver_password)

    # Publish the layer
    response = requests.post(f'{geoserver_url}/rest/workspaces/{workspace_name}/datastores/{datastore_name}/featuretypes',
                             headers=headers, auth=auth, json={'featureType': data})

    if response.status_code == 201:
        print(f'Layer {layer_name} published successfully.')
        return True
    else:
        print(f'Error publishing layer: {response.text}')
        return False

