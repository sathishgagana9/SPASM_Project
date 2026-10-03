from sentence_transformers import SentenceTransformer

from sklearn.decomposition import PCA

from sklearn.cluster import KMeans

from sklearn.metrics import (
    silhouette_score,
    davies_bouldin_score
)

model = SentenceTransformer(
    "all-MiniLM-L6-v2"
)

texts = [

    "Doctor helping patient",

    "Patient describing symptoms",

    "Teacher helping student",

    "Student asking questions",

    "Lawyer giving advice",

    "Client seeking legal help"
]

embeddings = model.encode(texts)

# PCA

pca = PCA(n_components=2)

reduced = pca.fit_transform(
    embeddings
)

print(
    "Explained Variance:",
    pca.explained_variance_ratio_
)

# Clustering

kmeans = KMeans(
    n_clusters=3,
    random_state=42
)

labels = kmeans.fit_predict(
    embeddings
)

silhouette = silhouette_score(
    embeddings,
    labels
)

db_index = davies_bouldin_score(
    embeddings,
    labels
)

print(
    "Silhouette Score:",
    round(silhouette, 4)
)

print(
    "Davies-Bouldin Index:",
    round(db_index, 4)
)