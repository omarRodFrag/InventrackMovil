from flask import Flask, jsonify, request, Response
from bson import ObjectId
from functools import wraps
import Backend.GlobalInfo.Helpers as HelperFunctions

import Backend.GlobalInfo.Messages as ResponseMessage

import bcrypt
import re
from flask_mail import Message
import json
import sys
import copy
import random
from flask_mail import Mail
import jwt
import Backend.GlobalInfo.keys as BaseDatos
from pymongo import MongoClient

import datetime
from Backend.GlobalInfo.keys import JWT_SECRET_KEY


# Connection to database
if BaseDatos.dbconn == None:
    mongoConnect = MongoClient(BaseDatos.strConnection)
    BaseDatos.dbconn = mongoConnect[BaseDatos.strDBConnection]
    dbConnLocal = BaseDatos.dbconn

mail = Mail()
from pymongo import MongoClient
import Backend.GlobalInfo.keys as BaseDatos

# Conexión a MongoDB
try:
    mongoConnect = MongoClient(BaseDatos.strConnection)
    dbConnLocal = mongoConnect[BaseDatos.strDBConnection]
    print("Conexión exitosa a MongoDB Atlas")
    
    # Prueba una simple consulta
    test_collection = dbConnLocal.clUsuarios.find_one()
    if test_collection:
        print("Conexión verificada, datos obtenidos.")
    else:
        print("Conexión exitosa, pero no se encontraron datos.")
    
except Exception as e:
    print("Error de conexión a MongoDB Atlas:", e)

def token_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = None
        
        # Verificar si el token está en los encabezados
        if 'Authorization' in request.headers:
            token = request.headers['Authorization'].split(" ")[1]  # Obtener el token de los encabezados
        
        if not token:
            return jsonify({'message': 'Token es requerido'}), 403
        
        try:
            # Verificar y decodificar el token
            decoded_token = jwt.decode(token, JWT_SECRET_KEY, algorithms=['HS256'])
            current_user = dbConnLocal.clUsuarios.find_one({"idUsuario": decoded_token['idUsuario']})
            if not current_user:
                return jsonify({'message': 'Usuario no encontrado'}), 404
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token ha expirado'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Token inválido'}), 401
        
        return f(current_user, *args, **kwargs)
    
    return decorated_function

def fnLogin(email, password):
    try:
        # Buscar al usuario en la base de datos (sin comparar la contraseña directamente)
        jsnInfoUser = dbConnLocal.clUsuarios.find_one({"strEmail": email})
        
        if jsnInfoUser is not None:
            # Verificar la contraseña con bcrypt
            hashed_password = jsnInfoUser.get('strPassword', '')

            if bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8')): 
                # Generar el JWT
                expiration_time = datetime.datetime.utcnow() + datetime.timedelta(hours=1)  # Token expira en 1 hora
                payload = {
                    'idUsuario': jsnInfoUser['idUsuario'],
                    'exp': expiration_time  # Fecha de expiración del token
                }
                token = jwt.encode(payload, JWT_SECRET_KEY, algorithm='HS256')  # Firmamos el token con la clave secreta
                
                # Generar un código de verificación aleatorio
                verification_code = random.randint(100000, 999999)

                # Almacenar el código de verificación en la base de datos
                dbConnLocal.clUsuarios.update_one(
                    {"strEmail": email},
                    {"$set": {"verification_code": verification_code}}
                )

                # Enviar el código de verificación por correo electrónico
                email_sent = send_verification_email(jsnInfoUser['strEmail'], verification_code)
                if email_sent:
                    return {
                                'intResponse': 200,
                                'message': 'Código de verificación enviado al correo.',
                                'token': token
                            }
                else:
                    return {'intResponse': 500, 'Result': {'error': 'No se pudo enviar el correo de verificación.'}}
            else:
                return {'intResponse': 203, 'Result': {'usuario': {}, 'error': 'Usuario o contraseña incorrecta'}}  # Contraseña incorrecta
        else:
            return {'intResponse': 203, 'Result': {'usuario': {}, 'error': 'Usuario no encontrado'}}  # Usuario no encontrado
    except Exception as exception:
        print('fnLogin', exception)
        return {'intResponse': 500}  # Error interno del servidor


# Función para obtener todos los productos
def obtener_productos():
    try:
        productos = list(dbConnLocal.clProductos.find({}))

        productos = [{
            "_id": str(p["_id"]),
            "idProducto": p.get("idProducto"),
            "nombre": p.get("nombre"),
            "descripcion": p.get("descripcion"),
            "categoria": p.get("categoria"),
            "cantidad": p.get("cantidad"),
            "stockMinimo": p.get("stockMinimo"),
            "activo": p.get("activo"),
            "fechaRegistro": p.get("fechaRegistro"),
            "ultimaActualizacion": p.get("ultimaActualizacion"),
        } for p in productos]

        return productos
    except Exception as e:
        HelperFunctions.PrintException()
        return []




