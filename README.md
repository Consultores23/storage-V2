# Google Cloud Storage API Service

Este servicio proporciona una API RESTful robusta y segura para gestionar recursos de Google Cloud Storage (GCS), incluyendo buckets y archivos (objetos). Está construido con Python y Flask, y diseñado para un despliegue ágil y escalable en Google Cloud Run.

El servicio utiliza las mejores prácticas de seguridad, delegando la firma de URLs a la API de IAM, lo que lo hace ideal para ejecutarse en entornos de GCP sin necesidad de gestionar claves de servicio manualmente.

## Características

-   **Gestión de Buckets (CRUD):**
    -   Crear nuevos buckets de GCS.
    -   Listar todos los buckets de un proyecto.
    -   Obtener detalles de un bucket específico.
    -   Eliminar buckets.
-   **Gestión de Archivos y Directorios (CRUD):**
    -   Subir archivos a un bucket, con soporte para prefijos (directorios).
    -   Listar archivos dentro de un bucket, con opción de filtrar por prefijo.
    -   Generar URLs de descarga temporales y seguras (Signed URLs).
    -   Eliminar archivos de un bucket.

---

## Prerrequisitos

-   Python 3.9+
-   Docker
-   Google Cloud SDK (`gcloud` CLI)
-   Un proyecto de Google Cloud con las APIs de **Cloud Storage**, **Cloud Run** y **IAM Credentials** habilitadas.

---

## Configuración Local

1.  **Clonar el repositorio:**
    ```bash
    git clone <tu-repositorio>
    cd <nombre-del-directorio>
    ```

2.  **Crear y activar un entorno virtual:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # En Windows: venv\Scripts\activate
    ```

3.  **Instalar dependencias:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Autenticación de Google Cloud:**
    Para desarrollo local, usa Application Default Credentials (ADC):
    ```bash
    gcloud auth application-default login
    ```

5.  **Establecer variables de entorno:**
    ```bash
    export GCP_PROJECT="tu-id-de-proyecto-gcp"
    export PORT=8080
    ```

6.  **Ejecutar la aplicación Flask:**
    ```bash
    python main.py
    ```
    El servicio estará disponible en `http://localhost:8080`.

---

## Despliegue en Google Cloud Run

1.  **Configurar `gcloud`:**
    ```bash
    gcloud auth login
    gcloud config set project tu-id-de-proyecto-gcp
    ```

2.  **Construir y subir la imagen a Artifact Registry:**
    ```bash
    # Configurar Docker con gcloud
    gcloud auth configure-docker us-central1-docker.pkg.dev

    # Construir la imagen
    docker build -t us-central1-docker.pkg.dev/tu-id-de-proyecto-gcp/tu-repo/gcs-api-service:latest .

    # Subir la imagen
    docker push us-central1-docker.pkg.dev/tu-id-de-proyecto-gcp/tu-repo/gcs-api-service:latest
    ```

3.  **Desplegar en Cloud Run:**
    **Importante:** Asegúrate de que el Service Account de Cloud Run tenga los roles **`Storage Admin`** y **`Service Account Token Creator`**.
    ```bash
    gcloud run deploy gcs-api-service \
      --image us-central1-docker.pkg.dev/tu-id-de-proyecto-gcp/tu-repo/gcs-api-service:latest \
      --platform managed \
      --region us-central1 \
      --set-env-vars GCP_PROJECT="tu-id-de-proyecto-gcp" \
      --allow-unauthenticated # Opcional: para acceso público
    ```

---

## 🚀 API Endpoints y Ejemplos de Uso (CRUD)

A continuación se muestran ejemplos usando `curl`. Reemplaza `http://localhost:8080` con la URL de tu servicio en Cloud Run.

### 🪣 Operaciones con Buckets

#### 1. Crear un nuevo Bucket (Create)
Crea un nuevo bucket en tu proyecto de GCP.
* **Endpoint:** `POST /buckets`
* **Ejemplo:**
    ```bash
    curl -X POST http://localhost:8080/buckets \
    -H "Content-Type: application/json" \
    -d '{
        "bucket_name": "mi-bucket-unico-para-pruebas-12345",
        "location": "US-CENTRAL1"
    }'
    ```
* **Respuesta Exitosa (201 Created):**
    ```json
    {
      "bucket_details": {
        "location": "US-CENTRAL1",
        "name": "mi-bucket-unico-para-pruebas-12345"
      },
      "message": "Bucket mi-bucket-unico-para-pruebas-12345 created successfully."
    }
    ```

#### 2. Listar todos los Buckets (Read)
Obtiene una lista de todos los buckets en el proyecto.
* **Endpoint:** `GET /buckets`
* **Ejemplo:**
    ```bash
    curl http://localhost:8080/buckets
    ```
* **Respuesta Exitosa (200 OK):**
    ```json
    {
      "buckets": [
        {
          "id": "mi-bucket-unico-para-pruebas-12345",
          "location": "US-CENTRAL1",
          "name": "mi-bucket-unico-para-pruebas-12345"
        }
      ]
    }
    ```

#### 3. Obtener detalles de un Bucket (Read)
Recupera la información de un bucket específico.
* **Endpoint:** `GET /buckets/<bucket_name>`
* **Ejemplo:**
    ```bash
    curl http://localhost:8080/buckets/mi-bucket-unico-para-pruebas-12345
    ```
