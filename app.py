from flask import Flask, render_template, request, redirect
import sqlite3
from datetime import datetime

app = Flask(__name__)

# Función para obtener una conexión a la base de datos
def get_db_connection():
    # Conectar a la base de datos SQLite
    conn = sqlite3.connect('/home/lksw/Super/supermercadoFinal.db')  # Asegúrate de que esta es la ruta correcta a tu base de datos en PythonAnywhere
    conn.row_factory = sqlite3.Row  # Configurar para que las filas se comporten como diccionarios
    return conn

# Función para crear las tablas si no existen
def create_table():
    conn = get_db_connection()
    cursor = conn.cursor()
    # Crear la tabla 'super' si no existe
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS super (
        codigo TEXT PRIMARY KEY,
        nombre TEXT NOT NULL,
        descripcion TEXT,
        stock INTEGER NOT NULL,
        precio_unitario REAL NOT NULL,
        fecha_vencimiento TEXT,
        tipo CHAR(1),
        descuento REAL,
        cantidad_vendida INTEGER DEFAULT 0,
        tiene_descuento TEXT DEFAULT 'no'
    )
    """)
    # Crear la tabla 'productos_vencidos' si no existe
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS productos_vencidos (
        codigo TEXT PRIMARY KEY,
        nombre TEXT NOT NULL,
        descripcion TEXT,
        stock INTEGER NOT NULL,
        precio_unitario REAL NOT NULL,
        fecha_vencimiento TEXT,
        tipo CHAR(1),
        descuento REAL,
        cantidad_vendida INTEGER DEFAULT 0,
        tiene_descuento TEXT DEFAULT 'no'
    )
    """)
    conn.commit()
    conn.close()

# Función para mover productos vencidos a la tabla 'productos_vencidos'
def mover_productos_vencidos():
    conn = get_db_connection()
    cursor = conn.cursor()
    hoy = datetime.now().strftime('%Y-%m-%d')  # Obtener la fecha actual en formato 'YYYY-MM-DD'
    cursor.execute("SELECT * FROM super")  # Seleccionar todos los productos de la tabla 'super'
    productos = cursor.fetchall()
    for producto in productos:
        fecha_vencimiento = producto['fecha_vencimiento']
        try:
            # Intentar convertir la fecha en formato 'YYYY-MM-DD'
            fecha_vencimiento_dt = datetime.strptime(fecha_vencimiento, '%Y-%m-%d')
        except ValueError:
            try:
                # Intentar convertir la fecha en formato 'DD/MM/YYYY'
                fecha_vencimiento_dt = datetime.strptime(fecha_vencimiento, '%d/%m/%Y')
            except ValueError:
                continue
        
        # Si el producto está vencido, moverlo a la tabla 'productos_vencidos'
        if fecha_vencimiento_dt <= datetime.now():
            cursor.execute("""
            INSERT INTO productos_vencidos (codigo, nombre, descripcion, stock, precio_unitario, fecha_vencimiento, tipo, descuento, cantidad_vendida, tiene_descuento)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (producto['codigo'], producto['nombre'], producto['descripcion'], producto['stock'], producto['precio_unitario'], producto['fecha_vencimiento'], producto['tipo'], producto['descuento'], producto['cantidad_vendida'], producto['tiene_descuento']))
            cursor.execute("DELETE FROM super WHERE codigo = ?", (producto['codigo'],))
    conn.commit()
    conn.close()

# Función para convertir las fechas de los productos a objetos datetime
def convertir_fechas(productos):
    productos_dict = [dict(producto) for producto in productos]
    for producto in productos_dict:
        try:
            producto['fecha_vencimiento'] = datetime.strptime(producto['fecha_vencimiento'], '%Y-%m-%d')
        except ValueError:
            try:
                producto['fecha_vencimiento'] = datetime.strptime(producto['fecha_vencimiento'], '%d/%m/%Y')
            except ValueError:
                producto['fecha_vencimiento'] = None
    return productos_dict

# Ruta principal para mostrar los productos
@app.route('/')
def index():
    create_table()  # Crear las tablas si no existen
    mover_productos_vencidos()  # Mover productos vencidos a la tabla 'productos_vencidos'
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM super")  # Seleccionar todos los productos de la tabla 'super'
    productos = cursor.fetchall()
    productos = convertir_fechas(productos)  # Convertir las fechas a objetos datetime
    conn.close()
    return render_template('index.html', productos=productos)

# Ruta para mostrar los productos vencidos
@app.route('/productos_vencidos')
def productos_vencidos():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM productos_vencidos")  # Seleccionar todos los productos de la tabla 'productos_vencidos'
    productos = cursor.fetchall()
    productos = convertir_fechas(productos)  # Convertir las fechas a objetos datetime
    conn.close()
    return render_template('productos_vencidos.html', productos=productos)

# Ruta para agregar un nuevo producto
@app.route('/agregar', methods=('GET', 'POST'))
def agregar():
    if request.method == 'POST':
        # Obtener los datos del formulario
        codigo = request.form['codigo']
        nombre = request.form['nombre']
        descripcion = request.form['descripcion']
        stock = request.form['stock']
        precio_unitario = request.form['precio_unitario']
        fecha_vencimiento = request.form['fecha_vencimiento']
        tipo = request.form['tipo']
        descuento = request.form['descuento']
        cantidad_vendida = request.form['cantidad_vendida']
        tiene_descuento = request.form['tiene_descuento']

        # Insertar el nuevo producto en la tabla 'super'
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO super (codigo, nombre, descripcion, stock, precio_unitario, fecha_vencimiento, tipo, descuento, cantidad_vendida, tiene_descuento) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                       (codigo, nombre, descripcion, stock, precio_unitario, fecha_vencimiento, tipo, descuento, cantidad_vendida, tiene_descuento))
        conn.commit()
        conn.close()
        return redirect('/')
    return render_template('agregar.html')

# Ruta para borrar un producto
@app.route('/borrar/<codigo>')
def borrar(codigo):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM super WHERE codigo = ?", (codigo,))  # Borrar el producto con el código especificado
    conn.commit()
    conn.close()
    return redirect('/')

# Ruta para editar un producto
@app.route('/editar/<codigo>', methods=('GET', 'POST'))
def editar(codigo):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM super WHERE codigo = ?", (codigo,))  # Seleccionar el producto con el código especificado
    producto = cursor.fetchone()

    if request.method == 'POST':
        # Obtener los datos del formulario
        nombre = request.form['nombre']
        descripcion = request.form['descripcion']
        stock = request.form['stock']
        precio_unitario = request.form['precio_unitario']
        fecha_vencimiento = request.form['fecha_vencimiento']
        tipo = request.form['tipo']
        descuento = request.form['descuento']
        cantidad_vendida = request.form['cantidad_vendida']
        tiene_descuento = request.form['tiene_descuento']

        # Actualizar el producto en la tabla 'super'
        cursor.execute("UPDATE super SET nombre = ?, descripcion = ?, stock = ?, precio_unitario = ?, fecha_vencimiento = ?, tipo = ?, descuento = ?, cantidad_vendida = ?, tiene_descuento = ? WHERE codigo = ?",
                       (nombre, descripcion, stock, precio_unitario, fecha_vencimiento, tipo, descuento, cantidad_vendida, tiene_descuento, codigo))
        conn.commit()
        conn.close()
        return redirect('/')

    conn.close()
    return render_template('editar.html', producto=dict(producto))

if __name__ == '__main__':
    create_table()  # Crear las tablas si no existen
    app.run(debug=True)  # Ejecutar la aplicación Flask en modo de depuración