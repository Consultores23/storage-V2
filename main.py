import os
import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
import werkzeug.utils

# Importaciones de Google Cloud y Auth
from google.cloud import storage
from google.api_core.exceptions import NotFound, Conflict
from google.auth import compute_engine
from google.auth.transport import requests

app = Flask(__name__)
# Habilitar CORS para todas las rutas y orígenes.
# Esto es crucial para que un front-end pueda consumir esta API desde otro dominio.
CORS(app)

# Inicializar cliente de Storage. Asume que la autenticación está manejada
# por el entorno (ADC localmente, Service Account en Cloud Run).
try:
    storage_client = storage.Client()
except Exception as e:
    # Manejo de error si el cliente no puede inicializarse
    print(f"Error initializing storage client: {e}")
    storage_client = None

# Obtener el ID del proyecto desde las variables de entorno
GCP_PROJECT = os.environ.get("GCP_PROJECT")

@app.route('/')
def hello():
    return "Cloud Storage API Service is running!"

# --- Bucket Operations ---

@app.route('/buckets', methods=['POST'])
def create_bucket():
    if not storage_client:
        return jsonify({"error": "Storage client not initialized."}), 500
    data = request.get_json()
    if not data or 'bucket_name' not in data:
        return jsonify({"error": "Missing bucket_name in request body"}), 400
    
    bucket_name = data['bucket_name']
    location = data.get('location', 'US-CENTRAL1') # Default location si no se provee

    try:
        bucket = storage_client.create_bucket(bucket_name, project=GCP_PROJECT, location=location)
        return jsonify({
            "message": f"Bucket {bucket.name} created successfully.",
            "bucket_details": {"name": bucket.name, "location": bucket.location}
        }), 201
    except Conflict:
        return jsonify({"error": f"Bucket {bucket_name} already exists."}), 409
    except Exception as e:
        return jsonify({"error": f"Could not create bucket: {str(e)}"}), 500

@app.route('/buckets', methods=['GET'])
def list_buckets():
    if not storage_client:
        return jsonify({"error": "Storage client not initialized."}), 500
    try:
        buckets = storage_client.list_buckets()
        bucket_list = [{"name": bucket.name, "id": bucket.id, "location": bucket.location} for bucket in buckets]
        return jsonify({"buckets": bucket_list}), 200
    except Exception as e:
        return jsonify({"error": f"Could not list buckets: {str(e)}"}), 500

@app.route('/buckets/<bucket_name>', methods=['GET'])
def get_bucket_details(bucket_name):
    if not storage_client:
        return jsonify({"error": "Storage client not initialized."}), 500
    try:
        bucket = storage_client.get_bucket(bucket_name)
        return jsonify({
            "name": bucket.name,
            "id": bucket.id,
            "location": bucket.location,
            "time_created": bucket.time_created
        }), 200
    except NotFound:
        return jsonify({"error": f"Bucket {bucket_name} not found."}), 404
    except Exception as e:
        return jsonify({"error": f"Could not retrieve bucket: {str(e)}"}), 500

@app.route('/buckets/<bucket_name>', methods=['DELETE'])
def delete_bucket(bucket_name):
    if not storage_client:
        return jsonify({"error": "Storage client not initialized."}), 500
    try:
        bucket = storage_client.get_bucket(bucket_name)
        bucket.delete(force=True) # Se usa force=True para conveniencia en el desarrollo.
        return jsonify({"message": f"Bucket {bucket_name} deleted successfully."}), 200
    except NotFound:
        return jsonify({"error": f"Bucket {bucket_name} not found."}), 404
    except Conflict as e:
        return jsonify({"error": f"Could not delete bucket {bucket_name}. It might not be empty: {str(e)}"}), 409
    except Exception as e:
        return jsonify({"error": f"Could not delete bucket: {str(e)}"}), 500

# --- File (Object) and Directory Operations ---

