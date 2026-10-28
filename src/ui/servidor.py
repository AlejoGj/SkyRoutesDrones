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
    candado: threading.RLock

    def log_message(self, format: str, *args: Any) -> None:
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
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(cuerpo)

    def do_OPTIONS(self) -> None:
        self.send_response(HTTPStatus.NO_CONTENT)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def _servir_archivo_estatico(self, nombre_relativo: str) -> None:
        ruta_limpia = nombre_relativo.lstrip("/") or "index.html"
        ruta_archivo = (DIRECTORIO_ESTATICOS / ruta_limpia).resolve()

        if (
            DIRECTORIO_ESTATICOS.resolve() not in ruta_archivo.parents
            and ruta_archivo != DIRECTORIO_ESTATICOS.resolve()
        ):
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
        longitud_hdr = self.headers.get("Content-Length", "0")
        try:
            longitud = int(longitud_hdr)
        except (ValueError, TypeError):
            raise ValueError(f"Cabecera Content-Length inválida: '{longitud_hdr}'.")
        if longitud <= 0:
            return {}
        crudo = self.rfile.read(longitud).decode("utf-8")
        if not crudo.strip():
            return {}
        cuerpo = json.loads(crudo)
        if not isinstance(cuerpo, dict):
            raise ValueError("El cuerpo de la petición debe ser un objeto JSON (diccionario clave-valor).")
        return cuerpo

    # ==========================================================================
    # DESPACHO DE PETICIONES GET Y POST
    # ==========================================================================

    def do_GET(self) -> None:
        url = urlparse(self.path)
        ruta = url.path
        params = parse_qs(url.query)

        try:
            if ruta == "/api/estado":
                with self.candado:
                    respuesta = self.controlador.obtener_estado_completo()
                self._enviar_json(respuesta)
                return

            if ruta == "/api/clima":
                nodo = params.get("nodo", [None])[0]
                with self.candado:
                    respuesta = self.controlador.consultar_clima_nodo(nodo)
                self._enviar_json(respuesta)
                return

            if ruta == "/api/polimorfismo/viabilidad":
                distancia = float(params.get("distancia_km", ["15.0"])[0])
                with self.candado:
                    respuesta = self.controlador.comparar_viabilidad_polimorfica(distancia)
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
        except (json.JSONDecodeError, ValueError) as exc:
            self._enviar_json(
                {
                    "ok": False,
                    "error_tipo": type(exc).__name__,
                    "mensaje": str(exc) if isinstance(exc, ValueError) else "El cuerpo de la petición no es un objeto JSON válido.",
                    "regla_negocio": "Protocolo de Comunicación HTTP",
                },
                HTTPStatus.BAD_REQUEST,
            )
            return

        try:
            with self.candado:
                if ruta == "/api/geocodificar":
                    respuesta = self.controlador.previsualizar_geocodificacion(
                        str(datos.get("direccion") or "")
                    )
                elif ruta == "/api/usuarios":
                    respuesta = self.controlador.gestionar_usuario(datos)
                elif ruta == "/api/flota/fabrica":
                    respuesta = self.controlador.crear_dron_desde_fabrica(datos)
                elif ruta == "/api/flota/recargar":
                    pct_raw = datos.get("porcentaje")
                    porcentaje = 100.0
                    if pct_raw not in (None, ""):
                        try:
                            porcentaje = float(pct_raw)
                        except (ValueError, TypeError):
                            porcentaje = 100.0
                    respuesta = self.controlador.recargar_bateria_dron(
                        id_dron=str(datos.get("id_dron", "")),
                        porcentaje=porcentaje,
                    )
                elif ruta == "/api/flota/telemetria":
                    respuesta = self.controlador.gestionar_telemetria_dron(datos)
                elif ruta == "/api/pedidos":
                    respuesta = self.controlador.registrar_nuevo_pedido(datos)
                elif ruta == "/api/pedidos/asignar":
                    respuesta = self.controlador.asignar_dron_pedido(
                        id_pedido=str(datos.get("id_pedido", "")).strip(),
                        id_dron=str(datos.get("id_dron", "")).strip() or None,
                    )
                elif ruta == "/api/pedidos/cancelar":
                    respuesta = self.controlador.cancelar_pedido(
                        str(datos.get("id_pedido", ""))
                    )
                elif ruta == "/api/misiones/despegar":
                    respuesta = self.controlador.despegar_mision(
                        id_pedido=str(datos.get("id_pedido", "")).strip(),
                        modo_despacho=str(datos.get("modo_despacho", "TEMPORAL")),
                        actualizar_clima=bool(datos.get("actualizar_clima", True)),
                        id_dron=str(datos.get("id_dron", "")).strip(),
                    )
                elif ruta == "/api/misiones/retorno":
                    respuesta = self.controlador.ordenar_retorno_base(
                        str(datos.get("id_dron", ""))
                    )
                elif ruta == "/api/misiones/aterrizar":
                    respuesta = self.controlador.finalizar_retorno_manual(
                        str(datos.get("id_dron", ""))
                    )
                elif ruta == "/api/simulacion/paso":
                    dt_raw = datos.get("delta_t")
                    delta_t = 30.0
                    if dt_raw not in (None, ""):
                        try:
                            delta_t = float(dt_raw)
                        except (ValueError, TypeError):
                            delta_t = 30.0

                    esc_raw = datos.get("escala_tiempo")
                    escala_tiempo = 15.0
                    if esc_raw not in (None, ""):
                        try:
                            escala_tiempo = float(esc_raw)
                        except (ValueError, TypeError):
                            escala_tiempo = 15.0

                    respuesta = self.controlador.avanzar_simulacion(
                        id_dron=datos.get("id_dron") or None,
                        delta_t=delta_t,
                        usar_reloj_real=bool(datos.get("usar_reloj_real", False)),
                        escala_tiempo=escala_tiempo,
                    )
                elif ruta == "/api/simulacion/reloj":
                    respuesta = self.controlador.controlar_reloj(
                        str(datos.get("accion", "reiniciar"))
                    )
                elif ruta == "/api/demo/preparar":
                    respuesta = self.controlador.preparar_tour_guiado()
                else:
                    self._enviar_json(
                        {"ok": False, "mensaje": f"Ruta no soportada: {ruta}"},
                        HTTPStatus.NOT_FOUND,
                    )
                    return

            self._enviar_json(respuesta, HTTPStatus.OK)

        except Exception as exc:
            self._enviar_json(self.controlador.formatear_excepcion(exc), HTTPStatus.BAD_REQUEST)


