import geopandas as gpd
import rioxarray as rxr
import numpy as np
import matplotlib.pyplot as plt

class SatelliteImageProcessor:
    def __init__(self, s3_directory, nir_file, red_band_file):
        self.s3_directory = s3_directory
        self.nir_file = nir_file
        self.red_band_file = red_band_file
        self.band_imagery = {}

    def get_band_imagery(self):
        s3_url_list = [f'{self.s3_directory}/{file}' for file in [self.nir_file, self.red_band_file]]
        for s3_url in s3_url_list:
            try:
                band_data = rxr.open_rasterio(s3_url).squeeze()
                if self.nir_file in s3_url:
                    self.band_imagery['nir'] = band_data
                elif self.red_band_file in s3_url:
                    self.band_imagery['red_band'] = band_data
            except Exception as e:
                return e
        print(self.band_imagery['red_band'].rio.crs)

    def process_polygon(self, path_to_polygon='sample_polygon.geojson'):
        polygon = gpd.read_file(path_to_polygon)
        print("clipping")
        polygon = polygon.to_crs(self.band_imagery['red_band'].rio.crs)
        try:
            clipped_nir = self.band_imagery['nir'].rio.clip(polygon.geometry, all_touched=True, from_disk=True)
            clipped_red = self.band_imagery['red_band'].rio.clip(polygon.geometry, all_touched=True, from_disk=True)
        except Exception as e:
            print(e)
        return clipped_nir, clipped_red

    @staticmethod
    def compute_ndvi(nir, red):
        return (nir - red) / (nir + red)

    @staticmethod
    def save_image(ndvi, path='ndvi.png'):
        plt.imsave(path, ndvi, cmap='viridis')

    @staticmethod
    def save_stats(ndvi, output_file_path='ndvi_stats.txt'):
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
        with open(output_file_path, "w", encoding="utf-8", newline="\n") as file:
            file.writelines(write_stats)

# Example usage
satellite_processor = SatelliteImageProcessor(
    s3_directory='s3://sentinel-cogs/sentinel-s2-l2a-cogs/36/N/YF/2023/6/S2B_36NYF_20230605_0_L2A/',
    nir_file='B08.tif',
    red_band_file='B04.tif'
)
satellite_processor.get_band_imagery()
nir, red = satellite_processor.process_polygon()
ndvi = SatelliteImageProcessor.compute_ndvi(nir, red)
ndvi.rio.write_nodata(np.nan, inplace=True)
ndvi = ndvi.rio.interpolate_na()
SatelliteImageProcessor.save_image(ndvi)
SatelliteImageProcessor.save_stats(ndvi)
