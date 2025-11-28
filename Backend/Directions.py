from flask_cors import CORS, cross_origin
from pymongo import MongoClient
from bson import ObjectId
import os
import sys
import Backend.Functions as callMethod
from Backend.Functions import token_required

import Backend.GlobalInfo.Helpers as HelperFunctions
import Backend.GlobalInfo.Messages as ResponseMessage

from flask import Flask, jsonify, request

import json

import Backend.GlobalInfo.keys as BaseDatos
from Backend.Functions import dbConnLocal  # Para hacer la conexión a la BD
from flask_mail import Mail, Message

# --- Logging setup ---
import logging
from logging.handlers import RotatingFileHandler

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
# ----------------------

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Configuración de Flask-Mail
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'omar.rod.fraf@gmail.com'
app.config['MAIL_PASSWORD'] = 'svxf owxq meja eavy'
app.config['MAIL_DEFAULT_SENDER'] = 'omar.rod.fraf@gmail.com'
mail = Mail(app)

# Log de cada petición entrante
@app.before_request
def log_request_info():
    try:
        logger.info(f"REQ START - {request.method} {request.path} - from {request.remote_addr}")
    except Exception:
        logger.exception("Error logueando request info")

@app.after_request
def log_response_info(response):
    try:
        logger.info(f"REQ END - {request.method} {request.path} - status {response.status_code}")
    except Exception:
        logger.exception("Error logueando response info")
    return response


# Ruta para el login
@app.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        email = data.get('strEmail')
        password = data.get('strPassword')

        # Llamar a la función de login
        response = callMethod.fnLogin(email, password)
        # Log de intento de login (sin incluir la contraseña)
        logger.info(f"LOGIN_ATTEMPT - email={email} - result_code={response.get('intResponse')}")
        return jsonify(response), response.get('intResponse', 200)
    except Exception as e:
        logger.exception("Error en la petición /login")
        return jsonify({'error': 'Error en la petición'}), 400

# Ruta para verificar el código MFA
@app.route('/verify', methods=['POST'])
@token_required
def verify_code(current_user):
    try:
        data = request.get_json()
        logger.info(f"VERIFY_CODE - user_id={current_user.get('idUsuario')}")
        
        # Ya no necesitas extraer el email del body
        email = current_user['strEmail']
        entered_code = data.get('code')

        # Buscar el código de verificación en la base de datos
        user = dbConnLocal.clUsuarios.find_one({"strEmail": email})

        if user:
            logger.info(f"VERIFY_CODE - usuario encontrado en BD - email={email}")
            stored_code = user.get('verification_code')
            
            if str(entered_code) == str(stored_code):  # Compara el código ingresado con el generado
                logger.info("VERIFY_CODE - código verificado correctamente")
                return jsonify({'message': 'Código verificado correctamente'}), 200
            else:
                logger.info("VERIFY_CODE - código incorrecto")
                return jsonify({'message': 'Código incorrecto'}), 400
        else:
            logger.warning("VERIFY_CODE - Usuario no encontrado")
            return jsonify({'message': 'Usuario no encontrado'}), 404

    except Exception as e:
        logger.exception("Error al verificar el código")
        return jsonify({'message': 'Error al verificar el código'}), 500


# API para obtener todos los productos
@app.route('/productos', methods=['GET'])
@token_required
def obtener_productos(current_user):
    try:
        productos = callMethod.obtener_productos()
        logger.info(f"OBTENER_PRODUCTOS - user_id={current_user.get('idUsuario')} - count={len(productos)}")
        return jsonify(productos), 200
    except Exception as e:
        logger.exception("Error al obtener productos")
        HelperFunctions.PrintException()
        return jsonify({'error': 'Error al obtener productos'}), 500


# API para obtener un producto específico
@app.route('/productos/<int:idProducto>', methods=['GET'])
@token_required
def obtener_producto(current_user, idProducto):
    try:
        producto = callMethod.obtener_producto(idProducto)
        if producto:
            logger.info(f"OBTENER_PRODUCTO - idProducto={idProducto} - encontrado")
            return jsonify(producto), 200
        else:
            logger.warning(f"OBTENER_PRODUCTO - idProducto={idProducto} - no encontrado")
            return jsonify({'error': 'Producto no encontrado'}), 404
    except Exception as e:
        logger.exception(f"Error al obtener producto id={idProducto}")
        HelperFunctions.PrintException()
        return jsonify({'error': 'Error al obtener producto'}), 500


@app.route('/productos/agregar', methods=['POST'])
@token_required
def agregar_producto(current_user):
    try:
        data = request.get_json()
        resultado = callMethod.agregar_producto(data)
        if resultado.get('success'):
            logger.info(f"AGREGAR_PRODUCTO - user_id={current_user.get('idUsuario')} - nombre={data.get('nombre')}")
            return jsonify({'message': 'Producto agregado correctamente'}), 201
        else:
            logger.warning(f"AGREGAR_PRODUCTO_FAILED - error={resultado.get('error')}")
            return jsonify({'error': resultado.get('error')}), 400
    except Exception as e:
        logger.exception("Error al agregar producto")
        HelperFunctions.PrintException()
        return jsonify({'error': 'Error al agregar producto'}), 500