def crear_servidor(
    host: str = "127.0.0.1",
    puerto_inicial: int = 8000,
    controlador: ControladorSkyRoute | None = None,
) -> tuple[ThreadingHTTPServer, int]:
    """Crea una instancia de ThreadingHTTPServer buscando automáticamente un puerto libre."""
    instancia_ctrl = controlador if controlador is not None else ControladorSkyRoute()
    candado = threading.RLock()

    class ManejadorConfigurado(ManejadorSkyRouteHTTP):
        pass

    ManejadorConfigurado.controlador = instancia_ctrl
    ManejadorConfigurado.candado = candado

    for desplazamiento in range(15):
        puerto = puerto_inicial + desplazamiento
        try:
            servidor = ThreadingHTTPServer((host, puerto), ManejadorConfigurado)
            return servidor, puerto
        except OSError:
            continue

    raise RuntimeError(
        f"No se encontró un puerto disponible entre {puerto_inicial} y {puerto_inicial + 14}."
    )


def iniciar_aplicacion(
    host: str = "127.0.0.1",
    puerto: int = 8000,
    abrir_navegador: bool = True,
) -> None:
    """Inicia el servidor local de SkyRoute y abre la consola gráfica en el navegador predeterminado."""
    servidor, puerto_real = crear_servidor(host=host, puerto_inicial=puerto)
    url = f"http://{host}:{puerto_real}"

    print("\n" + "=" * 68)
    print("  SKYROUTE DRONES · TORRE DE CONTROL DE OPERACIONES (VALLE DE ABURRA)")
    print("  Puente Nativo Python (http.server) · Base Olaya Herrera (6.2196, -75.5868)")
    print("-" * 68)
    print(f"  Interfaz Web Local : {url}")
    print("  Para detener       : Presiona Ctrl + C en esta terminal")
    print("=" * 68 + "\n")

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
