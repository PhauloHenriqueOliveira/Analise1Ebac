1. Contexto
Escreva uma breve descrição do problema.

2. Pacotes e bibliotecas
[ ]
!pip3 install geopandas
!pip install tabula-py PyPDF2
!pip install contextily

import json

import tabula
import PyPDF2
from PyPDF2 import PdfReader
import pandas as pd
import geopy
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
from shapely.geometry import Point
from shapely.geometry import Polygon
import numpy as np
import geopandas as gpd
import contextily as ctx
import matplotlib.pyplot as plt
import seaborn as sns
3. Exploração de dados
[ ]
!wget -q "https://raw.githubusercontent.com/andre-marcos-perez/ebac-course-utils/main/dataset/deliveries.json" -O deliveries.json


with open('deliveries.json', mode='r', encoding='utf8') as file:
  data = json.load(file)

[ ]
deliveries_df = pd.DataFrame(data)

deliveries_df.head()


hub_origin_df = pd.json_normalize(deliveries_df["origin"])
hub_origin_df
[ ]
deliveries_df = pd.merge(left=deliveries_df, right=hub_origin_df, how='inner', left_index=True, right_index=True)


deliveries_df = deliveries_df.drop("origin", axis=1)


deliveries_df = deliveries_df[["name", "region", "lng", "lat", "vehicle_capacity", "deliveries"]]
deliveries_df.rename(columns={"lng": "hub_lng", "lat": "hub_lat"}, inplace=True)
deliveries_df
[ ]
deliveries_exploded_df = deliveries_df[["deliveries"]].explode("deliveries")
deliveries_exploded_df
[ ]
deliveries_normalized_df = pd.concat([
  pd.DataFrame(deliveries_exploded_df["deliveries"].apply(lambda record: record["size"])).rename(columns={"deliveries": "delivery_size"}),
  pd.DataFrame(deliveries_exploded_df["deliveries"].apply(lambda record: record["id"])).rename(columns={"deliveries":"delivery_id"}),
  pd.DataFrame(deliveries_exploded_df["deliveries"].apply(lambda record: record["point"]["lng"])).rename(columns={"deliveries": "delivery_lng"}),
  pd.DataFrame(deliveries_exploded_df["deliveries"].apply(lambda record: record["point"]["lat"])).rename(columns={"deliveries": "delivery_lat"}),
], axis= 1)

deliveries_normalized_df
[ ]
deliveries_df = deliveries_df.drop("deliveries", axis=1)


deliveries_df = pd.merge(left=deliveries_df, right=deliveries_normalized_df, how='right', left_index=True, right_index=True)
deliveries_df.reset_index(inplace=True, drop=True)

deliveries_df
[ ]
deliveries_df.shape
(636149, 9)
[ ]
deliveries_df.info()
[ ]
deliveries_df.isna().sum()
[ ]
deliveries_df.nunique()
[ ]
len(deliveries_df)
[ ]
deliveries_df.head(n=5)
[ ]
deliveries_df.dtypes
[ ]
deliveries_df.select_dtypes("object").describe().transpose()
[ ]
deliveries_df.drop( ["name", "region"], axis=1 ).select_dtypes('int64').describe().transpose()
[ ]
deliveries_df.isna().any()
[ ]
deliveries_df.head()
[ ]
deliveries_por_regiao = deliveries_df.groupby('region').agg({'delivery_size': 'mean'})
print(deliveries_por_regiao)

Aqui podemos observar que o volume das entregas é diferente de uma região da outra, principalmente em df-1 que se mostra ser bastante volumosa, podendo assumir que talvez seja necessario aumentar a frota futuramente

4. Manipulação
[ ]
mapeamento_regiao = {
    'df-0': 'Região Norte/Leste',
    'df-1': 'Região Centro',
    'df-2': 'Região Sul/Oeste'
}


deliveries_df['region_descritiva'] = deliveries_df['region'].map(mapeamento_regiao)
adicionando essa coluna fica mais facil de entender quais os padrões de entregas de cada hub, mais para frente terá um mapa para melhor visualização

5. Visualização
[ ]
delivery_size_stats = deliveries_df.groupby('vehicle_capacity')['delivery_size'].agg(['mean', 'median', 'std'])

print("Estatísticas de tamanho de entrega para cada capacidade de veículo:")
print(delivery_size_stats)

plt.figure(figsize=(10, 6))
sns.histplot(data=deliveries_df, x='delivery_size', kde=True, bins=20)
plt.title('Distribuição do Tamanho das Entregas')
plt.xlabel('Tamanho da Entrega')
plt.ylabel('Frequência')
plt.grid(axis='y', linestyle='--', alpha=0.7)
plt.show()
nesse grafico podemos notar que a frequencia das entregas sempre atingem altos valores em relação ao tamanho de entregas

[ ]
gdf_entregas = gpd.GeoDataFrame(deliveries_df, geometry=gpd.points_from_xy(deliveries_df.delivery_lng, deliveries_df.delivery_lat))


gdf_entregas.crs = "EPSG:4326"


gdf_hubs = gpd.GeoDataFrame(deliveries_df, geometry=gpd.points_from_xy(deliveries_df.hub_lng, deliveries_df.hub_lat))


cores_por_regiao = {'df-0': 'red', 'df-1': 'green', 'df-2': 'blue'}


fig, ax = plt.subplots(figsize=(10, 10))


for regiao, cor in cores_por_regiao.items():
    gdf_entregas[gdf_entregas['region'] == regiao].plot(ax=ax, color=cor, markersize=5, label=regiao)


gdf_hubs.plot(ax=ax, color='black', markersize=50, marker='^', label='Hubs')


ctx.add_basemap(ax, crs=gdf_entregas.crs, source=ctx.providers.OpenStreetMap.Mapnik)


ax.set_title('Mapa de Entregas e Hubs por Região')
ax.set_xlabel('Longitude')
ax.set_ylabel('Latitude')


plt.legend()


plt.show()
para uma melhor visualização, nesse mapa podemos ver que as regiões onde estão cituados os hubs, df-0 e df-2 são entregas bastante espalhadas de longas distancias,df-0 sendo mais situada nas regiões norte e leste, e df-2 sendo mais para sul e oeste, dando a entender que haja uma necessidade na alta quantidade de veiculos por eles terem longas jornadas e idas e voltas, ja em df-1 é ao contrario, as entregas são mais centralizadas com viagens mais curtas mas em compensação são feitas mais entregas em menos periodos de tempo, dando a entender que a demanda dessa região é mais veiculos para entregas mais curtas em menos tempo

