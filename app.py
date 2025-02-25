# Import des bibliothèques nécessaires  
import streamlit as st  
import pandas as pd  
import plotly.express as px  
import matplotlib.pyplot as plt  
from wordcloud import WordCloud  
from PIL import Image  
import base64  
from io import BytesIO
import re

# Chargement des données au format Parquet  
# On charge les données des vins et des clients à partir des fichiers parquet.
df = pd.read_parquet("wine_dataset.parquet")  
df_client = pd.read_parquet("client_wine.parquet")  

# Configuration de l'application Streamlit  
st.set_page_config(page_title="Analyse des Vins", layout="wide")

# Charger l'image du logo  
logo = Image.open("logo.jpg")

# Définir la taille maximale du logo (ajuster selon vos besoins)
max_size = (200, 100)  # Largeur maximale de 200 pixels, hauteur maximale de 100 pixels

# Redimensionner le logo en conservant les proportions  
logo.thumbnail(max_size)

# Convertir l'image en base64  
buffered = BytesIO()
logo.save(buffered, format="JPEG")  # Vous pouvez changer le format si nécessaire  
img_str = base64.b64encode(buffered.getvalue()).decode()

# Afficher le logo dans la barre latérale  
st.sidebar.image(f"data:image/jpeg;base64,{img_str}", use_container_width=True)

# Menu latéral pour naviguer entre les sections  
menu = st.sidebar.radio("Menu", ["Accueil", "Analyse", "Définitions"])

# --- ONGLET ACCUEIL ---
if menu == "Accueil":
    st.markdown("<h1 style='text-align: center;'>Bienvenue dans le Domaine des Croix</h1>", unsafe_allow_html=True)
    
    # Message de bienvenue  
    st.write("""
    Bienvenue dans le domaine des Croix, un véritable sanctuaire pour les amateurs de vin. 
    Ici, nous nous consacrons à la production de vins d'exception, issus de cépages soigneusement sélectionnés. 
    Notre vignoble s'étend sur des collines ensoleillées, où chaque grappe est cultivée avec passion et expertise.
    """)
    
    # Affichage d'une image du vignoble  
    st.image("image.webp", caption="Vignoble du Domaine des Croix", use_container_width=True)

