from flask import Flask, render_template, request, redirect
import sqlite3
from datetime import datetime

app = Flask(__name__)

def get_db_connection():
    conn = sqlite3.connect('/home/lksw/Super/supermercadoFinal.db')  # Asegúrate de que esta es la ruta correcta a tu base de datos en PythonAnywhere
    conn.row_factory = sqlite3.Row
    return conn

def create_table():
    conn = get_db_connection()
    cursor = conn.cursor()
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

def mover_productos_vencidos():
    conn = get_db_connection()
    cursor = conn.cursor()
    hoy = datetime.now().strftime('%Y-%m-%d')
    cursor.execute("SELECT * FROM super")
    productos = cursor.fetchall()
    for producto in productos:
        fecha_vencimiento = producto['fecha_vencimiento']
        try:
            # Intentar convertir la fecha en formato yyyy-mm-dd
            fecha_vencimiento_dt = datetime.strptime(fecha_vencimiento, '%Y-%m-%d')
        except ValueError:
            try:
                # Intentar convertir la fecha en formato dd/mm/yyyy
                fecha_vencimiento_dt = datetime.strptime(fecha_vencimiento, '%d/%m/%Y')
            except ValueError:
                # Si la fecha no está en ninguno de los formatos, continuar con el siguiente producto
                continue
        
        if fecha_vencimiento_dt <= datetime.now():
            cursor.execute("""
            INSERT INTO productos_vencidos (codigo, nombre, descripcion, stock, precio_unitario, fecha_vencimiento, tipo, descuento, cantidad_vendida, tiene_descuento)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (producto['codigo'], producto['nombre'], producto['descripcion'], producto['stock'], producto['precio_unitario'], producto['fecha_vencimiento'], producto['tipo'], producto['descuento'], producto['cantidad_vendida'], producto['tiene_descuento']))
            cursor.execute("DELETE FROM super WHERE codigo = ?", (producto['codigo'],))
    conn.commit()
    conn.close()

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

@app.route('/')
def index():
    create_table()  # Ensure the table is created
    mover_productos_vencidos()  # Move expired products
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM super")
    productos = cursor.fetchall()
    productos = convertir_fechas(productos)
    conn.close()
    return render_template('index.html', productos=productos)

@app.route('/productos_vencidos')
def productos_vencidos():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM productos_vencidos")
    productos = cursor.fetchall()
    productos = convertir_fechas(productos)
    conn.close()
    return render_template('productos_vencidos.html', productos=productos)

@app.route('/agregar', methods=('GET', 'POST'))
def agregar():
    if request.method == 'POST':
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

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO super (codigo, nombre, descripcion, stock, precio_unitario, fecha_vencimiento, tipo, descuento, cantidad_vendida, tiene_descuento) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                       (codigo, nombre, descripcion, stock, precio_unitario, fecha_vencimiento, tipo, descuento, cantidad_vendida, tiene_descuento))
        conn.commit()
        conn.close()
        return redirect('/')
    return render_template('agregar.html')

@app.route('/borrar/<codigo>')
def borrar(codigo):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM super WHERE codigo = ?", (codigo,))
    conn.commit()
    conn.close()
    return redirect('/')

@app.route('/editar/<codigo>', methods=('GET', 'POST'))
def editar(codigo):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM super WHERE codigo = ?", (codigo,))
    producto = cursor.fetchone()

    if request.method == 'POST':
        nombre = request.form['nombre']
        descripcion = request.form['descripcion']
        stock = request.form['stock']
        precio_unitario = request.form['precio_unitario']
        fecha_vencimiento = request.form['fecha_vencimiento']
        tipo = request.form['tipo']
        descuento = request.form['descuento']
        cantidad_vendida = request.form['cantidad_vendida']
        tiene_descuento = request.form['tiene_descuento']

        cursor.execute("UPDATE super SET nombre = ?, descripcion = ?, stock = ?, precio_unitario = ?, fecha_vencimiento = ?, tipo = ?, descuento = ?, cantidad_vendida = ?, tiene_descuento = ? WHERE codigo = ?",
                       (nombre, descripcion, stock, precio_unitario, fecha_vencimiento, tipo, descuento, cantidad_vendida, tiene_descuento, codigo))
        conn.commit()
        conn.close()
        return redirect('/')

    conn.close()
    return render_template('editar.html', producto=dict(producto))

if __name__ == '__main__':
    create_table()  # Ensure the table is created when the app starts
    app.run(debug=True)