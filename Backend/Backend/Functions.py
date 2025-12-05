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

# --- Logging setup (comparte el logger 'invenTrackLogger') ---
import logging
from logging.handlers import RotatingFileHandler
import os

LOG_DIR = 'logs'
os.makedirs(LOG_DIR, exist_ok=True)

logger = logging.getLogger('invenTrackLogger')
logger.setLevel(logging.INFO)
if not logger.hasHandlers():
    log_path = os.path.join(LOG_DIR, 'error.log')
    fh = RotatingFileHandler(log_path, maxBytes=5*1024*1024, backupCount=5, encoding='utf-8')
    fh.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(module)s - %(message)s')
    fh.setFormatter(formatter)
    logger.addHandler(fh)
# ----------------------------------------------------------------

# Connection to database
if BaseDatos.dbconn == None:
    try:
        mongoConnect = MongoClient(BaseDatos.strConnection)
        BaseDatos.dbconn = mongoConnect[BaseDatos.strDBConnection]
        dbConnLocal = BaseDatos.dbconn
        logger.info("Inicializada variable BaseDatos.dbconn")
    except Exception:
        logger.exception("Error inicializando BaseDatos.dbconn")
        dbConnLocal = None

mail = Mail()
from pymongo import MongoClient
import Backend.GlobalInfo.keys as BaseDatos

# Conexión a MongoDB
try:
    mongoConnect = MongoClient(BaseDatos.strConnection)
    dbConnLocal = mongoConnect[BaseDatos.strDBConnection]
    logger.info("Conexión exitosa a MongoDB Atlas")
    
    # Prueba una simple consulta
    test_collection = dbConnLocal.clUsuarios.find_one()
    if test_collection:
        logger.info("Conexión verificada, datos obtenidos.")
    else:
        logger.info("Conexión verificada, pero no se encontraron datos.")
    
except Exception as e:
    logger.exception("Error de conexión a MongoDB Atlas: %s", e)

def token_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = None
        
        # Verificar si el token está en los encabezados
        if 'Authorization' in request.headers:
            try:
                token = request.headers['Authorization'].split(" ")[1]  # Obtener el token de los encabezados
            except Exception:
                logger.warning("Authorization header mal formado")
                return jsonify({'message': 'Token es requerido'}), 403
        
        if not token:
            logger.warning("Token faltante en request a %s %s", request.method, request.path)
            return jsonify({'message': 'Token es requerido'}), 403
        
        try:
            # Verificar y decodificar el token
            decoded_token = jwt.decode(token, JWT_SECRET_KEY, algorithms=['HS256'])
            current_user = dbConnLocal.clUsuarios.find_one({"idUsuario": decoded_token['idUsuario']})
            if not current_user:
                logger.warning("Token válido pero usuario no encontrado - idUsuario=%s", decoded_token.get('idUsuario'))
                return jsonify({'message': 'Usuario no encontrado'}), 404
        except jwt.ExpiredSignatureError:
            logger.info("Token expirado")
            return jsonify({'message': 'Token ha expirado'}), 401
        except jwt.InvalidTokenError:
            logger.info("Token inválido o con firma incorrecta")
            return jsonify({'message': 'Token inválido'}), 401
        except Exception:
            logger.exception("Error verificando token")
            return jsonify({'message': 'Error verificando token'}), 401
        
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
                    logger.info(f"LOGIN_SUCCESS - email={email} - idUsuario={jsnInfoUser.get('idUsuario')}")
                    return {
                                'intResponse': 200,
                                'message': 'Código de verificación enviado al correo.',
                                'token': token
                            }
                else:
                    logger.error("LOGIN_EMAIL_FAIL - No se pudo enviar el correo de verificación - email=%s", jsnInfoUser.get('strEmail'))
                    return {'intResponse': 500, 'Result': {'error': 'No se pudo enviar el correo de verificación.'}}
            else:
                logger.info(f"LOGIN_FAIL - contraseña incorrecta - email={email}")
                return {'intResponse': 203, 'Result': {'usuario': {}, 'error': 'Usuario o contraseña incorrecta'}}  # Contraseña incorrecta
        else:
            logger.info(f"LOGIN_FAIL - usuario no encontrado - email={email}")
            return {'intResponse': 203, 'Result': {'usuario': {}, 'error': 'Usuario no encontrado'}}  # Usuario no encontrado
    except Exception as exception:
        logger.exception("Error en fnLogin")
        return {'intResponse': 500}  # Error interno del servidor