@app.route('/productos/actualizar/<int:idProducto>', methods=['PUT'])
@token_required
def actualizar_producto(current_user, idProducto):
    try:
        data = request.get_json()
        resultado = callMethod.actualizar_producto(idProducto, data)
        if resultado.get('success'):
            logger.info(f"ACTUALIZAR_PRODUCTO - idProducto={idProducto} - user_id={current_user.get('idUsuario')}")
            return jsonify({'message': 'Producto actualizado correctamente'}), 200
        else:
            logger.warning(f"ACTUALIZAR_PRODUCTO_FAILED - idProducto={idProducto} - error={resultado.get('error')}")
            return jsonify({'error': resultado.get('error')}), 400
    except Exception as e:
        logger.exception(f"Error al actualizar el producto id={idProducto}")
        HelperFunctions.PrintException()
        return jsonify({'error': 'Error al actualizar el producto'}), 500

@app.route('/productos/stock/<int:idProducto>', methods=['PATCH'])
@token_required
def ajustar_stock(current_user, idProducto):
    try:
        data = request.get_json()
        cantidad = data.get("cantidad")  # Puede ser positiva o negativa

        resultado = callMethod.ajustar_stock(idProducto, cantidad)
        if resultado.get('success'):
            logger.info(f"AJUSTAR_STOCK - idProducto={idProducto} - cantidad={cantidad}")
            return jsonify({'message': 'Stock ajustado correctamente'}), 200
        else:
            logger.warning(f"AJUSTAR_STOCK_FAILED - idProducto={idProducto} - error={resultado.get('error')}")
            return jsonify({'error': resultado.get('error')}), 400
    except Exception as e:
        logger.exception(f"Error al ajustar el stock id={idProducto}")
        HelperFunctions.PrintException()
        return jsonify({'error': 'Error al ajustar el stock'}), 500
    

@app.route('/productos/eliminar/<int:idProducto>', methods=['DELETE'])
@token_required
def eliminar_producto(current_user, idProducto):
    try:
        resultado = callMethod.eliminar_producto(idProducto)
        if resultado.get('success'):
            logger.info(f"ELIMINAR_PRODUCTO - idProducto={idProducto} - user_id={current_user.get('idUsuario')}")
            return jsonify({'message': 'Producto eliminado correctamente'}), 200
        else:
            logger.warning(f"ELIMINAR_PRODUCTO_FAILED - idProducto={idProducto} - error={resultado.get('error')}")
            return jsonify({'error': resultado.get('error')}), 404
    except Exception as e:
        logger.exception(f"Error al eliminar el producto id={idProducto}")
        HelperFunctions.PrintException()
        return jsonify({'error': 'Error al eliminar el producto'}), 500
    

@app.route('/productos/estado/<int:idProducto>', methods=['PATCH'])
@token_required
def cambiar_estado_producto(current_user, idProducto):
    try:
        data = request.get_json()
        activo = bool(data.get('activo'))   # fuerza booleano

        resultado = callMethod.actualizar_activo(idProducto, activo)
        if resultado.get('success'):
            logger.info(f"CAMBIAR_ESTADO - idProducto={idProducto} - activo={activo}")
            return jsonify({'message': 'Status actualizado'}), 200
        else:
            logger.warning(f"CAMBIAR_ESTADO_FAILED - idProducto={idProducto} - error={resultado.get('error')}")
            return jsonify({'error': resultado.get('error')}), 400
    except Exception:
        logger.exception(f"Error al actualizar status id={idProducto}")
        HelperFunctions.PrintException()
        return jsonify({'error': 'Error al actualizar status'}), 500


# Ruta para procesar venta (Punto de Venta) por nombre de producto
@app.route('/venta', methods=['POST'])
@token_required
def procesar_venta(current_user):
    try:
        data = request.get_json() or {}
        nombre = data.get('nombre')
        cantidad = data.get('cantidad')

        # Validaciones
        if not nombre or str(nombre).strip() == "":
            logger.warning("VENTA_FAILED - nombre de producto faltante - user_id=%s", current_user.get('idUsuario'))
            return jsonify({'error': 'Nombre del producto es requerido'}), 400

        try:
            cantidad = int(cantidad)
        except Exception:
            logger.warning("VENTA_FAILED - cantidad invalida - value=%s - user_id=%s", cantidad, current_user.get('idUsuario'))
            return jsonify({'error': 'Cantidad inválida'}), 400

        if cantidad <= 0:
            logger.warning("VENTA_FAILED - cantidad debe ser positiva - cantidad=%s - user_id=%s", cantidad, current_user.get('idUsuario'))
            return jsonify({'error': 'La cantidad debe ser mayor a 0'}), 400

        resultado = callMethod.procesar_venta_por_nombre(nombre, cantidad, current_user)

        if resultado.get('success'):
            logger.info("VENTA_PROCESADA - nombre=%s - cantidad=%s - user_id=%s - ventaId=%s",
                        nombre, cantidad, current_user.get('idUsuario'), resultado.get('venta', {}).get('idVenta'))
            # Devolvemos mensaje y producto (compatibilidad con frontend existente), además del registro de venta
            return jsonify({
                'message': 'Venta procesada correctamente',
                'producto': resultado.get('producto'),
                'venta': resultado.get('venta', {})
            }), 200
        else:
            err = resultado.get('error', 'Error al procesar venta')
            logger.warning("VENTA_FAILED - nombre=%s - cantidad=%s - error=%s - user_id=%s", nombre, cantidad, err, current_user.get('idUsuario'))
            if err == 'Producto no encontrado':
                return jsonify({'error': err}), 404
            if err.startswith('No hay suficiente stock'):
                return jsonify({'error': err}), 400
            return jsonify({'error': err}), 400

    except Exception:
        logger.exception("Error en /venta")
        HelperFunctions.PrintException()
        return jsonify({'error': 'Error al procesar la venta'}), 500



if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"Arrancando servidor en puerto {port}")
    app.run(host='0.0.0.0', port=port, debug=True)
