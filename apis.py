# apis for ndp_d3
from owslib.wfs import WebFeatureService
import pandas as pd
import geopandas as gpd
import momepy
import streamlit as st

@st.cache(allow_output_mutation=True)
def pno_data(kunta,vuosi=2021):
    url = 'http://geo.stat.fi/geoserver/postialue/wfs'  # vaestoruutu tai postialue
    wfs = WebFeatureService(url=url, version="2.0.0")
    layer = f'postialue:pno_tilasto_{vuosi}'
    data_ = wfs.getfeature(typename=layer, outputFormat='json')  # propertyname=['kunta'],
    gdf_all = gpd.read_file(data_)
    noneed = ['id', 'euref_x', 'euref_y', 'pinta_ala']
    paavodata = gdf_all.drop(columns=noneed)
    kuntakoodit = pd.read_csv('config/kunta_dict.csv', index_col=False, header=0).astype(str)
    kuntakoodit['koodi'] = kuntakoodit['koodi'].str.zfill(3)
    kunta_dict = pd.Series(kuntakoodit.kunta.values, index=kuntakoodit.koodi).to_dict()
    paavodata = paavodata.replace({'kunta':kunta_dict})
    dict_feat = pd.read_csv('config/paavo2021_dict.csv', skipinitialspace=True, header=None, index_col=0,squeeze=True).to_dict()
    selkopaavo = paavodata.rename(columns=dict_feat).sort_values('Kunta')
    pno_valinta = selkopaavo[selkopaavo['Kunta'] == kunta].sort_values('Asukkaat yhteensä', ascending=False)
    return pno_valinta

@st.cache(allow_output_mutation=True)
def hri_data(pno):
    def make_bbox(pno, point_crs='4326', projected_crs='3857'):  # 3879
        poly = gpd.GeoSeries(pno.geometry)
        b = poly.to_crs(epsg=projected_crs)
        b = b.buffer(100)
        bbox = b.to_crs(epsg=point_crs).bounds
        bbox = bbox.reset_index(drop=True)
        bbox_tuple = bbox['minx'][0], bbox['miny'][0], bbox['maxx'][0], bbox['maxy'][0]
        return bbox_tuple
    bbox = make_bbox(pno) + tuple(['urn:ogc:def:crs:EPSG::4326'])
    url = 'https://kartta.hsy.fi/geoserver/wfs'
    wfs = WebFeatureService(url=url, version="2.0.0")
    layer = 'ilmasto_ja_energia:rakennukset'
    data = wfs.getfeature(typename=layer, bbox=bbox, outputFormat='json')
    gdf = gpd.read_file(data)
    # columns to keep
    columns = ['kuntanimi', 'valm_v', 'kerrosala', 'kerrosluku', 'kayt_luok', 'kayttark', 'geometry']
    # overlay with pno area & use only columns
    gdf_pno = pno.to_crs(3067).overlay(gdf.to_crs(3067), how='intersection')[columns]#.to_crs(4326)
    gdf_pno.rename(columns={'valm_v': 'rakennusvuosi',
                          'kayt_luok': 'rakennustyyppi',
                          'kayttark': 'tarkenne',
                          }, inplace=True)
    gdf_out = gdf_pno.to_crs(epsg=4326)
    return gdf_out

@st.cache(allow_output_mutation=True)
def densities(buildings):
    # projected crs for momepy calculations & prepare for housing
    gdf_ = buildings.to_crs(3857)
    gdf_['kerrosala'] = pd.to_numeric(gdf_['kerrosala'], errors='coerce', downcast='float')
    gdf_['kerrosala'].fillna(gdf_.area, inplace=True)
    no_list = ['Muut rakennukset','Palo- ja pelastustoimen rakennukset','Varastorakennukset']
    yes_serie = ~gdf_.rakennustyyppi.isin(no_list) # exclude some types
    gdf = gdf_[yes_serie]
    gdf['uID'] = momepy.unique_id(gdf)
    limit = momepy.buffered_limit(gdf)
    tessellation = momepy.Tessellation(gdf, unique_id='uID', limit=limit).tessellation
    # calculate GSI = ground space index = coverage = CAR = coverage area ratio
    tess_GSI = momepy.AreaRatio(tessellation, gdf,
                                momepy.Area(tessellation).series,
                                momepy.Area(gdf).series, 'uID')
    gdf['GSI'] = round(tess_GSI.series,3)
    # calculate FSI = floor space index = FAR = floor area ratio
    gdf['FSI'] = round(gdf['kerrosala'] / momepy.Area(tessellation).series,3)
    # calculate OSR = open space ratio = spaciousness
    gdf['OSR'] = round((1 - gdf['GSI']) / gdf['FSI'],3)
    # remove infinite values of osr
    gdf['OSR'].clip(upper=gdf['OSR'].quantile(0.99), inplace=True)
    # calculate average GSI of nearby plots as
    # queen contiguity for 2 degree neighbours = "perceived neighborhood"
    tessellation = tessellation.merge(gdf[['uID', 'OSR']])  # add OSR values to tesselation areas for calculation below
    sw = momepy.sw_high(k=2, gdf=tessellation, ids='uID')
    # add median OSR of "perceived neighborhood" for each building
    gdf['OSR_ND'] = momepy.AverageCharacter(tessellation, values='OSR', spatial_weights=sw, unique_id='uID').mean
    gdf['OSR_ND'] = round(gdf['OSR_ND'],2)
    gdf_out = gdf.to_crs(4326)
    return gdf_out

@st.cache(allow_output_mutation=True)
def tess_boundaries(buildings):
    # projected crs for momepy calculations & prepare for housing
    gdf_ = buildings.to_crs(3857)
    gdf_['kerrosala'] = pd.to_numeric(gdf_['kerrosala'], errors='coerce', downcast='float')
    gdf_['kerrosala'].fillna(gdf_.area, inplace=True)
    no_list = ['Muut rakennukset','Palo- ja pelastustoimen rakennukset','Varastorakennukset']
    yes_serie = ~gdf_.rakennustyyppi.isin(no_list) # exclude some types
    gdf = gdf_[yes_serie]
    gdf['uID'] = momepy.unique_id(gdf)
    limit = momepy.buffered_limit(gdf)
    tessellation = momepy.Tessellation(gdf, unique_id='uID', limit=limit).tessellation
    return tessellation.to_crs(4326)
