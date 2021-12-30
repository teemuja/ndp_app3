# ndp d3 app for smoooth rdm...
import streamlit as st
import plotly.express as px

from apis import pno_data
from apis import hri_data

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

# kuntascat
with st.expander(f"Kuntagraafi {kunta}"):
    featlist = kuntadata.columns.tolist()
    default_x = featlist.index('Rakennukset yhteensä')
    default_y = featlist.index('Asukkaat yhteensä')
    col1,col2 = st.columns([1,1])
    xaks = col1.selectbox('Valitse X-akselin tieto', featlist, index=default_x)
    yaks = col2.selectbox('Valitse Y-akselin tieto', featlist, index=default_y)
    def scatplot1(df):
        scat1 = px.scatter(df, x=xaks, y=yaks, color='Postinumeroalueen nimi',
                           hover_name='Postinumeroalueen nimi')
        scat1.update_layout(legend={'traceorder': 'normal'})
        return scat1
    scat1 = scatplot1(kuntadata)
    st.plotly_chart(scat1, use_container_width=True)
    st.caption("[stat.fi](https://www.stat.fi/org/avoindata/paikkatietoaineistot/paavo.html)")

# prep
colormap_hri = {
    "Erilliset pientalot": "bisque",
    "Rivi- ja ketjutalot": "burlywood",
    "Asuinkerrostalot": "chocolate",
    "Vapaa-ajan asuinrakennukset": "goldenrod",
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

#plot
with st.expander("Rakennukset kartalla", expanded=True):
    plot = hri_data(pno_alue)
    lat = plot.unary_union.centroid.y
    lon = plot.unary_union.centroid.x
    fig = px.choropleth_mapbox(plot,
                               geojson=plot.geometry,
                               locations=plot.index,
                               color=plot['rakennustyyppi'].astype(str),
                               hover_name="tarkenne",
                               hover_data=['kerrosala','kerrosluku','rakennusvuosi'],
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
        # download button
        raks_csv = plot.to_csv().encode('utf-8')
        st.download_button(label="Lataa rakennukset CSV-tiedostona", data=raks_csv,
                           file_name=f'rakennukset_{pno_nimi}.csv', mime='text/csv')
    st.caption("[hsy.fi](https://www.hsy.fi/ymparistotieto/avoindata/avoin-data---sivut/paakaupunkiseudun-rakennukset/)")

with st.expander("Tehokkuus-graafit", expanded=True):
    # get rid off outliers..
    high_limit = plot['kerrosala'].quantile(0.99)
    #low_limit = plot['kerrosala'].quantile(0.01)
    plot_out = plot[(plot['kerrosala'] < high_limit) & (plot['kerrosala'] > 0)]
    fig_h = px.histogram(plot_out,
                         title=f'{pno_nimi} - Kerrosalahistogrammi',
                         x='kerrosala', color="rakennustyyppi", barmode="overlay", nbins=10, histnorm='percent', #'probability density',
                         color_discrete_map=colormap_hri,
                         labels={
                             "kerrosala": "Eri kokoisten rakennusten jakauma",
                             "color": "rakennustyyppi"
                         }
                         )
    st.plotly_chart(fig_h, use_container_width=True)

    def scatplot2(df):
        scat = px.scatter(df, title=f'{pno_nimi} - Rakennusten koko rakennusvuosittain',
                          x='rakennusvuosi', y='kerrosala', color='rakennustyyppi', log_y=True,
                          hover_name='tarkenne', color_discrete_map=colormap_hri)
        #scat.update_layout(legend={'traceorder': 'normal'})
        return scat
    scat_ = plot[(plot['rakennusvuosi'] < 2022) & (plot['rakennusvuosi'] > 1850)]
    scat2 = scatplot2(scat_)
    st.plotly_chart(scat2, use_container_width=True)

footer_title = '''
---
:see_no_evil: **Naked Density Project**
[![MIT license](https://img.shields.io/badge/License-MIT-yellow.svg)](https://lbesson.mit-license.org/) 
'''
st.markdown(footer_title)
footer_fin = '<p style="font-family:sans-serif; color:Dimgrey; font-size: 12px;">\
        Naked Density Projekti on osa Teemu Jaman väitöskirjatutkimusta Aalto Yliopistossa. \
        Projektissa tutkitaan maankäytön tehokkuuden ja kaupunkirakenteen fyysisten piirteiden\
        vaikutuksia palveluiden kehittymiseen data-analytiikan ja koneoppimisen avulla.\
        </p>'
st.markdown(footer_fin, unsafe_allow_html=True)
