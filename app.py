import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import time

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By

# Configuration des URLs et des colonnes spécifiques demandées
CONFIG_SCRAPING = [
    {"label": "Chiens", "url": "https://sn.coinafrique.com/categorie/chiens?page=", "cols": ["nom", "prix", "adresse", "image_lien"]},
    {"label": "Moutons", "url": "https://sn.coinafrique.com/categorie/moutons?page=", "cols": ["Nom", "prix", "adresse", "image_ln"]},
    {"label": "Poules, Lapins et Pigeons", "url": "https://sn.coinafrique.com/categorie/poules-lapins-et-pigeons?page=", "cols": ["details", "prix", "adresse", "image_lien"]},
    {"label": "Autres Animaux", "url": "https://sn.coinafrique.com/categorie/autres-animaux?page=", "cols": ["nom", "prix", "adresse", "image_lien"]}
]

def get_bs4_data(url_base, nb_pages, col_names):
    results = []
    headers = {"User-Agent": "Mozilla/5.0"}
    
    for p in range(1, nb_pages + 1):
        try:
            res = requests.get(f"{url_base}{p}", headers=headers, timeout=10)
            soup = BeautifulSoup(res.text, 'html.parser')
            cards = soup.find_all('div', class_='col s6 m4 l3')
            
            for card in cards:
                try:
                    # Extraction brute basée sur la position des éléments dans la carte
                    d_nom = card.find('p', class_='ad__card-description').text.strip()
                    d_prix = card.find('p', class_='ad__card-price').text.strip()
                    d_ads = card.find('p', class_='ad__card-location').text.strip()
                    d_img = card.find('img', class_='ad__card-img')['src']
                    
                    # On mappe dynamiquement sur les noms de colonnes demandés
                    results.append({
                        col_names[0]: d_nom,
                        col_names[1]: d_prix,
                        col_names[2]: d_ads,
                        col_names[3]: d_img
                    })
                except: continue
            time.sleep(0.2)
        except: break
    return pd.DataFrame(results)

def get_selenium_data(url_base, nb_pages, col_names):
    results = []
    
    # Configuration des options Chrome pour le mode "Sans Tête" (Headless)
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    # Initialisation du driver
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    for p in range(1, nb_pages + 1):
        driver.get(f"{url_base}{p}")
        time.sleep(2)  # Temps de chargement pour le JavaScript
        
        # On récupère toutes les "cards" d'annonces
        cards = driver.find_elements(By.CLASS_NAME, 'col.s6.m4.l3')
        
        for card in cards:
            try:
                # Extraction via Selenium
                d_nom = card.find_element(By.CLASS_NAME, 'ad__card-description').text
                d_prix = card.find_element(By.CLASS_NAME, 'ad__card-price').text
                d_ads = card.find_element(By.CLASS_NAME, 'ad__card-location').text
                d_img = card.find_element(By.CLASS_NAME, 'ad__card-img').get_attribute('src')
                
                results.append({
                    col_names[0]: d_nom,
                    col_names[1]: d_prix,
                    col_names[2]: d_ads,
                    col_names[3]: d_img
                })
            except:
                continue
    
    driver.quit()
    return pd.DataFrame(results)
        
# --- INTERFACE STREAMLIT ---
st.set_page_config(page_title="Scraper Industriel CoinAfrique", layout="wide")
st.title("🚀 Extracteur Automatique Multi-Sources")

# Barre latérale pour les contrôles
with st.sidebar:
    st.header("Paramètres Globaux")
    methode = st.selectbox("Méthode de Scraping", ["BeautifulSoup", "Selenium", "WebScraping"])
    nb_pages = st.number_input("Nombre de pages (0 à 100)", min_value=0, max_value=100, value=1)
    lancer_btn = st.button("Lancer le scraping global")
    
    st.divider()
    
    webscraper_btn = st.button("Web Scrapper")
    dashboard_btn = st.button("Dashboard")
    
    st.divider()
    
    # Nouveau bouton pour afficher la section évaluation
    evaluation_btn = st.button("Formulaire d'évaluation")

if lancer_btn:
    if nb_pages == 0:
        st.warning("Veuillez choisir un nombre de pages supérieur à 0.")
    else:
        # Boucle sur chaque configuration d'URL
        for config in CONFIG_SCRAPING:
            st.subheader(f"📊 Résultats pour : {config['label']}")
            
            with st.spinner(f"Extraction de {config['label']}..."):
                if methode == "BeautifulSoup":
                    df = get_bs4_data(config['url'], nb_pages, config['cols'])
                else:
                  df = get_selenium_data(config['url'], nb_pages, config['cols'])
                    # print(df)
    
                if not df.empty:
                    st.write(f"✅ {len(df)} annonces trouvées.")
                    st.dataframe(df, use_container_width=True)
                    
                    # Bouton de téléchargement spécifique à ce DataFrame
                    csv = df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label=f"📥 Télécharger CSV ({config['label']})",
                        data=csv,
                        file_name=f"{config['label'].lower().replace(' ', '_')}.csv",
                        mime='text/csv',
                        key=config['label'] # Clé unique pour Streamlit
                    )
                else:
                    st.error(f"Aucune donnée récupérée pour {config['label']}.")
            
            st.divider() # Ligne de séparation visuelle entre les catégories
            
