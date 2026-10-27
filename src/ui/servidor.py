# Servidor HTTP nativo basado exclusivamente en la librería estándar (http.server)
# Puente entre la interfaz gráfica minimalista y el núcleo POO de SkyRoute

from __future__ import annotations

import argparse
import json
import sys
import threading
import webbrowser
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

# Garantizar resolución de paquete 'src' tanto con 'python -m src.ui' como con 'python src/ui/servidor.py'
RAIZ_PROYECTO = Path(__file__).resolve().parents[2]
if str(RAIZ_PROYECTO) not in sys.path:
    sys.path.insert(0, str(RAIZ_PROYECTO))

from src.ui.controlador import ControladorSkyRoute  # noqa: E402

DIRECTORIO_ESTATICOS = Path(__file__).resolve().parent / "estaticos"

TIPOS_MIME: dict[str, str] = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".svg": "image/svg+xml",
    ".png": "image/png",
    ".ico": "image/x-icon",
    ".json": "application/json; charset=utf-8",
}


class ManejadorSkyRouteHTTP(BaseHTTPRequestHandler):
    """
    Manejador HTTP orientado a objetos heredando de BaseHTTPRequestHandler (librería estándar).
    Despacha recursos estáticos locales y traduce peticiones JSON hacia ControladorSkyRoute.
    """

    controlador: ControladorSkyRoute
    candado: threading.Lock

    def log_message(self, format: str, *args: Any) -> None:
        # Silenciar trazas repetitivas de refresco en consola para mantener legibles los logs de dominio
        return

    # ==========================================================================
    # UTILIDADES DE LECTURA Y RESPUESTA HTTP
    # ==========================================================================

    def _enviar_json(self, payload: dict[str, Any], codigo_http: int = HTTPStatus.OK) -> None:
        cuerpo = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(codigo_http)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(cuerpo)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(cuerpo)

    def _servir_archivo_estatico(self, nombre_relativo: str) -> None:
        ruta_limpia = nombre_relativo.lstrip("/") or "index.html"
        ruta_archivo = (DIRECTORIO_ESTATICOS / ruta_limpia).resolve()

        # Protección contra traversal fuera de estaticos/
        if DIRECTORIO_ESTATICOS.resolve() not in ruta_archivo.parents and ruta_archivo != DIRECTORIO_ESTATICOS.resolve():
            self._enviar_json({"ok": False, "mensaje": "Acceso denegado."}, HTTPStatus.FORBIDDEN)
            return

        if not ruta_archivo.is_file():
            self._enviar_json({"ok": False, "mensaje": "Recurso no encontrado."}, HTTPStatus.NOT_FOUND)
            return

        contenido = ruta_archivo.read_bytes()
        tipo_mime = TIPOS_MIME.get(ruta_archivo.suffix.lower(), "application/octet-stream")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", tipo_mime)
        self.send_header("Content-Length", str(len(contenido)))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(contenido)

    def _leer_cuerpo_json(self) -> dict[str, Any]:
        longitud = int(self.headers.get("Content-Length", "0"))
        if longitud <= 0:
            return {}
        crudo = self.rfile.read(longitud).decode("utf-8")
        if not crudo.strip():
            return {}
        return json.loads(crudo)

    # ==========================================================================
    # DESPACHO DE PETICIONES GET Y POST
    # ==========================================================================

    def do_GET(self) -> None:
        url = urlparse(self.path)
        ruta = url.path

        try:
            if ruta == "/api/estado":
                with self.candado:
                    respuesta = self.controlador.obtener_estado_completo()
                self._enviar_json(respuesta)
                return

            if ruta == "/api/ruta-preview":
                params = parse_qs(url.query)
                id_dron = params.get("id_dron", ["DR-02"])[0]
                lat = float(params.get("lat", ["6.2620"])[0])
                lon = float(params.get("lon", ["-75.5780"])[0])
                with self.candado:
                    respuesta = self.controlador.calcular_preview_ruta(id_dron, lat, lon)
                self._enviar_json(respuesta)
                return

            if ruta in ("/", "/index.html"):
                self._servir_archivo_estatico("index.html")
                return

            self._servir_archivo_estatico(ruta)

        except Exception as exc:
            self._enviar_json(self.controlador.formatear_excepcion(exc), HTTPStatus.BAD_REQUEST)

    def do_POST(self) -> None:
        url = urlparse(self.path)
        ruta = url.path

        try:
            datos = self._leer_cuerpo_json()
        except json.JSONDecodeError:
            self._enviar_json(
                {
                    "ok": False,
                    "error_tipo": "FormatoJSONError",
                    "mensaje": "El cuerpo de la petición no es un objeto JSON válido.",
                    "regla_negocio": "Protocolo de Comunicación",
                },
                HTTPStatus.BAD_REQUEST,
            )
            return

        try:
            with self.candado:
                if ruta == "/api/sincronizar":
                    respuesta = self.controlador.sincronizar_flota(
                        factor_tiempo=float(datos.get("factor_tiempo", 1.0)),
                        paso_fijo_seg=datos.get("paso_fijo_seg"),
                        consultar_clima=bool(datos.get("consultar_clima", False)),
                    )
                elif ruta == "/api/pedidos":
                    respuesta = self.controlador.registrar_nuevo_pedido(datos)
                elif ruta == "/api/pedidos/asignar":
                    respuesta = self.controlador.asignar_dron(str(datos.get("id_pedido", "")))
                elif ruta == "/api/pedidos/despachar":
                    respuesta = self.controlador.iniciar_vuelo_mision(
                        id_pedido=str(datos.get("id_pedido", "")),
                        modo=str(datos.get("modo", "SIMULADO")),
                    )
                elif ruta == "/api/drones/retorno":
                    respuesta = self.controlador.ordenar_retorno_base(str(datos.get("id_dron", "")))
                elif ruta == "/api/drones/aterrizar":
                    respuesta = self.controlador.finalizar_retorno_dron(str(datos.get("id_dron", "")))
                elif ruta == "/api/drones/recargar":
                    respuesta = self.controlador.recargar_bateria_base(str(datos.get("id_dron", "")))
                elif ruta == "/api/telemetria":
                    respuesta = self.controlador.actualizar_telemetria_manual(datos)
                elif ruta == "/api/usuarios":
                    respuesta = self.controlador.gestionar_usuario(datos)
                else:
                    self._enviar_json({"ok": False, "mensaje": f"Ruta no soportada: {ruta}"}, HTTPStatus.NOT_FOUND)
                    return

            self._enviar_json(respuesta, HTTPStatus.OK)

        except Exception as exc:
            self._enviar_json(self.controlador.formatear_excepcion(exc), HTTPStatus.BAD_REQUEST)