# --- ONGLET ANALYSE ---
elif menu == "Analyse":
    st.title("Analyse des vins et estimation du prix")
    
    # Filtrage global dans la barre latérale  
    st.sidebar.subheader("Filtres Globaux")

    # Filtre par pays avec une sélection multiple  
    st.sidebar.markdown("### Sélectionnez des pays")
    countries = ['Tous'] + df['country'].unique().tolist()
    selected_countries = st.sidebar.multiselect(
        "Choisissez un ou plusieurs pays",
        options=countries  
    )
    
    # Filtre par cépage avec une sélection multiple  
    st.sidebar.markdown("### Sélectionnez des cépages")
    varieties = ['Tous'] + df['variety'].unique().tolist()
    selected_varieties = st.sidebar.multiselect(
        "Choisissez un ou plusieurs cépages",
        options=varieties  
    )
    
    # Filtre pour la plage de prix  
    st.sidebar.markdown("### Plage de Prix")
    price_range = st.sidebar.slider(
        "Sélectionnez la plage de prix",
        min_value=int(df['price'].min()),
        max_value=int(df['price'].max()),
        value=(int(df['price'].min()), int(df['price'].max())),
        step=1  
    )
    
    # Filtre pour la plage de points  
    st.sidebar.markdown("### Plage de Points")
    points_range = st.sidebar.slider(
        "Sélectionnez la plage de points",
        min_value=int(df['points'].min()),
        max_value=int(df['points'].max()),
        value=(int(df['points'].min()), int(df['points'].max())),
        step=1  
    )
    
    # Appliquer les filtres sur les données  
    filtered_df = df[
        (df['price'].between(price_range[0], price_range[1])) &
        (df['points'].between(points_range[0], points_range[1]))
    ]

    # Filtrer par pays si "Tous" n'est pas sélectionné  
    if "Tous" not in selected_countries:
        filtered_df = filtered_df[filtered_df['country'].isin(selected_countries)]

    # Filtrer par cépage si "Tous" n'est pas sélectionné  
    if "Tous" not in selected_varieties:
        filtered_df = filtered_df[filtered_df['variety'].isin(selected_varieties)]

    # --- METRIQUES GLOBALES ---
    st.subheader("Métriques générales")

    # Calcul des métriques sur les prix  
    price_metrics = {
        "Nombre total de vins": len(filtered_df),
        "Prix moyen des vins": filtered_df['price'].mean(),
        "Prix médian des vins": filtered_df['price'].median(),
        "Prix minimum des vins": filtered_df['price'].min(),
        "Prix maximum des vins": filtered_df['price'].max(),
        "Nombre de pays représentés": filtered_df['country'].nunique(),
    }

    # Calcul des métriques sur les points  
    points_metrics = {
        "Points moyen": filtered_df['points'].mean(),
        "Points médian": filtered_df['points'].median(),
        "Points minimum": filtered_df['points'].min(),
        "Points maximum": filtered_df['points'].max(),
        "Nombre de vins par points": len(filtered_df)
    }

    # Création d'un DataFrame pour afficher les métriques  
    metrics_df = pd.DataFrame({
        "Métriques": list(price_metrics.keys()) + list(points_metrics.keys()),
        "Valeurs": list(price_metrics.values()) + list(points_metrics.values())
    })

    # Affichage dynamique des métriques dans deux colonnes  
    col1, col2 = st.columns(2)
    with col1:
        st.dataframe(metrics_df)

    # --- RÉPARTITION DES CÉPAGES ---
    with col2:
        st.subheader("Répartition des cépages (Top 15)")
        top_grapes = filtered_df['variety'].value_counts().head(15).reset_index()
        top_grapes.columns = ['Cépage', 'Nombre de vins']  # Renommer les colonnes pour le graphique  
        fig_grapes = px.bar(top_grapes, x='Cépage', y='Nombre de vins', title="Top 15 des cépages", labels={'Cépage': 'Cépage', 'Nombre de vins': 'Nombre de vins'})
        st.plotly_chart(fig_grapes, use_container_width=True)

    # --- RÉPARTITION GÉOGRAPHIQUE DES VINS ---
    st.subheader("Répartition géographique des vins")
    
    # Compter le nombre de vins par pays pour la carte  
    country_counts = filtered_df['country'].value_counts().reset_index()
    country_counts.columns = ['country', 'count']

    # Créer une carte choroplèthe pour visualiser la répartition  
    fig_map = px.choropleth(
        country_counts,
        locations='country',
        locationmode='country names',
        color='count',
        title="Nombre de vins par pays",
        color_continuous_scale='Reds',
        labels={'count': 'Nombre de vins', 'country': 'Pays'}
    )
    
    # Mise à jour des axes pour permettre le zoom sur la carte  
    fig_map.update_geos(fitbounds="locations", visible=False)
    fig_map.update_layout(margin={"r":0,"t":40,"l":0,"b":0})  # Ajuster les marges  
    st.plotly_chart(fig_map, use_container_width=True)

    # --- ANALYSE DES PRIX PAR PAYS ---
    st.subheader("Analyse des prix par pays")
    top_countries = filtered_df['country'].value_counts().head(5).index  
    df_top_countries = filtered_df[filtered_df['country'].isin(top_countries)]
    
    # Histogramme de la distribution des prix par pays  
    fig_prices = px.histogram(df_top_countries, x='price', color='country', title="Distribution des prix par pays (Top 5)", labels={'price': 'Prix (€)', 'country': 'Pays'})
    fig_prices.update_traces(marker=dict(line=dict(width=1, color='black')))  # Ajouter bordure aux barres  
    fig_prices.update_layout(xaxis_title='Prix (€)', yaxis_title='Nombre de vins')  # Titre des axes  
    st.plotly_chart(fig_prices, use_container_width=True)

    # --- WORD CLOUD DES CÉPAGES ---
    st.subheader("Nuage de mots des cépages")
    if not filtered_df.empty:  # Vérifier si le DataFrame n'est pas vide  
        wordcloud = WordCloud(width=800, height=400, background_color='white').generate(' '.join(filtered_df['variety'].dropna()))
        plt.figure(figsize=(10,5))
        plt.imshow(wordcloud, interpolation='bilinear')
        plt.axis("off")
        st.pyplot(plt)
    else:
        st.warning("Aucun cépage à afficher dans le nuage de mots, veuillez ajuster les filtres.")

    # --- ESTIMATION DU PRIX POUR LE CLIENT ---
    st.subheader("Estimation du prix d'une bouteille de vin")

    # Sélection d'une bouteille dans le DataFrame client  
    wine_titles = df_client['title'].unique()
    selected_wine_title = st.selectbox("Choisissez une bouteille", options=wine_titles)

    # Affichage des caractéristiques de la bouteille choisie  
    selected_wine = df_client[df_client['title'] == selected_wine_title].iloc[0]
    st.write("### Caractéristiques de la bouteille sélectionnée")
    st.json(selected_wine.to_dict())  # Afficher les détails sous forme de JSON

    # Estimation basée sur les vins similaires à ceux de la bouteille sélectionnée  
    similar_wines = filtered_df[(filtered_df['country'] == selected_wine['country']) & (filtered_df['variety'] == selected_wine['variety'])]

    # Calcul du prix estimé si des vins similaires existent  
    if not similar_wines.empty:
        estimated_price = similar_wines['price'].median()
        st.metric("Prix estimé", f"{estimated_price:.2f} €")
        
        # Visualisation des prix similaires  
        fig_similar = px.histogram(similar_wines, x='price', title="Distribution des prix des vins similaires", labels={'price': 'Prix (€)'})
        fig_similar.add_vline(x=estimated_price, line_color='red', line_dash='dash', annotation_text='Prix estimé', annotation_position='top right')
        st.plotly_chart(fig_similar, use_container_width=True)
    else:
        st.warning("Pas assez de données pour estimer le prix.")

        # Comparaison des prix des bouteilles similaires  
    st.subheader("Comparaison des prix des bouteilles similaires")

    # Vérifiez que selected_wine est défini  
    if 'title' in selected_wine:
        # Extraire l'année de la bouteille sélectionnée à partir du titre en utilisant une regex  
        year_match = re.search(r'\d{4}', selected_wine['title'])  # Cherche une suite de 4 chiffres  
        if year_match:
            selected_year = year_match.group(0)  # On récupère la première occurrence trouvée  
        else:
            st.warning("Aucune année trouvée dans le titre de la bouteille sélectionnée.")
            selected_year = None  # Réinitialiser selected_year s'il n'y a pas d'année trouvée  
    else:
        st.warning("Aucun vin sélectionné.")
        selected_year = None

    if selected_year:
        # Comparer avec les vins de la même année dans le DataFrame  
        same_year_wines = df[df['title'].str.contains(selected_year)]

        if not same_year_wines.empty:
            average_year_price = same_year_wines['price'].mean()  # Calculer le prix moyen  
            st.metric("Prix moyen des vins de l'année " + selected_year, f"{average_year_price:.2f} €")  # Afficher la métrique

            # Graphique de la distribution des prix des vins de la même année  
            fig_year = px.histogram(same_year_wines, x='price', title=f"Distribution des prix des vins de l'année {selected_year}", labels={'price': 'Prix (€)'})
            fig_year.add_vline(x=estimated_price, line_color='red', line_dash='dash', annotation_text='Prix estimé', annotation_position='top right')
            st.plotly_chart(fig_year, use_container_width=True)
        else:
            st.warning(f"Aucun vin trouvé pour l'année {selected_year}.")

    # Comparer avec les vins du même pays  
    same_country_wines = df[df['country'] == selected_wine['country']]

    if not same_country_wines.empty:
        average_country_price = same_country_wines['price'].mean()  # Calculer le prix moyen  
        st.metric("Prix moyen des vins du pays " + selected_wine['country'], f"{average_country_price:.2f} €")  # Afficher la métrique

        # Graphique de la distribution des prix des vins du même pays  
        fig_country = px.histogram(same_country_wines, x='price', title=f"Distribution des prix des vins du pays : {selected_wine['country']}", labels={'price': 'Prix (€)'})
        fig_country.add_vline(x=estimated_price, line_color='red', line_dash='dash', annotation_text='Prix estimé', annotation_position='top right')
        st.plotly_chart(fig_country, use_container_width=True)
    else:
        st.warning(f"Aucun vin trouvé pour le pays {selected_wine['country']}.")

    # Comparer avec les vins du même cépage  
    same_variety_wines = df[df['variety'] == selected_wine['variety']]

    if not same_variety_wines.empty:
        average_variety_price = same_variety_wines['price'].mean()  # Calculer le prix moyen  
        st.metric("Prix moyen des vins du cépage " + selected_wine['variety'], f"{average_variety_price:.2f} €")  # Afficher la métrique

        # Graphique de la distribution des prix des vins du même cépage  
        fig_variety = px.histogram(same_variety_wines, x='price', title=f"Distribution des prix des vins du cépage : {selected_wine['variety']}", labels={'price': 'Prix (€)'})
        fig_variety.add_vline(x=estimated_price, line_color='red', line_dash='dash', annotation_text='Prix estimé', annotation_position='top right')
        st.plotly_chart(fig_variety, use_container_width=True)
    else:
        st.warning(f"Aucun vin trouvé pour le cépage {selected_wine['variety']}.")

# --- ONGLET DÉFINITIONS ---
elif menu == "Définitions":
    st.title("Définitions des colonnes du DataFrame")
    
    st.markdown("""
    1. **country** : Le pays d'origine du vin.
    2. **description** : Une description des arômes, saveurs et caractéristiques du vin.
    3. **designation** : La désignation spécifique du vin, souvent liée au vignoble ou à une cuvée spéciale.
    4. **points** : La note attribuée au vin, souvent sur une échelle de 0 à 100.
    5. **price** : Le prix du vin en dollars.
    6. **province** : La province ou région principale où le vin est produit.
    7. **region_1** : Une région plus spécifique à l'intérieur de la province où le vin est produit.
    8. **region_2** : Une sous-région encore plus spécifique, si applicable.
    9. **taster_name** : Le nom de l'expert qui a goûté et évalué le vin.
    10. **taster_twitter_handle** : Le pseudo Twitter de l'expert.
    11. **title** : Le nom complet du vin, comprenant l'année, le nom du vin et la région.
    12. **variety** : Le cépage ou l'assemblage de cépages utilisé(s) pour produire le vin.
    13. **winery** : Le nom du producteur de vin (château ou domaine viticole).
    """)
