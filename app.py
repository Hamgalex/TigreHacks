import requests
import pandas as pd
from requests_html import HTML
from requests_html import HTMLSession
import html
from bs4 import BeautifulSoup
import numpy as np
import spacy
from spacy.lang.es.stop_words import STOP_WORDS
import folium
from folium import Choropleth, Circle, Marker
from folium.plugins import HeatMap, MarkerCluster
from IPython.display import display
import streamlit as st
from streamlit_folium import st_folium

def obtener_codigo(enlace):
  try:
    return HTMLSession().get(enlace).text
  except requests.exceptions.RequestException as e:
    print(e)

def obtener_noticias(enlace):
  lista_datos = []
  respuesta = obtener_codigo(enlace)
  soup = BeautifulSoup(respuesta, "xml")
  elementos = soup.find_all('item')
  for elemento in elementos:
    id = elemento.guid.string
    fechaPub = elemento.pubDate.string
    titulo = html.unescape(elemento.title.string)
    descripcion = html.unescape(elemento.description.string)
    contenido = html.unescape(elemento.encoded.string)
    enlace = elemento.link.string
    entrada = {'id': id, 'fechaPub': fechaPub, 'titulo': titulo,
               'descripcion': descripcion, 'contenido': contenido,
               'enlace': enlace}
    lista_datos.append(entrada)
  
  return lista_datos


def obtener_colonias():
  raw_dataset = pd.read_csv("datasets/colsnuevoleon.csv",encoding='utf-8')
  latlong=raw_dataset.iloc[:,3:].values
  calle=raw_dataset.iloc[:,2].values
  dic=dict(zip(calle,latlong))
  #st.dataframe(raw_dataset)
  return dic


def obtener_localizaciones(datos,dic):
  
  coords=[]
  #print("XD")
  #print(datos)
  for entrada in datos['contenido']:
    nlp = spacy.load('es_core_news_sm')
    texto = BeautifulSoup(entrada).getText()
    doc = nlp(str(texto))
    ents = [i for i in doc.ents if i.label_ == 'LOC']
    bandera=False
    


    for palabra in ents:
      palabra=str(palabra)
      palabra=palabra.lower()
      palabra=palabra.replace("á","a")
      palabra=palabra.replace("é","e")
      palabra=palabra.replace("í","i")
      palabra=palabra.replace("ó","o")
      palabra=palabra.replace("ú","u")

      #print(palabra)
      if dic.get(palabra) is not None:
        if np.isnan(dic[palabra][0]):
          continue
        
        #mc.add_child(Marker([dic[palabra][0], dic[palabra][1]]))
        coords=coords+[dic[palabra][0], dic[palabra][1]]
        #print(dic[palabra][0])
        #print(dic[palabra][1])

        #mapa.add_child(mc)
        bandera=True
        break

      if bandera==True:
        break
  return coords

def mostrar_mapa(coords):
  mapa = folium.Map(location=[25.6750,-100.31847], tiles='cartodbpositron',
                    zoom_start=13)
  
  mc = MarkerCluster()
  coords=np.asarray(coords)
  coords = coords.reshape(-1, 2)
  for i in coords:
    mc.add_child(Marker(i))
    mapa.add_child(mc)
  
  st_data = st_folium(mapa, width=725)


def display_time_filters():
    lista_mes=['ENE','FEB','MAR','ABR','MAY','JUN','JUL','AGO','SEP','OCT','NOV','DIC']
    mes = st.sidebar.selectbox('Mes', lista_mes,  index=4)
    dia = st.sidebar.selectbox('Día', list(range(1, 31)),index=26)
    st.header(f'Mapa delictivo {dia}/{mes}/2023')
    return dia, mes

def main():
  lista_datos = obtener_noticias("https://elporvenir.mx/feedgooglenews/justicia")
  lista_datos += obtener_noticias("https://web.archive.org/web/20230514221533/" +
                                  "https://elporvenir.mx/feedgooglenews/justicia")
  lista_datos += obtener_noticias("https://web.archive.org/web/20230411062628/" +
                                  "https://elporvenir.mx/feedgooglenews/justicia")
  datos = pd.DataFrame.from_records(lista_datos)
  datos[['diasemana','dia','mes','ano','hora','hora2']] = datos['fechaPub'].str.split(', |\s',expand=True)
  
  with st.form("my_form"):
    dia,mes=display_time_filters()
  
  
    datos=datos.loc[(datos['dia'] == str(dia)) &(datos['mes']==mes) ]
    
    dic=obtener_colonias()
    
    coords=obtener_localizaciones(datos,dic)
    #st.write(coords)
    mostrar_mapa(coords)
    submitted = st.form_submit_button("Cargar Mapa")

if __name__ == "__main__":
    main()