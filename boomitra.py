import geopandas as gpd
import rioxarray as rxr
import numpy as np
import matplotlib.pyplot as plt

def get_band_imagery(
    s3_directory='s3://sentinel-cogs/sentinel-s2-l2a-cogs/36/N/YF/2023/6/S2B_36NYF_20230605_0_L2A/',
    nir_file='B08.tif',
    red_band_file='B04.tif'
):
    '''Takes path to AWS Sentinel or an S3 Bucket as params and returns a dict: {'nir': data, 'red_band': data, 'crs': crs_value}. Default Values to prevent errors during input stage'''
    band_imagery_dict = {}
    s3_url_list = [f'{s3_directory}/{file}' for file in [nir_file, red_band_file]]
    for s3_url in s3_url_list:
        try:
            band_data = rxr.open_rasterio(s3_url).squeeze()
            if nir_file in s3_url:
                band_imagery_dict['nir'] = band_data
            elif red_band_file in s3_url:
                band_imagery_dict['red_band'] = band_data
        except Exception as e:
            return e
    print(band_imagery_dict['red_band'].rio.crs)
    return band_imagery_dict

def process_polygon(imagery_data, path_to_polygon='sample_polygon.geojson'):
    '''Opens Local Geopandas Polygon File, Subsets the imagery data.'''
    polygon = gpd.read_file(path_to_polygon)
    print("clipping")
    polygon = polygon.to_crs(imagery_data['red_band'].rio.crs)
    try:
        clipped_nir = imagery_data['nir'].rio.clip(polygon.geometry, all_touched=True, from_disk=True)
        clipped_red = imagery_data['red_band'].rio.clip(polygon.geometry, all_touched=True, from_disk=True)
    except Exception as e:
        print(e)
    return clipped_nir, clipped_red

def compute_ndvi(nir, red):
    '''Takes nir and radband rio.xarrays and returns computed ndvi.'''
    ndvi = (nir - red) / (nir + red)
    return ndvi

def save_image(ndvi, path='ndvi.png'):
    '''Saves Image, Output Image File Path can be sent as an optional param.'''
    plt.imsave(path, ndvi, cmap='viridis')

def save_stats(ndvi, output_file_path:str='ndvi_stats.txt'):
    '''Computes Stats and Writes to txt file. File path can be sent as an optional param.'''
    mean_value = ndvi.mean().values
    max_value = ndvi.max().values
    min_value = ndvi.min().values
    std_deviation = ndvi.std().values
    print("Computing Stats....")
    write_stats = [
        f'Mean: {mean_value}\n',
        f'Max: {max_value}\n',
        f'Min: {min_value}\n',
        f'Std. Dev: {std_deviation}\n'
    ]
    with open(output_file_path, "w", encoding="utf-8", newline ="\n") as file:
        file.writelines(write_stats)

sat_imagery = get_band_imagery()
nir, red = process_polygon(sat_imagery)
ndvi = compute_ndvi(nir, red)
ndvi.rio.write_nodata(np.nan, inplace=True)
ndvi = ndvi.rio.interpolate_na()
save_image(ndvi)
save_stats(ndvi)
