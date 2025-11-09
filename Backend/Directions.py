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





# Ruta para el login
@app.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        email = data.get('strEmail')
        password = data.get('strPassword')

        # Llamar a la función de login
        response = callMethod.fnLogin(email,password)
        return jsonify(response), response['intResponse']
    except Exception as e:
        print(str(e))
        return jsonify({'error': 'Error en la petición'}), 400

# Ruta para verificar el código MFA
@app.route('/verify', methods=['POST'])
@token_required
def verify_code(current_user):
    try:
        data = request.get_json()
        print("Datos recibidos:", data)
        
        # Ya no necesitas extraer el email del body
        email = current_user['strEmail']
        entered_code = data.get('code')

        # Buscar el código de verificación en la base de datos
        user = dbConnLocal.clUsuarios.find_one({"strEmail": email})

        if user:
            print(user)
            stored_code = user.get('verification_code')
            
            if str(entered_code) == str(stored_code):  # Compara el código ingresado con el generado
                return jsonify({'message': 'Código verificado correctamente'}), 200
            else:
                return jsonify({'message': 'Código incorrecto'}), 400
        else:
            return jsonify({'message': 'Usuario no encontrado'}), 404

    except Exception as e:
        print(str(e))
        return jsonify({'message': 'Error al verificar el código'}), 500


# API para obtener todos los productos
@app.route('/productos', methods=['GET'])
@token_required
def obtener_productos(current_user):
    try:
        productos = callMethod.obtener_productos()
        return jsonify(productos), 200
    except Exception as e:
        HelperFunctions.PrintException()
        return jsonify({'error': 'Error al obtener productos'}), 500



# API para obtener un producto específico
@app.route('/productos/<int:idProducto>', methods=['GET'])
@token_required
def obtener_producto(current_user, idProducto):
    try:
        producto = callMethod.obtener_producto(idProducto)
        if producto:
            return jsonify(producto), 200
        else:
            return jsonify({'error': 'Producto no encontrado'}), 404
    except Exception as e:
        HelperFunctions.PrintException()
        return jsonify({'error': 'Error al obtener producto'}), 500


@app.route('/productos/agregar', methods=['POST'])
@token_required
def agregar_producto(current_user):
    try:
        data = request.get_json()
        resultado = callMethod.agregar_producto(data)
        if resultado['success']:
            return jsonify({'message': 'Producto agregado correctamente'}), 201
        else:
            return jsonify({'error': resultado['error']}), 400
    except Exception as e:
        HelperFunctions.PrintException()
        return jsonify({'error': 'Error al agregar producto'}), 500


@app.route('/productos/actualizar/<int:idProducto>', methods=['PUT'])
@token_required
def actualizar_producto(current_user, idProducto):
    try:
        data = request.get_json()
        resultado = callMethod.actualizar_producto(idProducto, data)
        if resultado['success']:
            return jsonify({'message': 'Producto actualizado correctamente'}), 200
        else:
            return jsonify({'error': resultado['error']}), 400
    except Exception as e:
        HelperFunctions.PrintException()
        return jsonify({'error': 'Error al actualizar el producto'}), 500

@app.route('/productos/stock/<int:idProducto>', methods=['PATCH'])
@token_required
def ajustar_stock(current_user, idProducto):
    try:
        data = request.get_json()
        cantidad = data.get("cantidad")  # Puede ser positiva o negativa

        resultado = callMethod.ajustar_stock(idProducto, cantidad)
        if resultado['success']:
            return jsonify({'message': 'Stock ajustado correctamente'}), 200
        else:
            return jsonify({'error': resultado['error']}), 400
    except Exception as e:
        HelperFunctions.PrintException()
        return jsonify({'error': 'Error al ajustar el stock'}), 500
    

@app.route('/productos/eliminar/<int:idProducto>', methods=['DELETE'])
@token_required
def eliminar_producto(current_user, idProducto):
    try:
        resultado = callMethod.eliminar_producto(idProducto)
        if resultado['success']:
            return jsonify({'message': 'Producto eliminado correctamente'}), 200
        else:
            return jsonify({'error': resultado['error']}), 404
    except Exception as e:
        HelperFunctions.PrintException()
        return jsonify({'error': 'Error al eliminar el producto'}), 500
    


@app.route('/productos/estado/<int:idProducto>', methods=['PATCH'])
@token_required
def cambiar_estado_producto(current_user, idProducto):
    try:
        data = request.get_json()
        activo = bool(data.get('activo'))   # fuerza booleano

        resultado = callMethod.actualizar_activo(idProducto, activo)
        if resultado['success']:
            return jsonify({'message': 'Status actualizado'}), 200
        else:
            return jsonify({'error': resultado['error']}), 400
    except Exception:
        HelperFunctions.PrintException()
        return jsonify({'error': 'Error al actualizar status'}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)