def fnRegister(email, password):
    try:
        # Validar formato de email
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            logger.info(f"REGISTER_FAIL - email inválido - email={email}")
            return {'intResponse': 400, 'error': 'Formato de email inválido'}
        
        # Verificar que el email no exista
        usuario_existente = dbConnLocal.clUsuarios.find_one({"strEmail": email})
        if usuario_existente is not None:
            logger.info(f"REGISTER_FAIL - email ya existe - email={email}")
            return {'intResponse': 400, 'error': 'El email ya está registrado'}
        
        # Validar contraseña (mínimo 6 caracteres)
        if not password or len(password) < 6:
            logger.info(f"REGISTER_FAIL - contraseña muy corta - email={email}")
            return {'intResponse': 400, 'error': 'La contraseña debe tener al menos 6 caracteres'}
        
        # Hashear la contraseña con bcrypt
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Generar idUsuario único
        max_id = list(dbConnLocal.clUsuarios.aggregate([
            {"$group": {"_id": None, "maxId": {"$max": "$idUsuario"}}}
        ]))
        nuevo_id = 1 if not max_id or max_id[0]['maxId'] is None else max_id[0]['maxId'] + 1
        
        # Crear nuevo usuario
        nuevo_usuario = {
            "idUsuario": nuevo_id,
            "strEmail": email,
            "strPassword": hashed_password,
            "fechaRegistro": datetime.datetime.utcnow()
        }
        
        # Guardar en la base de datos
        insert_res = dbConnLocal.clUsuarios.insert_one(nuevo_usuario)
        logger.info(f"REGISTER_SUCCESS - email={email} - idUsuario={nuevo_id} - inserted_id={insert_res.inserted_id}")
        
        return {
            'intResponse': 201,
            'message': 'Usuario registrado correctamente',
            'idUsuario': nuevo_id
        }
    except Exception as exception:
        logger.exception("Error en fnRegister")
        HelperFunctions.PrintException()
        return {'intResponse': 500, 'error': 'Error al registrar usuario'}


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

        logger.info(f"obtener_productos - encontrado {len(productos)} productos")
        return productos
    except Exception as e:
        logger.exception("Error en obtener_productos")
        HelperFunctions.PrintException()
        return []

# Función para obtener un producto específico por ID
def obtener_producto(idProducto):
    try:
        producto = dbConnLocal.clProductos.find_one({"idProducto": idProducto})
        if producto:
            logger.info(f"obtener_producto - idProducto={idProducto} - encontrado")
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
        logger.warning(f"obtener_producto - idProducto={idProducto} - no encontrado")
        return None
    except Exception as e:
        logger.exception("Error en obtener_producto")
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
        insert_res = dbConnLocal.clProductos.insert_one(nuevo_producto)
        logger.info(f"agregar_producto - idProducto={nuevo_id} - inserted_id={insert_res.inserted_id}")
        return {'success': True}
    except Exception as e:
        logger.exception("Error en agregar_producto")
        HelperFunctions.PrintException()
        return {'success': False, 'error': 'No se pudo agregar el producto'}