* **Respuesta Exitosa (200 OK):**
    ```json
    {
      "id": "mi-bucket-unico-para-pruebas-12345",
      "location": "US-CENTRAL1",
      "name": "mi-bucket-unico-para-pruebas-12345",
      "time_created": "2025-06-07T03:00:00.123Z"
    }
    ```

#### 4. Eliminar un Bucket (Delete)
Borra un bucket. Debe estar vacío.
* **Endpoint:** `DELETE /buckets/<bucket_name>`
* **Ejemplo:**
    ```bash
    curl -X DELETE http://localhost:8080/buckets/mi-bucket-unico-para-pruebas-12345
    ```
* **Respuesta Exitosa (200 OK):**
    ```json
    {
      "message": "Bucket mi-bucket-unico-para-pruebas-12345 deleted successfully."
    }
    ```

### 📄 Operaciones con Archivos y Directorios

#### 1. Subir un archivo (Create)
Sube un archivo a la raíz del bucket.
* **Endpoint:** `POST /buckets/<bucket_name>/files`
* **Ejemplo:**
    ```bash
    # Crea un archivo de prueba
    echo "Hola Mundo" > hola.txt

    curl -X POST http://localhost:8080/buckets/mi-bucket-unico-para-pruebas-12345/files \
    -F "file=@hola.txt"
    ```
* **Respuesta Exitosa (201 Created):**
    ```json
    {
      "message": "File hola.txt uploaded successfully to mi-bucket-unico-para-pruebas-12345.",
      "file_details": {
          "name": "hola.txt",
          "bucket": "mi-bucket-unico-para-pruebas-12345",
          "size": 11,
          "content_type": "text/plain"
      }
    }
    ```

#### 2. Subir un archivo a un Directorio (Create)
Para simular un directorio, se sube el archivo con un prefijo.
* **Endpoint:** `POST /buckets/<bucket_name>/files`
* **Ejemplo:**
    ```bash
    # Crea un archivo de prueba
    echo "Reporte de ventas" > reporte.pdf

    # Sube el archivo al "directorio" documentos/reportes/
    curl -X POST http://localhost:8080/buckets/mi-bucket-unico-para-pruebas-12345/files \
    -F "file=@reporte.pdf" \
    -F "object_prefix=documentos/reportes/"
    ```
* **Respuesta Exitosa (201 Created):**
    ```json
    {
        "message": "File documentos/reportes/reporte.pdf uploaded successfully to mi-bucket-unico-para-pruebas-12345."
    }
    ```

#### 3. Listar archivos en un Bucket (Read)
Lista todos los objetos dentro de un bucket.
* **Endpoint:** `GET /buckets/<bucket_name>/files`
* **Ejemplo:**
    ```bash
    curl http://localhost:8080/buckets/mi-bucket-unico-para-pruebas-12345/files
    ```
* **Respuesta Exitosa (200 OK):**
    ```json
    {
      "files": [
        { "name": "hola.txt", "size": 11, ... },
        { "name": "documentos/reportes/reporte.pdf", "size": 18, ... }
      ],
      "bucket": "mi-bucket-unico-para-pruebas-12345",
      "prefix_filter": null
    }
    ```

#### 4. Listar archivos en un Directorio (Read)
Filtra los objetos por un prefijo para listar el contenido de un "directorio".
* **Endpoint:** `GET /buckets/<bucket_name>/files?prefix=<prefix>`
* **Ejemplo:**
    ```bash
    curl "http://localhost:8080/buckets/mi-bucket-unico-para-pruebas-12345/files?prefix=documentos/reportes/"
    ```
* **Respuesta Exitosa (200 OK):**
    ```json
    {
      "files": [
        { "name": "documentos/reportes/reporte.pdf", "size": 18, ... }
      ],
      "bucket": "mi-bucket-unico-para-pruebas-12345",
      "prefix_filter": "documentos/reportes/"
    }
    ```

#### 5. Obtener URL de Descarga de un Archivo (Read)
Genera una URL firmada (válida por 60 minutos) para descargar un archivo de forma segura.
* **Endpoint:** `GET /buckets/<bucket_name>/files/<path:file_name>`
* **Ejemplo:**
    ```bash
    curl http://localhost:8080/buckets/mi-bucket-unico-para-pruebas-12345/files/documentos/reportes/reporte.pdf
    ```
* **Respuesta Exitosa (200 OK):**
    ```json
    {
      "file_name": "documentos/reportes/reporte.pdf",
      "bucket": "mi-bucket-unico-para-pruebas-12345",
      "download_url": "https://storage.googleapis.com/...",
      "size": 18,
      "content_type": "application/pdf"
    }
    ```

#### 6. Eliminar un Archivo (Delete)
Borra un objeto específico del bucket.
* **Endpoint:** `DELETE /buckets/<bucket_name>/files/<path:file_name>`
* **Ejemplo:**
    ```bash
    curl -X DELETE http://localhost:8080/buckets/mi-bucket-unico-para-pruebas-12345/files/documentos/reportes/reporte.pdf
    ```
* **Respuesta Exitosa (200 OK):**
    ```json
    {
      "message": "File documentos/reportes/reporte.pdf deleted successfully from bucket mi-bucket-unico-para-pruebas-12345."
    }
    ```
