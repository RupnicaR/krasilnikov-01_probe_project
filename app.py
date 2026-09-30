"""probe — учебный сервис для лабораторной работы № 2.

Делает ровно две вещи: отвечает строкой со словом-маркером и отдаёт JSON с
данными студента. Больше ничего от него не требуется: тема работы — упаковка
приложения в образ, а не разработка.

Перед сборкой заполните три строки ниже своими данными.
"""

import os
import socket
import time

from flask import Flask, jsonify

# ↓↓↓ заполните своими данными ↓↓↓
STUDENT = "Красильников"
GROUP = "БИСТ-23-ПО-__"
MARKER_DEFAULT = "sitelab"
BUILD_NOTE = "krasilnikov-prefix-corrected"
# ↑↑↑ заполните своими данными ↑↑↑

# Слово-маркер: из переменной окружения MARKER, а если её нет — из строки выше.
MARKER = os.environ.get("MARKER", MARKER_DEFAULT)

# Порт, на котором сервис слушает внутри контейнера. Возьмите из своего
# варианта колонку «Порт приложения внутри».
APP_PORT = int(os.environ.get("APP_PORT", "5000"))

app = Flask(__name__)
# без этого кириллица в JSON уезжает escape-последовательностями и ФИО в ответе
# не прочитать ни в браузере, ни в отчёте
app.json.ensure_ascii = False


@app.get("/")
def index():
    return "probe: %s, хост %s\n" % (MARKER, socket.gethostname())


def version():
    """Версия читается из файла, который пишется при сборке образа.

    Именно из файла, а не из переменной окружения: значение, зафиксированное
    на сборке, не должно подменяться ключом -e при запуске.
    """
    try:
        with open("/app/VERSION", encoding="utf-8") as f:
            return f.read().strip() or "dev"
    except OSError:
        return "dev"


@app.get("/me")
def me():
    return jsonify(
        student=STUDENT,
        group=GROUP,
        marker=MARKER,
        hostname=socket.gethostname(),
        version=version(),
    )


@app.get("/uptime")
def uptime():
    """Return the running container uptime in seconds."""
    try:
        with open("/proc/1/stat", encoding="ascii") as f:
            start_ticks = int(f.read().split()[21])
        hz = os.sysconf("SC_CLK_TCK")
        uptime_seconds = max(0, int(time.clock_gettime(time.CLOCK_BOOTTIME) - start_ticks / hz))
    except (OSError, ValueError, IndexError):
        uptime_seconds = 0
    return jsonify(marker=MARKER, uptime_seconds=uptime_seconds)


if __name__ == "__main__":
    # 0.0.0.0, а не 127.0.0.1: внутри контейнера localhost означает «только сам
    # контейнер», и снаружи такой сервис недоступен.
    app.run(host="0.0.0.0", port=APP_PORT)