@app.route('/buckets/<bucket_name>/files', methods=['POST'])
def upload_file(bucket_name):
    if not storage_client:
        return jsonify({"error": "Storage client not initialized."}), 500
    if 'file' not in request.files:
        return jsonify({"error": "No file part in the request"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    try:
        bucket = storage_client.get_bucket(bucket_name)
    except NotFound:
        return jsonify({"error": f"Bucket {bucket_name} not found."}), 404

    # El prefijo (directorio) puede venir del formulario
    object_prefix = request.form.get('object_prefix', '')
    if object_prefix and not object_prefix.endswith('/'):
        object_prefix += '/'

    if file:
        filename_secure = werkzeug.utils.secure_filename(file.filename)
        blob_name = f"{object_prefix}{filename_secure}"
        blob = bucket.blob(blob_name)
        
        try:
            blob.upload_from_file(file, content_type=file.content_type)
            return jsonify({
                "message": f"File {blob.name} uploaded successfully to {bucket_name}.",
                "file_details": {
                    "name": blob.name,
                    "bucket": blob.bucket.name,
                    "size": blob.size,
                    "content_type": blob.content_type
                }
            }), 201
        except Exception as e:
            return jsonify({"error": f"Could not upload file '{blob.name}': {str(e)}"}), 500
            
    return jsonify({"error": "File upload failed for unknown reasons."}), 500

@app.route('/buckets/<bucket_name>/files', methods=['GET'])
def list_files_in_bucket(bucket_name):
    if not storage_client:
        return jsonify({"error": "Storage client not initialized."}), 500
    prefix = request.args.get('prefix', None)
    try:
        blobs = storage_client.list_blobs(bucket_name, prefix=prefix)
        file_list = [{
            "name": blob.name,
            "size": blob.size,
            "updated": blob.updated,
            "content_type": blob.content_type
        } for blob in blobs]
        return jsonify({"files": file_list, "bucket": bucket_name, "prefix_filter": prefix}), 200
    except NotFound:
        return jsonify({"error": f"Bucket {bucket_name} not found."}), 404
    except Exception as e:
        return jsonify({"error": f"Could not list files in bucket {bucket_name}: {str(e)}"}), 500

@app.route('/buckets/<bucket_name>/files/<path:file_name>', methods=['GET'])
def download_file(bucket_name, file_name):
    if not storage_client:
        return jsonify({"error": "Storage client not initialized."}), 500
    try:
        bucket = storage_client.get_bucket(bucket_name)
    except NotFound:
        return jsonify({"error": f"Bucket {bucket_name} not found."}), 404

    blob = bucket.blob(file_name)

    if not blob.exists():
        return jsonify({"error": f"File {file_name} not found in bucket {bucket_name}."}), 404

    try:
        creds = compute_engine.Credentials()
        creds.refresh(requests.Request())
        service_account_email = creds.service_account_email

        signed_url = blob.generate_signed_url(
            version="v4",
            expiration=datetime.timedelta(minutes=60),
            method="GET",
            service_account_email=service_account_email,
            access_token=creds.token
        )

        return jsonify({
            "file_name": blob.name,
            "bucket": bucket.name,
            "download_url": signed_url,
            "size": blob.size,
            "content_type": blob.content_type
        }), 200

    except Exception as e:
        error_message = f"Could not generate signed URL for {file_name}: {str(e)}"
        print(f"ERROR: {error_message}")
        return jsonify({"error": error_message}), 500

@app.route('/buckets/<bucket_name>/files/<path:file_name>', methods=['DELETE'])
def delete_file(bucket_name, file_name):
    if not storage_client:
        return jsonify({"error": "Storage client not initialized."}), 500
    try:
        bucket = storage_client.get_bucket(bucket_name)
        blob = bucket.blob(file_name)
        if not blob.exists():
            return jsonify({"error": f"File {file_name} not found in bucket {bucket_name}."}), 404
        
        blob.delete()
        return jsonify({"message": f"File {file_name} deleted successfully from bucket {bucket_name}."}), 200
    except NotFound:
        return jsonify({"error": f"Bucket {bucket_name} not found."}), 404
    except Exception as e:
        return jsonify({"error": f"Could not delete file {file_name}: {str(e)}"}), 500

# --- Directory Operations ---

@app.route('/buckets/<bucket_name>/directories', methods=['POST'])
def create_directory(bucket_name):
    if not storage_client:
        return jsonify({"error": "Storage client not initialized."}), 500
    data = request.get_json()
    if not data or 'directory_name' not in data:
        return jsonify({"error": "Missing directory_name in request body"}), 400
    
    directory_name = data['directory_name']
    if not directory_name.endswith('/'):
        directory_name += '/'

    try:
        bucket = storage_client.get_bucket(bucket_name)
        blob = bucket.blob(directory_name)
        # Sube un objeto vacío para representar el directorio
        blob.upload_from_string('', content_type='application/x-directory')
        return jsonify({"message": f"Directory {directory_name} created successfully in {bucket_name}."}), 201
    except NotFound:
        return jsonify({"error": f"Bucket {bucket_name} not found."}), 404
    except Exception as e:
        return jsonify({"error": f"Could not create directory: {str(e)}"}), 500

@app.route('/buckets/<bucket_name>/directories/<path:directory_name>', methods=['DELETE'])
def delete_directory(bucket_name, directory_name):
    if not storage_client:
        return jsonify({"error": "Storage client not initialized."}), 500
    if not directory_name.endswith('/'):
        directory_name += '/'
    
    try:
        bucket = storage_client.get_bucket(bucket_name)
        blobs_to_delete = list(storage_client.list_blobs(bucket_name, prefix=directory_name))
        
        if not blobs_to_delete:
            return jsonify({"error": f"Directory {directory_name} not found or is already empty."}), 404

        for blob in blobs_to_delete:
            blob.delete()
            
        return jsonify({"message": f"Directory {directory_name} and all its contents deleted successfully."}), 200
    except NotFound:
        return jsonify({"error": f"Bucket {bucket_name} not found."}), 404
    except Exception as e:
        return jsonify({"error": f"Could not delete directory: {str(e)}"}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(debug=True, host='0.0.0.0', port=port)
