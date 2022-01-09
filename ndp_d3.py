# ndp d3 app for smoooth RDM...
import streamlit as st
import plotly.express as px

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
st.markdown("""---""")
st.title('Data Paper #0.9')
st.caption('Digitaalinen datapaperi tutkimustiedon analysointiin ja visualisointiin')
st.title(':point_down:')

# selectors
c1, c2 = st.columns(2)
kuntalista = ['Espoo','Helsinki','Vantaa']
default_kunta = kuntalista.index('Espoo')
kunta = c1.selectbox('Valitse kaupunki', kuntalista, index=default_kunta)
# get pno data..
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
pno_nimi = c2.selectbox('Valitse postinumeroalue', pno_lista, index=default_pno)
# get hri data
pno_alue = kuntadata[kuntadata['Postinumeroalueen nimi'] == pno_nimi]
data = hri_data(pno_alue)

# prep
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

# plot years
plot_yrs = data.loc[(data['rakennusvuosi'] < 2023) & (data['rakennusvuosi'] > 1700)]
fig_yrs = px.scatter(plot_yrs, title=f'{pno_nimi} - Kerrosalahistoriikki',
                         x='rakennusvuosi', y='kerrosala', color='rakennustyyppi', log_y=True,
                         hover_name='tarkenne', color_discrete_map=colormap_hri)
st.plotly_chart(fig_yrs, use_container_width=True)
st.caption("data: [hsy.fi](https://www.hsy.fi/ymparistotieto/avoindata/avoin-data---sivut/paakaupunkiseudun-rakennukset/)")
st.markdown('-----')
st.subheader('Tehokkuuslaskelmat')

density_data = densities(data) # cache not working?

# show only housing types
showlist = ["Erilliset pientalot", "Rivi- ja ketjutalot", "Asuinkerrostalot"]
housing = density_data.loc[density_data['rakennustyyppi'].isin(showlist)].dropna()

# SET PLACE FOR DENSITY PLOT
plot_spot = st.empty()

# classify
housing['OSR_class'] = 'tehokas'
housing.loc[housing['OSR'] > 2, 'OSR_class'] = 'tiivis'
housing.loc[housing['OSR'] > 10, 'OSR_class'] = 'väljä'
housing.loc[housing['OSR'] > 20, 'OSR_class'] = 'harva'
housing['OSR_ND_class'] = 'tehokas'
housing.loc[housing['OSR_ND'] > 2, 'OSR_ND_class'] = 'tiivis'
housing.loc[housing['OSR_ND'] > 10, 'OSR_ND_class'] = 'väljä'
housing.loc[housing['OSR_ND'] > 20, 'OSR_ND_class'] = 'harva'

# select plot type
osr_ve = st.radio("Väljyysluokittelun mittakaava", ('Tonttiväljyys', 'Naapuruston väljyys'))

if osr_ve == 'Tonttiväljyys':
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
    fig_dens1 = plot_with_osr(housing)
    with plot_spot:
        st.plotly_chart(fig_dens1, use_container_width=True)
else:
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
    fig_dens2 = plot_with_osr_nd(housing)
    with plot_spot:
        st.plotly_chart(fig_dens2, use_container_width=True)

# expl container
with st.expander("Selitteet", expanded=False):
    # describe_table
    st.markdown('Tilastotaulukko (asuinrakennukset)')
    des = housing.drop(columns=['uID','rakennusvuosi']).describe()
    st.dataframe(des)
    # expl
    selite = '''
    FSI = floor space index = tonttitehokkuus e<sub>t</sub> (ympyrän koko kuvaa rakennuksen kerrosalaa)<br>
    GSI = ground space index = rakennetun alueen suhde morfologiseen tonttiin <br>
    OSR = open space ratio = tonttiväljyys eli väljyysluku r<sub>t</sub> (rakentamattoman alueen suhde kerrosalaan tontilla)<br>
    OSR_ND = open space ratio = naapuruston väljyys (naapurustotonttien väjyyslukujen keskiarvo)<br>
    <p style="font-family:sans-serif; color:Dimgrey; font-size: 12px;">
    '''
    soveltaen = '''
    Soveltaen:<br>
     Berghauser Pont, Meta, and Per Haupt. 2021. Spacematrix: Space, Density and Urban Form. Rotterdam: nai010 publishers.<br>
     Meurman, Otto-I. 1947. Asemakaavaoppi. Helsinki: Rakennuskirja.<br>
    Morfologinen tontti on rakennuksen ympärillä oleva vapaa alue (max 100m) polygoni tesselaationa suhteessa ympäröiviin päärakennuksiin (piharakennuksia ei huomioita).
    Tämä tapa on katsottu soveltuvan ympäristön tehokkuuden laskemiseen juridisia tonttirajoja paremmin, mm. koska yhtiömuotoisilla tontteilla voi olla useampi rakennus.
    Naapurusto on määritetty käsittävän naapuritontit kahden asteen syvyydellä (rajanaapuritontit ja niiden rajanaapurit).
    Laskennat on toteutettu python-koodikirjastolla <a href="http://docs.momepy.org/en/stable/user_guide/elements/tessellation.html" target="_blank">Momepy</a>
    </p>
    '''
    st.markdown(selite, unsafe_allow_html=True)
    cs1, cs2, cs3 = st.columns(3)
    cs1.latex(r'''
            OSR = r_{t} = \frac {1-GSI} {FSI}
            ''')  # https://katex.org/docs/supported.html

    st.markdown(soveltaen, unsafe_allow_html=True)

    cita1 = '''
    <p style="font-family:sans-serif; color:Dimgrey; font-size: 12px;">
    Väljyysluokittelun raja-arvot:<br>
    tehokas: OSR_ND < 2, tiivis: OSR_ND < 10, väljä: OSR_ND < 20, harva: OSR_ND > 20 <br>
    O-I Meurman esitti Asemakaavaoppi -kirjassaan, että väljyysluvun tulisi kerrostaloalueilla olla vähintään 2-3 ja pientaloalueilla 7-8 (Meurman 1947, s. 226)
    </p>
    '''
    st.markdown(cita1, unsafe_allow_html=True)

st.markdown('-----')
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
        Kartalla visualisoitu vain nomogrammin kohteet. Arvot laskettu huomioiden kaikki rakennustyypit (kts. selitteet).
        </p>
        '''
    st.markdown(mapnote1, unsafe_allow_html=True)
    # save
    raks = density_data.drop(columns='uID').to_csv().encode('utf-8')
    st.download_button(label="Tallenna rakennukset CSV:nä", data=raks, file_name=f'rakennukset_{pno_nimi}.csv',
                       mime='text/csv')

footer_title = '''
---
:see_no_evil: **Naked Density Project**
[![MIT license](https://img.shields.io/badge/License-MIT-yellow.svg)](https://lbesson.mit-license.org/) 
'''
st.markdown(footer_title)
footer_text = '''
<p style="font-family:sans-serif; color:Dimgrey; font-size: 12px;">
Naked Density Projekti on osa <a href="https://github.com/teemuja" target="_blank">Teemu Jaman</a> väitöskirjatutkimusta Aalto Yliopistossa.
Projektissa tutkitaan maankäytön tehokkuuden ja kaupunkirakenteen fyysisten piirteiden
vaikutuksia palveluiden kehittymiseen data-analytiikan ja koneoppimisen avulla.
</p>
'''
st.markdown(footer_text, unsafe_allow_html=True)

#jepjep