def actualizar_producto(idProducto, data):
    try:
        producto = dbConnLocal.clProductos.find_one({"idProducto": idProducto})
        if not producto:
            logger.warning(f"actualizar_producto - idProducto={idProducto} - no encontrado")
            return {'success': False, 'error': 'Producto no encontrado'}

        # Actualización dinámica
        data['ultimaActualizacion'] = datetime.datetime.utcnow()

        result = dbConnLocal.clProductos.update_one(
            {"idProducto": idProducto},
            {"$set": data}
        )

        if result.modified_count > 0:
            logger.info(f"actualizar_producto - idProducto={idProducto} - modificados={result.modified_count}")
            return {'success': True}
        else:
            logger.info(f"actualizar_producto - idProducto={idProducto} - no se realizaron cambios")
            return {'success': False, 'error': 'No se realizaron cambios'}
    except Exception as e:
        logger.exception("Error en actualizar_producto")
        HelperFunctions.PrintException()
        return {'success': False, 'error': 'Error al actualizar producto'}
    
def ajustar_stock(idProducto, cantidad):
    try:
        producto = dbConnLocal.clProductos.find_one({"idProducto": idProducto})
        if not producto:
            logger.warning(f"ajustar_stock - idProducto={idProducto} - no encontrado")
            return {'success': False, 'error': 'Producto no encontrado'}

        nuevo_stock = producto.get('cantidad', 0) + cantidad

        if nuevo_stock < 0:
            logger.info(f"ajustar_stock - intento reducir por debajo de 0 - idProducto={idProducto} - cantidad={cantidad}")
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
        logger.info(f"ajustar_stock - idProducto={idProducto} - nuevo_stock={nuevo_stock}")
        return {'success': True}
    except Exception as e:
        logger.exception("Error en ajustar_stock")
        HelperFunctions.PrintException()
        return {'success': False, 'error': 'Error al ajustar stock'}
    

def eliminar_producto(idProducto):
    try:
        resultado = dbConnLocal.clProductos.delete_one({"idProducto": idProducto})

        if resultado.deleted_count > 0:
            logger.info(f"eliminar_producto - idProducto={idProducto} - eliminado")
            return {'success': True}
        else:
            logger.warning(f"eliminar_producto - idProducto={idProducto} - no encontrado")
            return {'success': False, 'error': 'Producto no encontrado'}
    except Exception as e:
        logger.exception("Error en eliminar_producto")
        HelperFunctions.PrintException()
        return {'success': False, 'error': 'Error al eliminar producto'}



# Función para enviar el correo de verificación
def send_verification_email(email, code):
    try:
        msg = Message('Código de Verificación', recipients=[email])
        msg.body = f'Tu código de verificación es: {code}'
        mail.send(msg)
        logger.info(f"send_verification_email - email enviado a {email}")
        return True
    except Exception as e:
        logger.exception(f"Error al enviar correo a {email}")
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
        logger.info(f"actualizar_activo - idProducto={idProducto} - activo={activo} - modified={res.modified_count}")
        return {'success': res.modified_count > 0}
    except Exception:
        logger.exception("Error en actualizar_activo")
        HelperFunctions.PrintException()
        return {'success': False, 'error': 'Error al actualizar status'}



