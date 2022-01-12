# ndp d3 app for smoooth RDM...
import streamlit as st
import plotly.express as px
import pandas as pd
import geopandas as gpd # for file import here
from shapely import wkt

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
        NDP project app3 V0.75 "Dense Betaman"\
        </p>'
st.markdown(header, unsafe_allow_html=True)
# plot size setup
#px.defaults.width = 600
px.defaults.height = 600

# page title
header_title = '''
:see_no_evil: **Naked Density Project**
'''
st.subheader(header_title)
header_text = '''
<p style="font-family:sans-serif; color:Dimgrey; font-size: 12px;">
Naked Density Projekti on <a href="https://github.com/teemuja" target="_blank">Teemu Jaman</a> väitöskirjatutkimus Aalto Yliopistossa.
Projektissa tutkitaan maankäytön tehokkuuden ja kaupunkirakenteen fyysisten piirteiden
vaikutuksia kestävään kehitykseen data-analytiikan avulla.
</p>
'''
st.markdown(header_text, unsafe_allow_html=True)

st.markdown("""---""")
st.title('Data Paper #0.9')
st.caption('Digitaalinen datapaperi tutkimustiedon analysointiin ja visualisointiin')
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
    "tehokas": "chocolate",
    "tiivis": "darkgoldenrod",
    "väljä": "darkolivegreen",
    "harva": "cornflowerblue"
}

# SELECTORS
c_one, c_two, c_three = st.columns(3)
rajaus = c_one.selectbox('Tarkastelurajaus',['Postinumeroalue','Oma rajaus'])
st.markdown('-----')
if rajaus == 'Oma rajaus':
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

        except ValueError:
            st.error('Tarkista rajaustiedosto')
            st.stop()
    else:
        st.stop()
    c_three.markdown('Rajaustiedosto')
    ohje = '''
    <p style="font-family:sans-serif; color:Dimgrey; font-size: 12px;">
    Rajaustiedosto tulee olla CSV-tiedosto, jossa on "WKT" -niminen sarake, joka sisältää rajauspolygonin
    koordinaattit epsg=4326 koordinaatistossa WKT-muodossa.
    </p>
    '''
    c_three.markdown(ohje, unsafe_allow_html=True)

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

            except:
                st.write('Postinumeroalueen data puuttuu')
                st.stop()

with st.expander('Rakennukset kartalla', expanded=False):
    rak_plot = st.empty()
    st.plotly_chart(mymap, use_container_width=True)
    st.caption(
        "data: [hsy.fi](https://www.hsy.fi/ymparistotieto/avoindata/avoin-data---sivut/paakaupunkiseudun-rakennukset/)")
    # save
    raks = data.to_csv().encode('utf-8')
    st.download_button(label="Tallenna rakennukset CSV:nä", data=raks, file_name=f'rakennukset_{pno_nimi}.csv',
                       mime='text/csv')

# rakennuskanta
with st.expander("Kerrosalahistoriikki", expanded=False):
    # plot years
    plot_yrs = data.loc[(data['rakennusvuosi'] < 2023) & (data['rakennusvuosi'] > 1700)]
    fig_yrs = px.scatter(plot_yrs, title=f'{pno_nimi} - Rakennuskanta rakennusvuosittain',
                         x='rakennusvuosi', y='kerrosala', color='rakennustyyppi', log_y=True,
                         hover_name='tarkenne', color_discrete_map=colormap_hri)
    st.plotly_chart(fig_yrs, use_container_width=True)


# DENSITY PART
st.markdown('-----')
st.subheader('Tehokkuuslaskelmat')

def classify_housign(density_data):
    # show only housing types
    showlist = ["Erilliset pientalot", "Rivi- ja ketjutalot", "Asuinkerrostalot"]
    housing = density_data.loc[density_data['rakennustyyppi'].isin(showlist)].dropna()
    # classify
    housing['OSR_class'] = 'tehokas'
    housing.loc[housing['OSR'] > 2, 'OSR_class'] = 'tiivis'
    housing.loc[housing['OSR'] > 10, 'OSR_class'] = 'väljä'
    housing.loc[housing['OSR'] > 20, 'OSR_class'] = 'harva'
    housing['OSR_ND_class'] = 'tehokas'
    housing.loc[housing['OSR_ND'] > 2, 'OSR_ND_class'] = 'tiivis'
    housing.loc[housing['OSR_ND'] > 10, 'OSR_ND_class'] = 'väljä'
    housing.loc[housing['OSR_ND'] > 20, 'OSR_ND_class'] = 'harva'
    return housing


