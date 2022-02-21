# ndp d3 app for smoooth RDM...
import streamlit as st
import plotly.express as px
import pandas as pd
import geopandas as gpd # for file import here
from shapely import wkt
import json

# data prep libraries in apis.py
from apis import pno_data
from apis import hri_data
from apis import densities
from apis import tess_boundaries

# page setup
st.set_page_config(page_title="NDP App d3", layout="wide")
padding = 2
st.markdown(f""" <style>
    .reportview-container .main .block-container{{
        padding-top: {padding}rem;
        padding-right: {padding}rem;
        padding-left: {padding}rem;
        padding-bottom: {padding}rem;
    }} </style> """, unsafe_allow_html=True)

header = '<p style="font-family:sans-serif; color:grey; font-size: 12px;">\
        NDP project app3 V0.95 "Dense Beta"\
        </p>'
st.markdown(header, unsafe_allow_html=True)
# plot size setup
#px.defaults.width = 600
px.defaults.height = 600

# button style
m = st.markdown("""
<style>
div.stButton > button:first-child {
    background-color: #fab43a;
    color:#ffffff;
}
div.stButton > button:hover {
    background-color: #e75d35; 
    color:#ffffff;
    }
</style>""", unsafe_allow_html=True)

# page title
header_title = '''
:see_no_evil: **Naked Density Project**
'''
st.subheader(header_title)
header_text = '''
<p style="font-family:sans-serif; color:Dimgrey; font-size: 12px;">
Naked Density Projekti on <a href="https://research.aalto.fi/en/persons/teemu-jama" target="_blank">Teemu Jaman</a> väitöskirjatutkimus Aalto Yliopistossa.
Projektissa tutkitaan maankäytön tehokkuuden vaikutuksia kestävään kehitykseen data-analytiikan avulla.
</p>
'''
st.markdown(header_text, unsafe_allow_html=True)
st.markdown('------')
st.title("Data Paper #3")
st.markdown("Pääkaupunkiseudun maankäytön tehokkuus")
st.markdown("###")
st.title(':point_down:')

#plot setup
colormap_hri = {
    "Erilliset pientalot": "goldenrod",
    "Rivi- ja ketjutalot": "darkgoldenrod",
    "Asuinkerrostalot": "chocolate",
    "Vapaa-ajan asuinrakennukset": "gold",
    "Muut rakennukset": "gainsboro",
    "Liikenteen rakennukset": "darkcyan",
    "Kokoontumisrakennukset": "darkorange",
    "Toimistorakennukset": "cornflowerblue",
    "Maatalousrakennukset": "darkolivegreen",
    "Opetusrakennukset": "blueviolet",
    "Liikerakennukset": "orange",
    "Hoitoalan rakennukset": "darkorchid",
    "Teollisuusrakennukset": "dimgrey",
    "Varastorakennukset": "darkgrey",
    "Palo- ja pelastustoimen rakennukset": "grey"
}
colormap_osr = {
    "umpi": "chocolate",
    "tiivis": "darkgoldenrod",
    "kompakti": "darkolivegreen",
    "väljä": "lightgreen",
    "harva": "cornflowerblue",
    "haja": "lightblue"
}

# SELECTORS
c_one, c_two, c_three = st.columns(3)
rajaus = c_one.selectbox('Tarkastelurajaus',['Postinumeroalue','Oma rajaus'])
third = c_three.empty()

