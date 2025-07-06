# Google Cloud Storage API Service

Este servicio proporciona una API RESTful robusta y segura para gestionar recursos de Google Cloud Storage (GCS), incluyendo buckets, directorios y archivos (objetos). Está construido con Python y Flask, y diseñado para un despliegue ágil y escalable en Google Cloud Run.

El servicio utiliza las mejores prácticas de seguridad, delegando la firma de URLs a la API de IAM, lo que lo hace ideal para ejecutarse en entornos de GCP sin necesidad de gestionar claves de servicio manualmente. Además, incluye soporte para CORS, permitiendo que sea consumido desde aplicaciones front-end de manera segura.

## Características

-   **Soporte para CORS:** Habilitado para permitir peticiones desde cualquier origen de front-end.
-   **Gestión de Buckets (CRUD):**
    -   Crear nuevos buckets de GCS.
    -   Listar todos los buckets de un proyecto.
    -   Obtener detalles de un bucket específico.
    -   Eliminar buckets (incluso si no están vacíos).
-   **Gestión de Directorios:**
    -   Crear directorios (simulados como objetos vacíos).
    -   Eliminar un directorio y todo su contenido.
-   **Gestión de Archivos (CRUD):**
    -   Subir archivos a un bucket, con soporte para prefijos (directorios).
    -   Listar archivos dentro de un bucket, con opción de filtrar por prefijo.
    -   Generar URLs de descarga temporales y seguras (Signed URLs V4).
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
    Para desarrollo local, usa Application Default Credentials (ADC). Tu usuario debe tener los permisos necesarios en IAM.
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
      --allow-unauthenticated # Opcional: para acceso público a la API
    ```

---

## 🚀 API Endpoints y Ejemplos de Uso (CRUD)

A continuación se muestran ejemplos usando `curl`. Reemplaza `http://localhost:8080` con la URL de tu servicio en Cloud Run.

### 🪣 Operaciones con Buckets

#### 1. Crear un Bucket
* **Endpoint:** `POST /buckets`
* **Ejemplo:**
    ```bash
    curl -X POST http://localhost:8080/buckets \
    -H "Content-Type: application/json" \
    -d '{"bucket_name": "mi-bucket-unico-12345", "location": "US-CENTRAL1"}'
    ```

#### 2. Listar Buckets
* **Endpoint:** `GET /buckets`
* **Ejemplo:**
    ```bash
    curl http://localhost:8080/buckets
    ```

#### 3. Eliminar un Bucket
* **Endpoint:** `DELETE /buckets/<bucket_name>`
* **Ejemplo:**
    ```bash
    curl -X DELETE http://localhost:8080/buckets/mi-bucket-unico-12345
    ```

### 📁 Operaciones con Directorios

#### 1. Crear un Directorio
* **Endpoint:** `POST /buckets/<bucket_name>/directories`
* **Ejemplo:**
    ```bash
    curl -X POST http://localhost:8080/buckets/mi-bucket-unico-12345/directories \
    -H "Content-Type: application/json" \
    -d '{"directory_name": "documentos/reportes/"}'
    ```

#### 2. Eliminar un Directorio y su Contenido
* **Endpoint:** `DELETE /buckets/<bucket_name>/directories/<path:directory_name>`
* **Ejemplo:**
    ```bash
    curl -X DELETE http://localhost:8080/buckets/mi-bucket-unico-12345/directories/documentos/reportes/
    ```

### 📄 Operaciones con Archivos

#### 1. Subir un Archivo a un Directorio
* **Endpoint:** `POST /buckets/<bucket_name>/files`
* **Ejemplo:**
    ```bash
    # Crea un archivo de prueba
    echo "Reporte de ventas" > reporte.pdf

    curl -X POST http://localhost:8080/buckets/mi-bucket-unico-12345/files \
    -F "file=@reporte.pdf" \
    -F "object_prefix=documentos/reportes/"
    ```

#### 2. Listar Archivos en un Directorio
* **Endpoint:** `GET /buckets/<bucket_name>/files?prefix=<prefix>`
* **Ejemplo:**
    ```bash
    curl "http://localhost:8080/buckets/mi-bucket-unico-12345/files?prefix=documentos/reportes/"
    ```

#### 3. Obtener URL de Descarga de un Archivo
* **Endpoint:** `GET /buckets/<bucket_name>/files/<path:file_name>`
* **Ejemplo:**
    ```bash
    curl http://localhost:8080/buckets/mi-bucket-unico-12345/files/documentos/reportes/reporte.pdf
    ```

#### 4. Eliminar un Archivo
* **Endpoint:** `DELETE /buckets/<bucket_name>/files/<path:file_name>`
* **Ejemplo:**
    ```bash
    curl -X DELETE http://localhost:8080/buckets/mi-bucket-unico-12345/files/documentos/reportes/reporte.pdf
    ```