# --- Initialising SessionState ---
if "load_state" not in st.session_state:
    st.session_state.load_state = False
    if st.button('Laske tehokkuudet') or st.session_state.load_state:
        st.session_state.load_state = True
        density_data = densities(data)
        housing = classify_housign(density_data)
else:
    density_data = densities(data)
    housing = classify_housign(density_data)

def create_plot(density_data,osr_ve):
    if osr_ve == 'Tonttiväljyys':
        @st.cache
        def plot_with_osr(housing):
            fig_dens = px.scatter(housing, title=f'{pno_nimi} - Tehokkuussuureiden nomogrammi',
                                  x='GSI', y='FSI', symbol='rakennustyyppi', color='OSR_class', size='kerrosala',
                                  log_y=False,
                                  hover_name='tarkenne',
                                  hover_data=['rakennusvuosi', 'kerrosala', 'kerrosluku', 'FSI', 'GSI', 'OSR', 'OSR_ND'],
                                  labels={"OSR_class": f'{osr_ve}'},
                                  color_discrete_map=colormap_osr,
                                  symbol_map={'Asuinkerrostalot': 'square', 'Rivi- ja ketjutalot': 'triangle-up',
                                              'Erilliset pientalot': 'circle'}
                                  )
            fig_dens.update_layout(legend={'traceorder': 'normal'})
            fig_dens.update_layout(xaxis_range=[0, 0.5], yaxis_range=[0, 2])
            fig_dens.update_xaxes(rangeslider_visible=True)
            return fig_dens
        fig_out = plot_with_osr(housing)

    else:
        @st.cache
        def plot_with_osr_nd(housing):
            fig_dens = px.scatter(housing, title=f'{pno_nimi} - Tehokkuussuureiden nomogrammi',
                                   x='GSI', y='FSI', symbol='rakennustyyppi', color='OSR_ND_class', size='kerrosala',
                                   log_y=False,
                                   hover_name='tarkenne',
                                   hover_data=['rakennusvuosi', 'kerrosala', 'kerrosluku', 'FSI', 'GSI', 'OSR', 'OSR_ND'],
                                   labels={"OSR_ND_class": f'{osr_ve}'},
                                   color_discrete_map=colormap_osr,
                                   symbol_map={'Asuinkerrostalot': 'square', 'Rivi- ja ketjutalot': 'triangle-up',
                                               'Erilliset pientalot': 'circle'}
                                   )
            fig_dens.update_layout(legend={'traceorder': 'normal'})
            fig_dens.update_layout(xaxis_range=[0, 0.5], yaxis_range=[0, 2])
            fig_dens.update_xaxes(rangeslider_visible=True)
            return fig_dens
        fig_out = plot_with_osr_nd(housing)
    return fig_out

# SET PLACE FOR DENSITY PLOT
plot_spot = st.empty()
# select plot type
osr_ve = st.radio("Väljyysluokittelun mittakaava", ('Tonttiväljyys', 'Naapuruston väljyys'))

if osr_ve == 'Tonttiväljyys':
    plot = create_plot(density_data,'Tonttiväljyys')
    plot_spot.plotly_chart(plot, use_container_width=True)
else:
    plot = create_plot(density_data, 'Naapuruston väljyys')
    plot_spot.plotly_chart(plot, use_container_width=True)