if rajaus == 'Oma rajaus':
    third.markdown('Rajaustiedosto')
    ohje = '''
        <p style="font-family:sans-serif; color:Dimgrey; font-size: 12px;">
        <br><br>
        Rajaustiedosto tulee olla CSV-tiedosto, jossa on "WKT" -nimiawaaä sarakkeessa rajauspolygonin
        koordinaattit epsg=4326 koordinaatistossa WKT-muodossa.
        </p>
        '''
    third.markdown(ohje, unsafe_allow_html=True)
    uploadedFile = c_two.file_uploader("Valitse rajaustiedosto", type='csv')
    if uploadedFile is not None:
        from io import StringIO
        try:
            bytesData = uploadedFile.getvalue()
            encoding = encodingUTF8
            s = str(bytesData, encoding)
            file = StringIO(s)
            df = pd.read_csv(file, error_bad_lines=True, warn_bad_lines=False, sep=',')
            try:
                df['geometry'] = df['WKT'].apply(wkt.loads)
                boundary = gpd.GeoDataFrame(df, crs=4326, geometry='geometry')
            except ValueError:
                st.error('Tarkista rajaustiedosto')
                st.stop()
        except:
            bytesData = uploadedFile.getvalue()
            encoding = 'iso8859-1'
            s = str(bytesData, encoding)
            file = StringIO(s)
            df = pd.read_csv(file, error_bad_lines=True, warn_bad_lines=False, sep=',')
            try:
                df['geometry'] = df['WKT'].apply(wkt.loads)
                boundary = gpd.GeoDataFrame(df, crs=4326, geometry='geometry')
            except ValueError:
                st.error('Tarkista rajaustiedosto')
                st.stop()

        # GET HRI DATA inside my boundary
        data = hri_data(boundary)
        pno_nimi = rajaus # for naming plots
        # plot
        myplot = data.copy()
        try:
            lat = myplot.unary_union.centroid.y
            lon = myplot.unary_union.centroid.x
            mymap = px.choropleth_mapbox(myplot,
                                         geojson=myplot.geometry,
                                         locations=myplot.index,
                                         title=f'Rakennukset alueella: {pno_nimi}',
                                         color="rakennustyyppi",
                                         hover_name="tarkenne",
                                         hover_data=['rakennusvuosi', 'kerrosala', 'kerrosluku'],
                                         mapbox_style="carto-positron",
                                         color_discrete_map=colormap_hri,
                                         center={"lat": lat, "lon": lon},
                                         zoom=13,
                                         opacity=0.8,
                                         width=1200,
                                         height=700
                                         )
            mymap.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0}, height=700,
                                legend=dict(
                                    yanchor="top",
                                    y=0.99,
                                    xanchor="left",
                                    x=0.01
                                )
                                )
        except ValueError:
            st.error('Tarkista rajaustiedosto')
            st.stop()
    else:
        st.stop()


else:
    kuntalista = ['Espoo', 'Helsinki', 'Vantaa']
    default_kunta = kuntalista.index('Espoo')
    kunta = c_two.selectbox('Valitse kaupunki', kuntalista, index=default_kunta)
    if kunta is not None:
        kuntadata = pno_data(kunta,2021)
        pno_lista = kuntadata['Postinumeroalueen nimi'].tolist()
        # select pno area
        if kunta == 'Espoo':
            def_pno = 'Tapiola'
        elif kunta == 'Helsinki':
            def_pno = 'Munkkiniemi'
        elif kunta == 'Vantaa':
            def_pno = 'Tammisto'
        default_pno = pno_lista.index(def_pno)
        pno_nimi = c_three.selectbox('Valitse postinumeroalue', pno_lista, index=default_pno)
        if pno_nimi is not None:
            # GET HRI DATA for pno area
            pno_alue = kuntadata[kuntadata['Postinumeroalueen nimi'] == pno_nimi]
            data = hri_data(pno_alue)
            #tess = tess_boundaries(data)
            #
            myplot = data.copy()
            try:
                lat = myplot.unary_union.centroid.y
                lon = myplot.unary_union.centroid.x
                mymap = px.choropleth_mapbox(myplot,
                                             geojson=myplot.geometry,
                                             locations=myplot.index,
                                             title=f'Rakennukset alueella: {pno_nimi}',
                                             color="rakennustyyppi",
                                             hover_name="tarkenne",
                                             hover_data=['rakennusvuosi', 'kerrosala', 'kerrosluku'],
                                             mapbox_style="carto-positron",
                                             color_discrete_map=colormap_hri,
                                             center={"lat": lat, "lon": lon},
                                             zoom=13,
                                             opacity=0.8,
                                             width=1200,
                                             height=700
                                             )
                mymap.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0}, height=700,
                                      legend=dict(
                                          yanchor="top",
                                          y=0.99,
                                          xanchor="left",
                                          x=0.01
                                      )
                                    )
                #
            except:
                st.write('Postinumeroalueen data puuttuu')
                st.stop()