def procesar_venta_por_nombre(nombre, cantidad, usuario=None):
    """
    Realiza la venta por nombre (solo nombre, user-friendly), reduce stock
    y registra la venta en la colección clVentas.
    Devuelve {'success': True, 'producto': {...}, 'venta': {...}} o {'success': False, 'error': '...'}
    """
    try:
        if not nombre or str(nombre).strip() == "":
            return {'success': False, 'error': 'Nombre inválido'}

        try:
            cantidad = int(cantidad)
        except Exception:
            return {'success': False, 'error': 'Cantidad inválida'}

        if cantidad <= 0:
            return {'success': False, 'error': 'Cantidad inválida'}

        nombre_busqueda = str(nombre).strip()

        # Filtro case-insensitive exact match (igual que en otras funciones)
        filtro_update = {
            "nombre": {"$regex": f"^{nombre_busqueda}$", "$options": "i"},
            "cantidad": {"$gte": cantidad}
        }

        update = {
            "$inc": {"cantidad": -cantidad},
            "$set": {"ultimaActualizacion": datetime.datetime.utcnow()}
        }

        res = dbConnLocal.clProductos.update_one(filtro_update, update)

        if res.modified_count > 0:
            # Venta realizada. Recuperamos el documento actualizado
            producto_actualizado = dbConnLocal.clProductos.find_one(
                {"nombre": {"$regex": f"^{nombre_busqueda}$", "$options": "i"}}
            )

            if not producto_actualizado:
                # Raro: se modificó pero no encontramos (fallback)
                logger.warning("procesar_venta_por_nombre - producto actualizado pero find_one falló - nombre=%s", nombre_busqueda)
                return {'success': True, 'producto': None, 'venta': {}}

            # Preparar objeto producto para respuesta
            producto_resp = {
                "idProducto": producto_actualizado.get("idProducto"),
                "nombre": producto_actualizado.get("nombre"),
                "cantidad": producto_actualizado.get("cantidad"),
                "ultimaActualizacion": producto_actualizado.get("ultimaActualizacion")
            }

            # --- Crear registro de venta en clVentas ---
            try:
                # Generar idVenta incremental (misma lógica que usas para idProducto)
                max_id = list(dbConnLocal.clVentas.aggregate([
                    {"$group": {"_id": None, "maxId": {"$max": "$idVenta"}}}
                ]))
                nuevo_id_venta = 1 if not max_id else max_id[0]['maxId'] + 1

                # Intentamos obtener precio si el producto lo tiene (opcional)
                precio_unitario = producto_actualizado.get('precio', None)
                venta_total = None
                if precio_unitario is not None:
                    try:
                        venta_total = float(precio_unitario) * float(cantidad)
                    except Exception:
                        venta_total = None

                registro_venta = {
                    "idVenta": nuevo_id_venta,
                    "idProducto": producto_actualizado.get("idProducto"),
                    "nombre": producto_actualizado.get("nombre"),
                    "cantidadVendida": cantidad,
                    "precioUnitario": precio_unitario,
                    "ventaTotal": venta_total,
                    "idUsuario": usuario.get('idUsuario') if usuario else None,
                    "fecha": datetime.datetime.utcnow(),
                }

                insert_res = dbConnLocal.clVentas.insert_one(registro_venta)
                logger.info("procesar_venta_por_nombre - registrado en clVentas - idVenta=%s - inserted_id=%s",
                            nuevo_id_venta, insert_res.inserted_id)

                venta_resp = {
                    "idVenta": nuevo_id_venta,
                    "idProducto": registro_venta.get("idProducto"),
                    "cantidadVendida": registro_venta.get("cantidadVendida"),
                    "precioUnitario": registro_venta.get("precioUnitario"),
                    "ventaTotal": registro_venta.get("ventaTotal"),
                    "fecha": registro_venta.get("fecha")
                }

            except Exception:
                # Si por alguna razón falla el registro en clVentas, no revertimos el stock (pero lo logueamos)
                logger.exception("procesar_venta_por_nombre - error registrando en clVentas")
                HelperFunctions.PrintException()
                venta_resp = {}

            return {'success': True, 'producto': producto_resp, 'venta': venta_resp}

        else:
            # No se modificó nada: o no existe el producto o no hay stock suficiente.
            existe = dbConnLocal.clProductos.find_one({"nombre": {"$regex": f"^{nombre_busqueda}$", "$options": "i"}})
            if not existe:
                logger.info("procesar_venta_por_nombre - producto no encontrado - nombre=%s", nombre_busqueda)
                return {'success': False, 'error': 'Producto no encontrado'}
            else:
                logger.info("procesar_venta_por_nombre - stock insuficiente - nombre=%s - solicitado=%s - disponible=%s",
                            nombre_busqueda, cantidad, existe.get('cantidad', 0))
                return {'success': False, 'error': 'No hay suficiente stock para realizar esta operación'}

    except Exception:
        logger.exception("Error en procesar_venta_por_nombre")
        HelperFunctions.PrintException()
        return {'success': False, 'error': 'Error al procesar la venta'}
