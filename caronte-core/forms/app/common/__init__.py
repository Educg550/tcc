from typing import _GenericAlias
import urllib.parse
import io
import csv

from flask import abort, render_template
from jinja2 import TemplateNotFound
from app.logger import Logger as Logger
from psycopg.types.json import Jsonb

from app.common.Result import Result
from app.exceptions.error_messages import FILE_ERROR, FILE_NOT_FOUND


def props(cls) -> dict:
    """
    Retorna os atributos definidos em classes
    """
    res = {}
    _dict = cls.__dict__["__annotations__"]
    names = [
        annotation
        for annotation in _dict
        if type(_dict[annotation]) is not _GenericAlias
    ]
    for name in names:
        res[name] = _dict[name]
    return res


def get_values(columns: dict, input_values: dict) -> dict:
    """
    columns = { NAME, TYPE }

    Retorna apenas os valores de `input_values` cujas chaves estão presentes em `columns` e possuem o tipo de dado correto
    """
    properties = props(columns)
    res = {}
    for column, typed in properties.items():
        if column in input_values.keys():
            if isinstance(input_values[column], typed):
                if typed is dict:
                    res[column] = Jsonb(input_values[column])
                else:
                    res[column] = input_values[column]

    return res


def parse_form_urlencoded(value, encoding="utf-8"):
    """
    Convert x-www-form-urlencoded to dict
    """
    return urllib.parse.parse_qs(str(value, encoding))


def to_csv(result: Result):
    output = io.StringIO()

    if not result.succeeded or len(result.data) <= 0:
        output.seek(0)
        return output

    writer = csv.DictWriter(output, fieldnames=result.data[0].keys())
    writer.writeheader()
    writer.writerows(result.data)

    output.seek(0)
    return output


def print_csv(csvio):
    def truncate(data, value=10):
        data = str(data)
        truncate_data = data[: value - 5] + (data[value - 5 :] and "...")
        return truncate_data.ljust(value)

    for index, row in enumerate(csvio):
        if index == 0:
            print(truncate("#", 10), end="")
        else:
            print(truncate(index, 10), end="")
        for col in row.split(","):
            print(truncate(col, 25), end="")
        print()


def remove_null_values(data):
    if isinstance(data, dict):
        return {k: remove_null_values(v) for k, v in data.items() if v is not None}
    elif isinstance(data, list):
        return [remove_null_values(item) for item in data if item is not None]
    else:
        return data


def get_ilike_filter(column, filter, exist_where=False):
    res = ""
    condition = []
    values = []
    for k, v in filter.items():
        if v:
            condition.append(f"{column} ->> unaccent(%s) ilike unaccent(%s)")
            values.append(k)
            values.append(f"%{v}%")
    if len(condition) > 0:
        if exist_where:
            res += " and "
        else:
            res += " where "
        res += " and ".join(condition)
    else:
        condition = ""

    return res, values


ALLOWED_EXTENSIONS = {"pdf"}


def allowed_file(filename, allowed_extensions=ALLOWED_EXTENSIONS):
    if "*" in allowed_extensions:
        return True
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed_extensions


def file_to_stringio(file, allowed_extensions=["*"]):
    if file.filename == "":
        return Result(message=FILE_NOT_FOUND())
    if file and allowed_file(file.filename, allowed_extensions):
        file_content_bytes = file.stream.read()
        file_content_string = file_content_bytes.decode("utf-8")
        fileContent = io.StringIO(file_content_string)

        return Result(fileContent)
    return Result(message=FILE_ERROR())


def render_template_or_404(name, **context):
    try:
        return render_template(name, **context)
    except TemplateNotFound:
        abort(404)
