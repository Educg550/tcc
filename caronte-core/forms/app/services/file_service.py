from flask_babel import gettext
import time
import os
import socket
import tempfile
import uuid
from app.config import load_config
import magic
from werkzeug.utils import secure_filename

from app.logger import Logger
from app.common.Result import Result

ALLOWED_EXTENSIONS = {
    "pdf": "application/pdf"
}
MAX_SIZE = 1 * 1024 * 1024

SHARED_TMP = "/shared/tmp"
UPLOAD_FOLDER = "/shared/uploads"
CLAMD_SOCKET = "/run/clamav/clamd.sock"

config = load_config()

def is_valid_file_type(ext: str, mime: str, allowed: dict) -> bool:
    return allowed.get(ext) == mime

def clean_old_files(directory, max_age_minutes=10):
    now = time.time()
    deleted = 0

    try:
        for filename in os.listdir(directory):
            filepath = os.path.join(directory, filename)
            if os.path.isfile(filepath):
                modified_time = os.path.getmtime(filepath)
                age_minutes = (now - modified_time) / 60
                if age_minutes > max_age_minutes:
                    os.remove(filepath)
                    deleted += 1
        if deleted > 0:
            Logger.print.info(f"[Limpeza] {deleted} arquivo(s) antigos removidos de {directory}")
    except Exception as e:
        Logger.print.warning(f"[Limpeza] Erro ao limpar arquivos antigos: {e}")

def scan_tpc_file_with_clamav(docker_file_path: str, socket_path=CLAMD_SOCKET):
    try:
        if not os.path.exists(socket_path):
            raise FileNotFoundError(f"Socket não encontrado em {socket_path}")

        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
            s.connect(socket_path)
            cmd = f'nSCAN {docker_file_path}\n'
            s.sendall(cmd.encode())

            chunks = []
            while True:
                chunk = s.recv(4096)
                if not chunk:
                    break
                chunks.append(chunk.decode())

        response = ''.join(chunks).strip()
        Logger.print.info(f"[ClamAV] Resposta: {response}")

        if "OK" in response:
            return True
        elif "FOUND" in response:
            return False
        else:
            raise RuntimeError(f"Resposta inesperada do ClamAV: {response}")
    except Exception as e:
        raise RuntimeError(f"Erro ao conectar com ClamAV: {e}")

def process_file_field(request_files, field, allowed_extensions = ALLOWED_EXTENSIONS, max_size = MAX_SIZE):
    Result(message="Ocorreu uma falha ao processar o arquivo")

    clean_old_files(directory=SHARED_TMP)
    
    uploaded_file = request_files.get(field["name"])
    if (not uploaded_file or not uploaded_file.filename):
        if not field.get("required", False):
            return Result("")
        return Result(message=f"Arquivo inválido no campo {field['label']}")

    file_data = uploaded_file.read()

    if len(file_data) >= max_size:
        return Result(message=f"Arquivo muito grande no campo {field['label']}")
    
    mime = magic.from_buffer(file_data, mime=True)
    ext = uploaded_file.filename.rsplit(".", 1)[-1].lower()
    if not is_valid_file_type(ext, mime, allowed_extensions):
        return Result(message=f"Tipo de arquivo no campo {field['label']} não permitido")

    safe_name = secure_filename(uploaded_file.filename)
    ext = os.path.splitext(safe_name)[1]
    unique_prefix = uuid.uuid4().hex
    unique_name = f"{unique_prefix}_{safe_name}"

    if "USE_CLAMAV" in config:
        os.makedirs(SHARED_TMP, exist_ok=True)
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext, dir=SHARED_TMP) as tmp:
            tmp.write(file_data)
            temp_path = tmp.name
        os.chmod(temp_path, 0o644)

        try:
            if not scan_tpc_file_with_clamav(temp_path):
                os.remove(temp_path)
                return Result(message=gettext("O arquivo enviado no campo %(label)s foi rejeitado como malicioso.", label = field['label']))
        except Exception as exception:
            if os.path.isfile(temp_path):
                os.remove(temp_path)
            Logger.print.warning(exception)
            return Result(message=gettext("Ocorreu uma falha ao se conectar com o servidor. Tente novamente mais tarde."))
        finally:
            try:
                os.remove(temp_path)
            except FileNotFoundError:
                # Arquivo já não existe
                pass
            except PermissionError as e:
                Logger.print.error(f"{temp_path}: {e}")

    final_path = os.path.join(UPLOAD_FOLDER, unique_name)
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    with open(final_path, "wb") as f:
        f.write(file_data)

    return Result(unique_name)

def handle_download_file(db, response_token, filename) -> Result:
    safe_name = secure_filename(filename)

    res = get_stringio_file(db, response_token, safe_name)

    if not res.succeeded:
        return Result(message=gettext("Ocorreu uma falha ao fazer download do arquivo"))

    return Result({
        "directory": UPLOAD_FOLDER,
        "path": filename,
        "as_attachment": False,
        "download_name": filename.rsplit("_", 1)[-1]
    })

def get_stringio_file(db, token, filename):
    sql_string = '''
        select 1 from responses
        inner join form_response
            on responses.response_id = form_response.id
        where 
            form_response.token = %s and
            responses.value = %s
        limit 1
    '''

    res = None
    with db.transaction() as f:
        res = f.sql(sql_string, (token, filename,), callback=lambda x : x.fetchone())

    return Result(res)

def handle_request_files(fields, section_info, form_data, request_files):
    for field in fields:
        if field["type"] == "File":
            partial_response_field = next(iter([ partial_response for partial_response in section_info["partial_responses"] if partial_response["field_id"] == field["id"] ]), None)
            response_field = None
            if partial_response_field:
                response_field = partial_response_field.get("value")

            if field["name"] not in request_files and response_field:
                # ja foi enviado e nao editado
                form_data[field["name"]] = response_field
                continue

            last_file = None
            if field["name"] in request_files and response_field:
                # ja foi enviado e editado
                last_file = response_field
                
            output_filename = process_file_field(request_files, field)
            if not output_filename.succeeded:
                return Result(True, message=output_filename.message)
            
            if last_file:
                path = os.path.join(UPLOAD_FOLDER, last_file)
                if os.path.isfile(path):
                    os.remove(path)
                Logger.print.info(f"[Limpeza] {last_file} arquivo atualizado removido de {UPLOAD_FOLDER}")

            form_data[field["name"]] = output_filename.data
    return Result(True)

def remove_request_files(db, fields, response_token, filename):
    sql_string = '''
        select 
            responses.id 
        from responses
        inner join form_response
            on form_response.id = responses.response_id
        where responses.field_id = %s   
            and form_response.token = %s
            and responses.value = %s
    '''

    with db.transaction() as f:
        f.sql_dict(sql_string, (fields.get("id"), response_token, filename, ), callback=lambda x : x.fetchone())

    path = os.path.join(UPLOAD_FOLDER, filename)
    if os.path.isfile(path):
        os.remove(path)

    return Result(True)