def crear_servidor(host: str = "127.0.0.1", puerto_inicial: int = 8000) -> tuple[ThreadingHTTPServer, int]:
    """Crea una instancia de ThreadingHTTPServer buscando automáticamente un puerto libre."""
    controlador = ControladorSkyRoute()
    candado = threading.Lock()

    class ManejadorConfigurado(ManejadorSkyRouteHTTP):
        pass

    ManejadorConfigurado.controlador = controlador
    ManejadorConfigurado.candado = candado

    for desplazamiento in range(15):
        puerto = puerto_inicial + desplazamiento
        try:
            servidor = ThreadingHTTPServer((host, puerto), ManejadorConfigurado)
            return servidor, puerto
        except OSError:
            continue

    raise RuntimeError(f"No se encontró un puerto disponible entre {puerto_inicial} y {puerto_inicial + 14}.")


def iniciar_aplicacion(
    host: str = "127.0.0.1",
    puerto: int = 8000,
    abrir_navegador: bool = True,
) -> None:
    """Inicia el servidor local de SkyRoute y abre la consola gráfica en el navegador predeterminado."""
    servidor, puerto_real = crear_servidor(host=host, puerto_inicial=puerto)
    url = f"http://{host}:{puerto_real}"

    print("\n" + "=" * 64)
    print("  SKYROUTES DRONES · INTERFAZ DE GESTIÓN Y TELEMETRÍA")
    print("  Puente Nativo Python (http.server) · Backend POO Intacto")
    print("-" * 64)
    print(f"  Dirección local : {url}")
    print("  Para detener    : Presiona Ctrl + C en esta terminal")
    print("=" * 64 + "\n")

    if abrir_navegador:
        threading.Timer(0.4, lambda: webbrowser.open(url)).start()

    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\n[UI] Cerrando servidor gráfico SkyRoute de forma segura...")
    finally:
        servidor.server_close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Servidor UI nativo para SkyRoute Drones.")
    parser.add_argument("--host", default="127.0.0.1", help="Host de escucha local (default: 127.0.0.1)")
    parser.add_argument("--puerto", type=int, default=8000, help="Puerto HTTP inicial (default: 8000)")
    parser.add_argument(
        "--sin-navegador",
        action="store_true",
        help="No abrir automáticamente el navegador web al iniciar",
    )
    args = parser.parse_args()
    iniciar_aplicacion(host=args.host, puerto=args.puerto, abrir_navegador=not args.sin_navegador)


if __name__ == "__main__":
    main()