# map container
with st.expander("Tehokkuusluokat kartalla", expanded=False):
    import json
    map_spot = st.empty()
    tess = tess_boundaries(data).explode()

    def housing_plot(plot):
        if osr_ve == 'Tonttiväljyys':
            mapcolor = plot['OSR_class']
        else:
            mapcolor = plot['OSR_ND_class']
        lat = plot.unary_union.centroid.y
        lon = plot.unary_union.centroid.x
        map = px.choropleth_mapbox(plot,
                                   geojson=plot.geometry,
                                   locations=plot.index,
                                   color=mapcolor,
                                   hover_name="tarkenne",
                                   hover_data=['rakennusvuosi', 'kerrosala', 'kerrosluku', 'FSI', 'GSI', 'OSR', 'OSR_ND'],
                                   mapbox_style="carto-positron",
                                   labels={'OSR_class': 'Tonttiväljyys','OSR_ND_class': 'Naapuruston väljyys'},
                                   color_discrete_map=colormap_osr,
                                   center={"lat": lat, "lon": lon},
                                   zoom=13,
                                   opacity=0.8,
                                   width=1200,
                                   height=700
                                   )
        map.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0}, height=700,mapbox={
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
        return map
    # plot
    with map_spot:
        st.plotly_chart(housing_plot(housing), use_container_width=True)
    mapnote1 = '''
        <p style="font-family:sans-serif; color:Dimgrey; font-size: 12px;">
        Kartalla visualisoitu vain nomogrammin kohteet. Arvot laskettu huomioiden kaikki rakennustyypit (kts. selitteet). Morfologiset tontit hiusviivalla.
        </p>
        '''
    st.markdown(mapnote1, unsafe_allow_html=True)

# expl container
with st.expander("Selitteet", expanded=False):
    # describe_table
    st.markdown('Tilastotaulukko (asuinrakennukset)')
    des = housing.drop(columns=['uID', 'rakennusvuosi']).describe()
    st.dataframe(des)
    # expl
    selite = '''
    FSI = floor space index = tonttitehokkuus e<sub>t</sub> (ympyrän koko kuvaa rakennuksen kerrosalaa)<br>
    GSI = ground space index = peitto(coverage), eli rakennetun alueen suhde morfologiseen tonttiin <br>
    OSR = open space ratio = tonttiväljyys eli väljyysluku r<sub>t</sub> (rakentamattoman alueen suhde kerrosalaan tontilla)<br>
    OSR_ND = naapuruston väljyys (naapurustotonttien väjyyslukujen keskiarvo)<br>

    Väljyysluokittelu perustuu väljyyslukuun. Väljyysluku (OSR) on hyvä rakennetun ympäristön tehokkuuden mittari, koska se
    yhdistää sekä rakentamisen volyymin (FSI) että maankäytön (GSI) tuottamat tehokkuussuureet. O-I Meurman esitti Asemakaavaoppi -kirjassaan,
    että väljyysluvun tulisi kerrostaloalueilla olla vähintään 2-3 ja pientaloalueilla 7-8 (Meurman 1947, s. 226). </p>
    <p style="font-family:sans-serif; color:Dimgrey; font-size: 12px;">
    Väljyysluokittelun raja-arvot:<br>
    tehokas: OSR < 2, tiivis: 2 < OSR < 10, väljä: 10 < OSR < 20, harva: OSR > 20 <br>
    '''
    soveltaen = '''
    Soveltaen:<br>
    Berghauser Pont, Meta, and Per Haupt. 2021. Spacematrix: Space, Density and Urban Form. Rotterdam: nai010 publishers.<br>
    Meurman, Otto-I. 1947. Asemakaavaoppi. Helsinki: Rakennuskirja.<br>
    Morfologinen tontti on rakennuksen ympärillä oleva vapaa alue (max 100m) _polygoni tesselaationa_ suhteessa ympäröiviin päärakennuksiin (piharakennuksia ei huomioita).
    Tämä tapa on katsottu soveltuvan ympäristön tehokkuuden laskemiseen juridisia tonttirajoja paremmin, koska yhtiömuotoisilla tontteilla voi olla useampi rakennus.
    Morfologinen tontti huomioi myös kaavoitus- ja liikennesuunnittelutapojen vaikutukset (kts. Tehokkuusluokat kartalla).
    Naapurusto käsittää kunkin rakennuksen naapuritontit kahden asteen syvyydellä (rajanaapuritontit ja niiden rajanaapurit).
    Tällä on tavoiteltu "koetun lähinaapuruston" määritelmää, johon syvyyden kautta laskettuna vaikuttaa myös valittu kaavoitustapa.
    Laskennat on toteutettu python-koodikirjastolla <a href="http://docs.momepy.org/en/stable/user_guide/elements/tessellation.html" target="_blank">Momepy</a>
    </p>
    '''
    st.markdown(selite, unsafe_allow_html=True)
    cs1, cs2, cs3 = st.columns(3)
    cs1.latex(r'''
            OSR = r_{t} = \frac {1-GSI} {FSI}
            ''')  # https://katex.org/docs/supported.html

    st.markdown(soveltaen, unsafe_allow_html=True)

footer_title = '''
---
:see_no_evil: **Naked Density Project**
[![MIT license](https://img.shields.io/badge/License-MIT-yellow.svg)](https://lbesson.mit-license.org/) 
'''
st.markdown(footer_title)

#jepjep