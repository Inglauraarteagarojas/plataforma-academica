from flask import Flask, render_template, request, redirect, url_for, send_file, flash
import csv
import os
from datetime import datetime
import io
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'cambiar-esta-clave-en-produccion')

# Lista para almacenar los datos (en producción usarías una base de datos)
academic_data = []

@app.route('/')
def index():
    """Página principal con el formulario"""
    return render_template('index.html')

@app.route('/add_data', methods=['POST'])
def add_data():
    """Procesar datos del formulario"""
    try:
        # Obtener datos del formulario
        data = {
            'nombre_asignatura': request.form.get('nombre_asignatura', '').strip(),
            'numero_semana': request.form.get('numero_semana', '').strip(),
            'tema_general': request.form.get('tema_general', '').strip(),
            'temas_especificos': request.form.get('temas_especificos', '').strip(),
            'trabajo_individual': request.form.get('trabajo_individual', '').strip(),
            'bibliografia_recomendada': request.form.get('bibliografia_recomendada', '').strip(),
            'bibliografia_complementaria': request.form.get('bibliografia_complementaria', '').strip(),
            'practica_individual_grupal': request.form.get('practica_individual_grupal', '').strip(),
            'fecha_creacion': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # Validar que los campos obligatorios no estén vacíos
        required_fields = ['nombre_asignatura', 'numero_semana', 'tema_general']
        for field in required_fields:
            if not data[field]:
                flash(f'El campo {field.replace("_", " ").title()} es obligatorio', 'error')
                return redirect(url_for('index'))
        
        # Validar que el número de semana sea válido
        try:
            semana = int(data['numero_semana'])
            if semana < 1 or semana > 52:
                flash('El número de semana debe estar entre 1 y 52', 'error')
                return redirect(url_for('index'))
        except ValueError:
            flash('El número de semana debe ser un número válido', 'error')
            return redirect(url_for('index'))
        
        # Agregar datos a la lista
        academic_data.append(data)
        flash('Datos agregados exitosamente', 'success')
        
    except Exception as e:
        flash(f'Error al procesar los datos: {str(e)}', 'error')
        app.logger.error(f'Error en add_data: {str(e)}')
    
    return redirect(url_for('view_data'))

@app.route('/view_data')
def view_data():
    """Ver todos los datos ingresados"""
    return render_template('view_data.html', data=academic_data)

@app.route('/download_csv')
def download_csv():
    """Generar y descargar archivo CSV"""
    if not academic_data:
        flash('No hay datos para exportar', 'error')
        return redirect(url_for('view_data'))
    
    try:
        # Crear archivo CSV en memoria
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Escribir encabezados
        headers = [
            'Nombre de la Asignatura',
            'Número de Semana',
            'Tema General/Módulo',
            'Temas Específicos',
            'Trabajo Individual',
            'Bibliografía Recomendada',
            'Bibliografía Complementaria',
            'Práctica Individual y Grupal',
            'Fecha de Creación'
        ]
        writer.writerow(headers)
        
        # Escribir datos
        for row in academic_data:
            writer.writerow([
                row['nombre_asignatura'],
                row['numero_semana'],
                row['tema_general'],
                row['temas_especificos'],
                row['trabajo_individual'],
                row['bibliografia_recomendada'],
                row['bibliografia_complementaria'],
                row['practica_individual_grupal'],
                row['fecha_creacion']
            ])
        
        # Preparar archivo para descarga
        output.seek(0)
        
        # Crear nombre de archivo con timestamp
        filename = f'datos_academicos_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        
        # Convertir a bytes para Flask
        csv_data = output.getvalue().encode('utf-8-sig')  # utf-8-sig para compatibilidad con Excel
        
        return send_file(
            io.BytesIO(csv_data),
            mimetype='text/csv',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        flash(f'Error al generar CSV: {str(e)}', 'error')
        app.logger.error(f'Error en download_csv: {str(e)}')
        return redirect(url_for('view_data'))

@app.route('/delete_data/<int:index>')
def delete_data(index):
    """Eliminar un registro específico"""
    try:
        if 0 <= index < len(academic_data):
            deleted_item = academic_data.pop(index)
            flash(f'Registro "{deleted_item["nombre_asignatura"]}" eliminado exitosamente', 'success')
        else:
            flash('Registro no encontrado', 'error')
    except Exception as e:
        flash(f'Error al eliminar registro: {str(e)}', 'error')
        app.logger.error(f'Error en delete_data: {str(e)}')
    
    return redirect(url_for('view_data'))

@app.route('/clear_all')
def clear_all():
    """Limpiar todos los datos"""
    global academic_data
    try:
        count = len(academic_data)
        academic_data = []
        flash(f'{count} registros eliminados exitosamente', 'success')
    except Exception as e:
        flash(f'Error al limpiar datos: {str(e)}', 'error')
        app.logger.error(f'Error en clear_all: {str(e)}')
    
    return redirect(url_for('view_data'))

@app.route('/api/stats')
def api_stats():
    """API endpoint para estadísticas básicas"""
    try:
        stats = {
            'total_registros': len(academic_data),
            'asignaturas_unicas': len(set(item['nombre_asignatura'] for item in academic_data)),
            'ultima_actualizacion': academic_data[-1]['fecha_creacion'] if academic_data else None
        }
        return stats
    except Exception as e:
        app.logger.error(f'Error en api_stats: {str(e)}')
        return {'error': 'Error al obtener estadísticas'}, 500

@app.errorhandler(404)
def not_found(error):
    """Página de error 404"""
    return render_template('error.html', 
                         error_code=404, 
                         error_message="Página no encontrada"), 404

@app.errorhandler(500)
def internal_error(error):
    """Página de error 500"""
    return render_template('error.html', 
                         error_code=500, 
                         error_message="Error interno del servidor"), 500

# Configuración para producción
if __name__ == '__main__':
    # Configuración para producción
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)