# définir quelques styles liés aux box
st.markdown('''<style> .stButton>button {
    font-size: 12px;
    height: 3em;
    width: 18em;
}</style>''', unsafe_allow_html=True)

if 'show_webscraper' not in st.session_state:
    st.session_state.show_webscraper = False

if webscraper_btn:
    st.session_state.show_webscraper = True

# Fonction de loading des données
def load_(dataframe, title, key) :
    st.markdown("""
    <style>
    div.stButton {text-align:center}
    </style>""", unsafe_allow_html=True)

    if st.button(title,key):
      
        st.subheader('Display data dimension')
        st.write('Data dimension: ' + str(dataframe.shape[0]) + ' rows and ' + str(dataframe.shape[1]) + ' columns.')
        st.dataframe(dataframe)

if st.session_state.show_webscraper:
  for i in range(1,5): 
    load_(pd.read_csv(f"data/coinafrique_animaux{i}.csv"), f"Coin Afrique Animaux {i}", f"{i}")
    

if 'page' not in st.session_state:
    st.session_state.page = False
    
if dashboard_btn:
    st.session_state.page = True
    
def get_combined_data():
  all_dfs = []
  for i in range(1, 5):
    try:
      df = pd.read_csv(f"data/coinafrique_animaux{i}.csv")
      # Nettoyage rapide du prix pour les graphiques
      if 'prix' in df.columns or 'Prix' in df.columns:
        p_col = 'prix' if 'prix' in df.columns else 'Prix'
        df['prix_clean'] = df[p_col].str.replace(r'\D', '', regex=True).fillna(0)
        df['prix_clean'] = pd.to_numeric(df['prix_clean'], errors='coerce').fillna(0)
      
      # On ajoute une colonne pour identifier la catégorie dans le dashboard
      categories = ["Chiens", "Moutons", "Volailles", "Autres"]
      df['Categorie'] = categories[i-1]
      all_dfs.append(df)
    except:
      continue
  return pd.concat(all_dfs, ignore_index=True) if all_dfs else pd.DataFrame()
    
if st.session_state.page:
  df_dash = get_combined_data()

  if not df_dash.empty:
    # 1. Ligne de KPIs
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Annonces", len(df_dash))
    col2.metric("Prix Moyen (CFA)", f"{int(df_dash['prix_clean'].mean()):,}")
    col3.metric("Nombre de Catégories", df_dash['Categorie'].nunique())

    st.divider()

    # 2. Graphiques simples
    c1, c2 = st.columns(2)

    with c1:
      st.subheader("Répartition par Catégorie")
      # Graphique à barres : Nombre d'annonces par catégorie
      cat_counts = df_dash['Categorie'].value_counts()
      st.bar_chart(cat_counts)

    with c2:
      st.subheader("Prix Moyen par Catégorie")
      # Prix moyen par catégorie
      avg_price = df_dash.groupby('Categorie')['prix_clean'].mean()
      st.area_chart(avg_price)

    # 3. Tableau récapitulatif
    st.subheader("Top 10 des annonces les plus chères")
    st.table(df_dash.nlargest(10, 'prix_clean')[['Categorie', 'prix_clean', 'adresse']])
  else:
    st.error("Aucune donnée disponible pour le dashboard. Veuillez d'abord scraper ou charger les fichiers CSV.")

else:
  # Affichez ici votre code précédent pour le Scraping et le bouton webscraper_btn
  if webscraper_btn:
      st.session_state.show_webscraper = True
  
  # ... reste du code de chargement (load_) ...
  

# --- Logique d'affichage du formulaire ---
if evaluation_btn:
    st.title("📋 Évaluation de l'application")
    st.markdown("""
    Votre avis nous intéresse ! Veuillez choisir l'une des plateformes ci-dessous 
    pour remplir le formulaire de satisfaction.
    """)
    
    # Création de deux colonnes pour les boutons de redirection
    col_kobo, col_google = st.columns(2)
    
    with col_kobo:
        st.info("Plateforme KoboToolbox")
        st.link_button("Accéder au lien Kobo", "https://ee.kobotoolbox.org/x/cTV7iqiT", use_container_width=True)
        
    with col_google:
        st.success("Plateforme Google Forms")
        st.link_button("Accéder au Google Form", "https://docs.google.com/forms/d/e/1FAIpQLScRIqM6tJH_jC8cJyXSuYRzmlMfoQgv8z94JNLNoREff51fvQ/viewform?usp=publish-editor", use_container_width=True)

    st.divider()
    st.caption("Merci pour votre temps et votre contribution.")