# ndp d3 app for smoooth rdm...
import streamlit as st
import plotly.express as px

from apis import pno_data
from apis import hri_data
from apis import densities

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

# page title
header_title = '''
:see_no_evil: **Naked Density Project**
'''

st.subheader(header_title)
st.markdown("""---""")
st.title('Data Paper #0.1')
st.caption('Digitaalinen datapaperi tutkimustiedon hallintaan')
st.title(':point_down:')

# valitsimet
c1, c2 = st.columns(2)
kuntalista = ['Espoo','Helsinki','Vantaa']
default_kunta = kuntalista.index('Espoo')
kunta = c1.selectbox('Valitse kaupunki', kuntalista, index=default_kunta)
# hae pno data..
kuntadata = pno_data(kunta,2021)
pno_lista = kuntadata['Postinumeroalueen nimi'].tolist()
# lisää pno_lista valikkoon
pno_nimi = c2.selectbox('Valitse postinumeroalue', pno_lista)

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
pno_alue = kuntadata[kuntadata['Postinumeroalueen nimi'] == pno_nimi]
data = hri_data(pno_alue)

with st.expander("Kerrosalagraafit", expanded=True):
    # get rid off outliers..
    high_limit = data['kerrosala'].quantile(0.99)
    #low_limit = data['kerrosala'].quantile(0.01)
    # plot 1
    plot_kem = data[(data['kerrosala'] < high_limit) & (data['kerrosala'] > 0)]
    fig_kem = px.histogram(plot_kem,
                         title=f'{pno_nimi} - Kerrosalahistogrammi',
                         x='kerrosala', color="rakennustyyppi", barmode="overlay", nbins=10, histnorm='percent', #'probability density',
                         color_discrete_map=colormap_hri,
                         labels={
                             "kerrosala": "Eri kokoisten rakennusten jakauma",
                             "color": "Rakennustyyppi"
                         }
                         )
    st.plotly_chart(fig_kem, use_container_width=True)
    # plot 2
    plot_yrs = data[(data['rakennusvuosi'] < 2022) & (data['rakennusvuosi'] > 1800)]
    fig_yrs = px.scatter(plot_yrs, title=f'{pno_nimi} - Rakennusten koko rakennusvuosittain',
                          x='rakennusvuosi', y='kerrosala', color='rakennustyyppi', log_y=True,
                          hover_name='tarkenne', color_discrete_map=colormap_hri)
    st.plotly_chart(fig_yrs, use_container_width=True)

with st.expander("Tehokkuusgraafi", expanded=False):
    density_data = densities(data)
    # select only housing types & drop nan values
    showlist = ["Erilliset pientalot","Rivi- ja ketjutalot","Asuinkerrostalot"]
    housing = density_data[density_data.rakennustyyppi.isin(showlist)]
    # plot
    fig_dens = px.scatter(housing, title=f'{pno_nimi} - Tehokkuusmatriisi',
                         x='GSI', y='FSI', color='rakennustyyppi', size='kerrosala', log_y=False,
                         hover_name='tarkenne', hover_data=['rakennusvuosi','kerrosala','kerrosluku','FSI','GSI','OSR'],
                         color_discrete_map=colormap_hri)
    fig_dens.update_layout(legend={'traceorder': 'normal'})
    st.plotly_chart(fig_dens, use_container_width=True)
    selite = '''
    FSI = floor space index = tehokkuusluku   
    GSI = ground space index = peitto  
    OSR = open space ratio = väljyysluku  
    soveltaen: Berghauser Pont, Meta, and Per Haupt. 2021. Spacematrix: Space, Density and Urban Form. Rotterdam: nai010 publishers.
    '''
    st.markdown(selite)

#map plot
with st.expander("Rakennukset kartalla", expanded=False):
    plot = density_data
    lat = plot.unary_union.centroid.y
    lon = plot.unary_union.centroid.x
    fig = px.choropleth_mapbox(plot,
                               geojson=plot.geometry,
                               locations=plot.index,
                               color=plot['rakennustyyppi'].astype(str),
                               hover_name="tarkenne",
                               hover_data=['rakennusvuosi','kerrosala','kerrosluku','FSI','GSI','OSR'],
                               mapbox_style="carto-positron",
                               labels={"color": "rakennustyyppi"},
                               color_discrete_map=colormap_hri,
                               center={"lat": lat, "lon": lon},
                               zoom=13,
                               opacity=0.8,
                               width=1200,
                               height=700
                               )
    fig.update_layout(title_text="Plot", margin={"r": 0, "t": 0, "l": 0, "b": 0}, height=700)

    # generate plot
    with st.spinner('Kokoaa rakennuksia...'):
        st.plotly_chart(fig, use_container_width=True)

    st.caption("data: [hsy.fi](https://www.hsy.fi/ymparistotieto/avoindata/avoin-data---sivut/paakaupunkiseudun-rakennukset/)")
    # download button
    raks_csv = plot.drop(columns='uID').to_csv().encode('utf-8')
    st.download_button(label="Lataa rakennukset CSV-tiedostona", data=raks_csv,
                       file_name=f'rakennukset_{pno_nimi}.csv', mime='text/csv')

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
