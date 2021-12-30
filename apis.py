# apis for ndp_d3
from owslib.wfs import WebFeatureService
import pandas as pd
import geopandas as gpd
import streamlit as st

import osmnx as ox
from shapely.geometry import Point

def loc2bbox(address,radius=1000):
    def make_bbox(center,radius,point_crs='4326',projected_crs='3857'):
        bounds=gpd.GeoSeries(center)
        bounds=bounds.set_crs(epsg=point_crs)
        bounds=bounds.to_crs(epsg=projected_crs)
        bounds=bounds.buffer(radius)
        bounds=bounds.to_crs(epsg=point_crs)[0].bounds
        return(bounds)
    location = ox.geocode(address)
    init_point = Point(location[1],location[0])
    bbox_tuple = make_bbox(init_point,radius) + tuple(['urn:ogc:def:crs:EPSG::4326'])
    return bbox_tuple

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
    paavodata['kunta'] = paavodata['kunta'].apply(lambda x: kunta_dict[x])
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
    gdf_pno = pno.overlay(gdf.to_crs(3067), how='intersection')[columns]#.to_crs(4326)
    gdf_pno.rename(columns={'valm_v': 'rakennusvuosi',
                          'kayt_luok': 'rakennustyyppi',
                          'kayttark': 'tarkenne',
                          }, inplace=True)
    gdf_out = gdf_pno.to_crs(epsg=4326)
    return gdf_out

def densities(gdf):
    import momepy
    # jatka...

# eipätaaskaanvissiin