# rakennuskanta..
plot_yrs = data.loc[(data['rakennusvuosi'] < 2023) & (data['rakennusvuosi'] > 1700)]
fig_yrs = px.scatter(plot_yrs, title=f'{pno_nimi} - Rakennuskanta rakennusvuosittain',
                     x='rakennusvuosi', y='kerrosala', color='rakennustyyppi', log_y=True,
                     hover_name='tarkenne', color_discrete_map=colormap_hri)
st.plotly_chart(fig_yrs, use_container_width=True)

with st.expander('Rakennukset kartalla', expanded=False):
    rak_plot = st.empty()
    st.plotly_chart(mymap, use_container_width=True)
    st.caption(
        "data: [hsy.fi](https://www.hsy.fi/ymparistotieto/avoindata/avoin-data---sivut/paakaupunkiseudun-rakennukset/)")
    # save
    raks = data.to_csv().encode('utf-8')
    st.download_button(label="Tallenna rakennukset CSV:nä", data=raks, file_name=f'rakennukset_{pno_nimi}.csv',
                       mime='text/csv')

# DENSITY PART
def classify_housign(density_data):
    # show only housing types
    showlist = ["Erilliset pientalot", "Rivi- ja ketjutalot", "Asuinkerrostalot"]
    housing = density_data.loc[density_data['rakennustyyppi'].isin(showlist)].dropna()
    # classify
    housing['OSR_class'] = 'umpi'
    housing.loc[housing['OSR'] > 1, 'OSR_class'] = 'tiivis'
    housing.loc[housing['OSR'] > 2, 'OSR_class'] = 'kompakti'
    housing.loc[housing['OSR'] > 4, 'OSR_class'] = 'väljä'
    housing.loc[housing['OSR'] > 8, 'OSR_class'] = 'harva'
    housing.loc[housing['OSR'] > 16, 'OSR_class'] = 'haja'
    housing['OSR_ND_class'] = 'umpi'
    housing.loc[housing['OSR_ND'] > 1, 'OSR_ND_class'] = 'tiivis'
    housing.loc[housing['OSR_ND'] > 2, 'OSR_ND_class'] = 'kompakti'
    housing.loc[housing['OSR_ND'] > 4, 'OSR_ND_class'] = 'väljä'
    housing.loc[housing['OSR_ND'] > 8, 'OSR_ND_class'] = 'harva'
    housing.loc[housing['OSR_ND'] > 16, 'OSR_ND_class'] = 'haja'
    return housing

st.markdown('###')
st.subheader('Tehokkuuslaskelmat')
st.markdown('###')
#
run_den = st.button(f'Laske tehokkuudet alueelle {pno_nimi}')
st.markdown('###')
st.markdown('###')

if run_den:
    with st.spinner(text='Laskee tehokkuuksia... tämä kestää hetken..'):
        density_data = densities(data)
        housing = classify_housign(density_data)
else:
    st.stop()

# Density expander...
with st.expander("Tehokkuusnomogrammit", expanded=True):
    #OSR
    fig_OSR = px.scatter(housing, title=f'{pno_nimi} - Tonttiväljyys',
                                  x='GSI', y='FSI', symbol='rakennustyyppi', color='OSR_class', size='kerrosala',
                                  log_y=False,
                                  hover_name='tarkenne',
                                  hover_data=['rakennusvuosi', 'kerrosala', 'kerrosluku', 'FSI', 'GSI', 'OSR', 'OSR_ND'],
                                  labels={"OSR_class": 'Tonttiväljyys','rakennustyyppi':''},
                                  category_orders={'OSR_class': ['umpi','tiivis','kompakti','väljä','harva','haja']},
                                  color_discrete_map=colormap_osr,
                                  symbol_map={'Asuinkerrostalot': 'square', 'Rivi- ja ketjutalot': 'triangle-up',
                                              'Erilliset pientalot': 'circle'}
                                  )
    fig_OSR.update_layout(xaxis_range=[0, 0.5], yaxis_range=[0, 2])
    fig_OSR.update_xaxes(rangeslider_visible=True)

    #OSR_ND
    fig_OSR_ND = px.scatter(housing, title=f'{pno_nimi} - Naapuruston väljyys',
                                   x='GSI', y='FSI', symbol='rakennustyyppi', color='OSR_ND_class', size='kerrosala',
                                   log_y=False,
                                   hover_name='tarkenne',
                                   hover_data=['rakennusvuosi', 'kerrosala', 'kerrosluku', 'FSI_ND', 'GSI_ND', 'OSR_ND'],
                                   labels={"OSR_ND_class": 'Naapuruston väljyys','rakennustyyppi':''},
                                   category_orders={'OSR_ND_class': ['umpi','tiivis','kompakti','väljä','harva','haja']},
                                   color_discrete_map=colormap_osr,
                                   symbol_map={'Asuinkerrostalot': 'square', 'Rivi- ja ketjutalot': 'triangle-up',
                                               'Erilliset pientalot': 'circle'}
                                   )
    fig_OSR_ND.update_layout(xaxis_range=[0, 0.5], yaxis_range=[0, 2])
    fig_OSR_ND.update_xaxes(rangeslider_visible=True)

    # charts..
    #col1, col2 = st.columns(2)
    st.plotly_chart(fig_OSR, use_container_width=True)
    st.plotly_chart(fig_OSR_ND, use_container_width=True)