# Función para obtener un producto específico por ID
def obtener_producto(idProducto):
    try:
        producto = dbConnLocal.clProductos.find_one({"idProducto": idProducto})
        if producto:
            return {
                "_id": str(producto["_id"]),
                "idProducto": producto.get("idProducto"),
                "nombre": producto.get("nombre"),
                "descripcion": producto.get("descripcion"),
                "categoria": producto.get("categoria"),
                "cantidad": producto.get("cantidad"),
                "stockMinimo": producto.get("stockMinimo"),
                "activo": producto.get("activo"),
                "fechaRegistro": producto.get("fechaRegistro"),
                "ultimaActualizacion": producto.get("ultimaActualizacion")
            }
        return None
    except Exception as e:
        HelperFunctions.PrintException()
        return None



# Función para agregar un producto
def agregar_producto(data):
    try:
        # Obtener el mayor idProducto existente
        max_id = list(dbConnLocal.clProductos.aggregate([
            {"$group": {"_id": None, "maxId": {"$max": "$idProducto"}}}
        ]))
        nuevo_id = 1 if not max_id else max_id[0]['maxId'] + 1

        # Preparar documento
        nuevo_producto = {
            "idProducto": nuevo_id,
            "nombre": data.get("nombre"),
            "descripcion": data.get("descripcion"),
            "categoria": data.get("categoria"),
            "cantidad": data.get("cantidad", 0),
            "stockMinimo": data.get("stockMinimo", 1),
            "activo": True,
            "fechaRegistro": datetime.datetime.utcnow(),
            "ultimaActualizacion": datetime.datetime.utcnow(),
        }

        # Insertar en la colección
        dbConnLocal.clProductos.insert_one(nuevo_producto)

        return {'success': True}
    except Exception as e:
        HelperFunctions.PrintException()
        return {'success': False, 'error': 'No se pudo agregar el producto'}



def actualizar_producto(idProducto, data):
    try:
        producto = dbConnLocal.clProductos.find_one({"idProducto": idProducto})
        if not producto:
            return {'success': False, 'error': 'Producto no encontrado'}

        # Actualización dinámica
        data['ultimaActualizacion'] = datetime.datetime.utcnow()

        result = dbConnLocal.clProductos.update_one(
            {"idProducto": idProducto},
            {"$set": data}
        )

        if result.modified_count > 0:
            return {'success': True}
        else:
            return {'success': False, 'error': 'No se realizaron cambios'}
    except Exception as e:
        HelperFunctions.PrintException()
        return {'success': False, 'error': 'Error al actualizar producto'}
    
def ajustar_stock(idProducto, cantidad):
    try:
        producto = dbConnLocal.clProductos.find_one({"idProducto": idProducto})
        if not producto:
            return {'success': False, 'error': 'Producto no encontrado'}

        nuevo_stock = producto.get('cantidad', 0) + cantidad

        if nuevo_stock < 0:
            return {'success': False, 'error': 'No hay suficiente stock para realizar esta operación'}

        dbConnLocal.clProductos.update_one(
            {"idProducto": idProducto},
            {
                "$set": {
                    "cantidad": nuevo_stock,
                    "ultimaActualizacion": datetime.datetime.utcnow()
                }
            }
        )
        return {'success': True}
    except Exception as e:
        HelperFunctions.PrintException()
        return {'success': False, 'error': 'Error al ajustar stock'}
    

def eliminar_producto(idProducto):
    try:
        resultado = dbConnLocal.clProductos.delete_one({"idProducto": idProducto})

        if resultado.deleted_count > 0:
            return {'success': True}
        else:
            return {'success': False, 'error': 'Producto no encontrado'}
    except Exception as e:
        HelperFunctions.PrintException()
        return {'success': False, 'error': 'Error al eliminar producto'}



# Función para enviar el correo de verificación
def send_verification_email(email, code):
    try:
        msg = Message('Código de Verificación', recipients=[email])
        msg.body = f'Tu código de verificación es: {code}'
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Error al enviar correo: {e}")
        return False




def actualizar_activo(idProducto, activo):
    try:
        res = dbConnLocal.clProductos.update_one(
            {"idProducto": idProducto},
            {"$set": {
                "activo": activo,
                "ultimaActualizacion": datetime.datetime.utcnow()
            }}
        )
        return {'success': res.modified_count > 0}
    except Exception:
        HelperFunctions.PrintException()
        return {'success': False, 'error': 'Error al actualizar status'}
    
    



