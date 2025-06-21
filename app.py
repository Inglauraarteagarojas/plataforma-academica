from flask import Flask, render_template, request, redirect, url_for, send_file, flash, send_from_directory
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
    """Home page with the form"""
    return render_template('index.html')

@app.route('/add_data', methods=['POST'])
def add_data():
    """process form data"""
    try:
        # Obtener datos del formulario
        data = {
            'subject_name': request.form.get('subject_name', '').strip(),
            'week_number': request.form.get('week_number', '').strip(),
            'general_topic': request.form.get('general_topic', '').strip(),
            'specific_topics': request.form.get('specific_topics', '').strip(),
            'individual_work': request.form.get('individual_work', '').strip(),
            'recommended_bibliography': request.form.get('recommended_bibliography', '').strip(),
            'complementary_bibliography': request.form.get('complementary_bibliography', '').strip(),
            'individual_group_practice': request.form.get('individual_group_practice', '').strip(),
            'creation_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # Validar que los campos obligatorios no estén vacíos
        required_fields = ['subject_name', 'week_number', 'general_topic']
        for field in required_fields:
            if not data[field]:
                flash(f'The field {field.replace("_", " ").title()} is required', 'error')
                return redirect(url_for('index'))
        
        # Validar que el número de semana sea válido
        try:
            semana = int(data['nweek_number'])
            if semana < 1 or semana > 52:
                flash('The week number must be between 1 and 52', 'error')
                return redirect(url_for('index'))
        except ValueError:
            flash('The week number must be a valid number', 'error')
            return redirect(url_for('index'))
        
        # Agregar datos a la lista
        academic_data.append(data)
        flash('Data added successfully', 'success')
        
    except Exception as e:
        flash(f'Error processing data: {str(e)}', 'error')
        app.logger.error(f'Error in add_data: {str(e)}')
    
    return redirect(url_for('view_data'))

@app.route('/view_data')
def view_data():
    """Ver todos los datos ingresados"""
    return render_template('view_data.html', data=academic_data)

@app.route('/download_csv')
def download_csv():
    """Generar y descargar archivo CSV"""
    if not academic_data:
        flash('There is no data to export', 'error')
        return redirect(url_for('view_data'))
    
    try:
        # Crear archivo CSV en memoria
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Escribir encabezados
        headers = [
            'subject_name',
            'week_number',
            'general_topic',
            'specific_topics',
            'individual_work',
            'recommended_bibliography',
            'complementary_bibliography',
            'individual_group_practice',
            'creation_date'
        ]
        writer.writerow(headers)
        
        # Escribir datos
        for row in academic_data:
            writer.writerow([
                row['subject_name'],
                row['week_number'],
                row['general_topic'],
                row['specific_topics'],
                row['individual_work'],
                row['recommended_bibliography'],
                row['complementary_bibliography'],
                row['individual_group_practice'],
                row['fcreation_date']
            ])
        
        # Preparar archivo para descarga
        output.seek(0)
        
        # Crear nombre de archivo con timestamp
        filename = f'academic_data_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        
        # Convertir a bytes para Flask
        csv_data = output.getvalue().encode('utf-8-sig')  # utf-8-sig para compatibilidad con Excel
        
        return send_file(
            io.BytesIO(csv_data),
            mimetype='text/csv',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        flash(f'Error generating CSV: {str(e)}', 'error')
        app.logger.error(f'Error en download_csv: {str(e)}')
        return redirect(url_for('view_data'))

@app.route('/delete_data/<int:index>')
def delete_data(index):
    """Eliminar un registro específico"""
    try:
        if 0 <= index < len(academic_data):
            deleted_item = academic_data.pop(index)
            flash(f'Record "{deleted_item["subject_name"]}" successfully removed', 'success')
        else:
            flash('Record not found', 'error')
    except Exception as e:
        flash(f'Error deleting record: {str(e)}', 'error')
        app.logger.error(f'Error en delete_data: {str(e)}')
    
    return redirect(url_for('view_data'))

@app.route('/clear_all')
def clear_all():
    """Limpiar todos los datos"""
    global academic_data
    try:
        count = len(academic_data)
        academic_data = []
        flash(f'{count} records successfully deleted', 'success')
    except Exception as e:
        flash(f'Error clearing data: {str(e)}', 'error')
        app.logger.error(f'Error in clear_all: {str(e)}')
    
    return redirect(url_for('view_data'))

@app.route('/api/stats')
def api_stats():
    """API endpoint para estadísticas básicas"""
    try:
        stats = {
            'total_records': len(academic_data),
            'single_subjects': len(set(item['subject_name'] for item in academic_data)),
            'last_update': academic_data[-1]['creation_date'] if academic_data else None
        }
        return stats
    except Exception as e:
        app.logger.error(f'Error in api_stats: {str(e)}')
        return {'error': 'Error getting statistics'}, 500

# Ruta para servir archivos estáticos (opcional, Flask lo hace automáticamente)
@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

# Manejadores de error
@app.errorhandler(404)
def page_not_found(error):
    """Manejo de error 404"""
    return render_template('error.html', 
                         error_code=404,
                         error_message="Page not found"), 404

@app.errorhandler(500)
def internal_server_error(error):
    """Manejo de error 500"""
    return render_template('error.html', 
                         error_code=500,
                         error_message="Internal Server Error"), 500

# Asegurarse que base.html está disponible para todos los templates
@app.context_processor
def inject_base_template():
    """Inyecta variables globales a todos los templates"""
    return {
        'sitename': 'Academic Platform',
        'current_year': datetime.now().year
    }

if __name__ == '__main__':
    # Crear directorio de templates si no existe
    if not os.path.exists('templates'):
        os.makedirs('templates')
    
    port = int(os.environ.get('PORT', 5001))
    debug_mode = os.environ.get('FLASK_ENV') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug_mode)
    