with st.expander("Tehokkuuskartta", expanded=False):
    with st.spinner(text='Laatii karttaa..'):
        tess = tess_boundaries(data).explode()  # for plots
        # the map
        lat = housing.unary_union.centroid.y
        lon = housing.unary_union.centroid.x
        OSR_map = px.choropleth_mapbox(housing,
                                       geojson=housing.geometry,
                                       locations=housing.index,
                                       title=f'Tehokkuudet alueella: {pno_nimi}',
                                       color="OSR_ND_class",
                                       labels={"OSR_ND_class": 'Ympäristön väljyysluokat asuinrakennuksittain'},
                                       hover_name="tarkenne",
                                       hover_data=['rakennusvuosi', 'kerrosala', 'kerrosluku', 'FSI', 'GSI', 'OSR',
                                                   'OSR_ND'],
                                       mapbox_style="carto-positron",
                                       color_discrete_map=colormap_osr,
                                       category_orders={
                                           'OSR_ND_class': ['umpi', 'tiivis', 'kompakti', 'väljä', 'harva',
                                                            'haja']},
                                       center={"lat": lat, "lon": lon},
                                       zoom=14,
                                       opacity=0.8,
                                       width=1200,
                                       height=700
                                       )
        OSR_map.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0}, height=700,
                              legend=dict(
                                  yanchor="top",
                                  y=0.99,
                                  xanchor="left",
                                  x=0.01
                              ),
                              mapbox={
                                  "layers": [
                                      {
                                          "source": json.loads(tess.geometry.to_json()),
                                          "below": "traces",
                                          "type": "line",
                                          "color": "grey",
                                          "line": {"width": 0.2},
                                      }
                                  ]
                              }
                              )
        # chart
        st.plotly_chart(OSR_map, use_container_width=True)
        mapnote1 = '''
                        <p style="font-family:sans-serif; color:Dimgrey; font-size: 12px;">
                        Kartalla vain asuinrakennuksien tehokkuusluokat. Hiusviivoilla morfologiset tontit,
                        joiden rakennukset huomioitu laskennassa (kts. selitteet).
                        Mahdolliset puuttuvat rakennukset ovat puutteita lähtödatassa tai teknisiä virheitä kohteen datan laadussa.
                        </p>
                        '''
        st.markdown(mapnote1, unsafe_allow_html=True)

        # prepare save..
        density_data.insert(0, 'TimeStamp', pd.to_datetime('now').replace(microsecond=0))
        density_data['date'] = density_data['TimeStamp'].dt.date
        saved_data = density_data.drop(columns=(['uID', 'TimeStamp'])).assign(alue=pno_nimi)

        # save button
        raks = saved_data.to_csv().encode('utf-8')
        save = st.download_button(label="Tallenna CSV", data=raks, file_name=f'rakennukset_{pno_nimi}.csv',
                                  mime='text/csv')

        # secret save
        from io import StringIO
        import boto3
        from botocore.exceptions import ClientError
        bucket = 'ndpproject'
        csv_buffer = StringIO()
        saved_data.to_csv(csv_buffer)
        s3_resource = boto3.resource('s3')
        try:
            s3_resource.Object(bucket, f'ndp3/D3_v1_{pno_nimi}.csv').load()
        except ClientError as e:
            s3_resource.Object(bucket, f'ndp3/D3_v1_{pno_nimi}.csv').put(Body=csv_buffer.getvalue())


