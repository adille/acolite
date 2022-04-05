"""
Create netcdf files for ONDA storage

AD 2022 03

log

TO BE ADDED
[17:19] Clémence Goyens
For the HYPSTAR: next time (sorry Antoine I should have checked earlier bu forgot ) I think in the longname we should add the wavelength and maybe add the version number of the hypernets tools ....
 like hypernets processor (not tools oops)



"""
import os, datetime, time
import pandas as pd
import xarray as xr
import numpy as np
import acolite as ac
from scipy import ndimage

import matplotlib
import matplotlib.pyplot as plt
matplotlib.use('Qt5Agg')


Resample = True

#############################
#    B. Sentinel 2 data     #
#############################
print(" >>> b. reading satellite data...")

def create_S2_xarray_4_ONDA(S2_dataset):
    xds = xr.open_dataset(S2_dataset, decode_coords="all")
    try:
        image_name = xds.oname
    except:
        try:
            image_name = xds.output_name
        except:
            image_name = os.path.basename(S2_dataset)
    day = datetime.datetime(*map(int, image_name.split('_')[2:8]))

    # 2.a. variable selection
    vars_list_2keep = ['transverse_mercator',
                       'x',
                       'y',
                       'lon',
                       'lat',
                       'l2_flags',
                       'chl_oc2_BLK',
                       'chl_re_moses2bBLK',
                       'SPM_Nechad2010_665',
                       'chl_re_mishraBLK',
                       'SPM_Nechad2010_665',
                       'TUR_Nechad2009_665'
                       ]

    rrs_list = [elem for elem in list(xds.variables) if (elem[:3] in ['Rrs', 'rrs'])]
    vars_list_2keep = vars_list_2keep + rrs_list

    for var in list(xds.variables):
        if var not in vars_list_2keep:
            xds = xds.drop_vars(var)

    # temp:
    xds = xds.rename({'chl_oc2': 'chl_bluegreen'})
    xds.chl_bluegreen.attrs['units'] = 'mg m-3'
    xds = xds.rename({'chl_re_mishra2B': 'chl_rededge'})
    xds.chl_rededge.attrs['units'] = 'mg m-3'
    try:
        xds = xds.rename({'SPM_Nechad2010_665': 'SPM'})
    except:
        # temp SPM
        A665 = 355.85
        C665 = 0.1725
        spm665  = A665 * xds.Rrs_665/np.pi / (1 - xds.Rrs_665/np.pi / C665)
        xds['SPM'] = spm665
        xds.SPM.attrs = {'units': 'g m-3',
                         'long_name': 'suspended particulate matter',
                         'parameter': 'SPM_Nechad2010_665',
                         'algorithm': '2010 calibration',
                         'title': 'Nechad SPM',
                         'reference': 'Nechad et al. 2010',
                         'A_SPM': '355.85',
                         'C_SPM': '0.1725',
                         }
    try:
        xds = xds.rename({'TUR_Nechad2009_665': 'TUR'})
    except:
        # temp TUR
        A665 = 610.94
        C665 = 0.2324
        tur665 = A665 * xds.Rrs_665/np.pi / (1 - xds.Rrs_665/np.pi / C665)
        xds['TUR'] = tur665
        xds.TUR.attrs = {'units': 'FNU',
                         'long_name': 'turbidity',
                         'parameter': 'TUR_Nechad2009_665',
                         'algorithm': '2010 calibration',
                         'title': 'Nechad TUR',
                         'reference': 'Nechad et al. 2009',
                         'A_TUR': '610.94',
                         'C_TUR': '0.2324',
                     }

    ###
    #  2.b. attributes selection
    xds.attrs['contact'] = 'dvanderzande@naturalsciences.be, cgoyens@naturalsciences.be'

    attrs_list_2keep = ['generated_by', 'generated_on', 'contact', 'product_type',
                  'metadata_profile', 'metadata_version', 'Conventions', 'sensor',
                  'global_dims', 'granule', 'oname', 'scene_xrange', 'scene_yrange',
                  'scene_proj4_string', 'scene_pixel_size', 'scene_dims', 'limit',
                  'proj4_string', 'pixel_size', 'projection_key', 'data_dimensions',
                  'data_elements', 's2_target_res'
                  ]

    l2w_mask_list = [elem for elem in list(xds.attrs) if (elem[:8] in ['l2w_mask'])]
    attrs_list_2keep = attrs_list_2keep + l2w_mask_list

    for att in list(xds.attrs):
        if att not in attrs_list_2keep:
            xds.attrs.__delitem__(att)

    #####
    # resample
    if Resample is True:
        list2resample = [elem for elem in list(xds.variables) if elem not in [ 'l2_flags', 'lon', 'lat', 'x', 'y', 'transverse_mercator', 'spatial_ref']]
        for item in list2resample:
            xds[item].values = ndimage.median_filter(xds[item], 3)

    #####
    # 2.c. save to netcdf
    # Creates output folder if does not exists
    if os.path.exists(out_S2_dir) is False: os.mkdir(out_S2_dir)

    out_name = 'BLK_' + day.strftime('%Y_%m_%d_') + 'S2' + '.nc'
    # save to netcdf
    xds.to_netcdf(os.path.join(out_S2_dir, out_name))

    print('saved to --> ', out_name)

# # !!!! +++ SPM/TUR +++++
# allfiles = os.listdir(in_S2_dir)
# S2_images_list = [image for image in allfiles if image[-len('.nc'):] in ['.nc']]
# S2_images_list_path = [in_S2_dir + '/' + image for image in S2_images_list]

# for S2_image in S2_images_list_path:
#     create_S2_xarray(S2_image)


# create_S2_xarray(S2_images_list_path[317])

# xds = xr.open_dataset(S2_images_list_path[317])
#
# from scipy import misc
#
# # from skimage import filters
# # size = 20
# # structuring_element = np.ones((3*size, 3*size))
# # smooth_mean = filters.rank.mean(xds.Rrs_665, structuring_element)
#
#
# med_denoised = ndimage.median_filter(xds.Rrs_665, 2)
#
# fig, axs = plt.subplots(1,2, figsize =(15,15))
# axs[0].imshow(xds.Rrs_665)
# axs[1].imshow(med_denoised)
# plt.tight_layout()
#
#
# fig, axs = plt.subplots(1,2, figsize =(15,15))
# axs[0].imshow(xds.Rrs_665)
# axs[1].imshow(smooth_mean)
# plt.tight_layout()