import os

# Variable para la conexión
dbconn = None

JWT_SECRET_KEY = 'R1Xfj$3pnkd3Gx9A*v4'


# MongoDB
# Para producción en MongoDB Atlas (usa las variables de entorno para seguridad)
strConnection = os.getenv(
    'MONGODB_URI', 
    "mongodb+srv://omarrodfraf:f716fa40@clusteromar.m8ome.mongodb.net/?retryWrites=true&w=majority&appName=ClusterOmar"
)
#strConnection = "mongodb://localhost:27017"
strDBConnection = "Inventrack"  # Cambia esto por el nombre de tu base de datos en Atlas