# ----------------------------------------------------------------------------------------

# expl container
with st.expander("Selitteet", expanded=False):
    st.markdown('Tehokkuuslaskelmatavat nomogrammeissa pohjautuvat uusimpaan alan tutkimukseen (kts. referenssit alla),'
                'sekä O-I Meurmanin Asemakaavaoppi-kirjassa esitettyihin laskentamalleihin vuodelta 1947.')
    # describe_table
    st.markdown(f'Tilastotaulukko {pno_nimi} (asuinrakennukset)')
    des = housing.drop(columns=['uID', 'rakennusvuosi']).describe()
    st.dataframe(des)
    # expl
    selite = '''
    **FSI** = floor space index = FAR = floor area ratio = tonttitehokkuus e<sub>t</sub><br>
    **GSI** = ground space index = peitto(coverage), eli rakennetun alueen suhde morfologiseen tonttiin <br>
    **OSR** = open space ratio = tonttiväljyys eli väljyysluku r<sub>t</sub> , eli rakentamattoman alueen suhde kerrosalaan <br>
    **suure_ND** = naapuruston vastaava arvo<br>
    **OSR_ND_mean** = naapuruston väjyyslukujen keskiarvo<br>

    Väljyysluokittelu perustuu _väljyyslukuun_. Naapuruston väljyysluku (OSR ND) on hyvä rakennetun ympäristön tehokkuuden mittari, koska se
    yhdistää sekä rakentamisen volyymin (FSI) että maankäytön (GSI + tonttirakenne ja kadut) tuottaman _kokonaistehokkuuden_.
    <br>
    _Morfologinen tontti_ on rakennuksen ympärillä oleva vapaa alue (max 100m) _polygoni tesselaationa_ suhteessa ympäröiviin päärakennuksiin (piharakennuksia ei huomioita).
    Tämä tapa on katsottu soveltuvan ympäristön tehokkuuden laskemiseen juridisia tonttirajoja paremmin, koska yhtiömuotoisilla tontteilla voi olla useampi rakennus.
    Morfologinen tontti huomioi myös kaavoitus- ja liikennesuunnittelutapojen vaikutukset.
    _Naapurusto_ käsittää kunkin rakennuksen naapuritontit kahden asteen syvyydellä (rajanaapuritontit ja niiden rajanaapurit).
    Tällä on tavoiteltu "koetun lähinaapuruston" määritelmää, johon syvyyden kautta laskettuna vaikuttaa myös valittu kaavoitustapa.
    Laskennat on toteutettu python-koodikirjastolla <a href="http://docs.momepy.org/en/stable/user_guide/elements/tessellation.html" target="_blank">Momepy</a>
    <br>
    
    Väljyysluokittelun raja-arvot:<br>
    umpi: OSR < 1 <br>
    tiivis: OSR 1-2 <br>
    kompakti: OSR 2-4 <br>
    väljä: OSR 4-8 <br>
    harva: OSR 8-16 <br>
    haja: OSR > 16 <br>
    <br>
    '''
    references = '''
    <p style="font-family:sans-serif; color:Dimgrey; font-size: 12px;">
    Referenssit:<br>
    <i>
    Berghauser Pont, Meta, and Per Haupt. 2021. Spacematrix: Space, Density and Urban Form. Rotterdam: nai010 publishers.<br>
    Dovey, Kim, Pafka, Elek. 2014. The urban density assemblage: Modelling multiple measures. Urban Des Int 19, 66–76<br>
    Meurman, Otto-I. 1947. Asemakaavaoppi. Helsinki: Rakennuskirja.<br>
    Fleischmann, Martin. 2019. momepy: Urban Morphology Measuring Toolkit. Journal of Open Source Software, 4(43), 1807<br>
    </p></i>
    '''
    st.markdown(selite, unsafe_allow_html=True)
    cs1, cs2, cs3 = st.columns(3)
    cs1.latex(r'''
            OSR = r_{t} = \frac {1-GSI} {FSI}
            ''')  # https://katex.org/docs/supported.html

    st.markdown(references, unsafe_allow_html=True)

footer_title = '''
---
:see_no_evil: **Naked Density Project**
[![MIT license](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/teemuja) 
'''
st.markdown(footer_title)

#jepjep