# 1. from __future__ import annotations (PEP 563):
# Hace que las anotaciones de tipo (Type Hints) se interpreten como cadenas de texto diferidas
# en tiempo de ejecución. Permite referenciar clases en firmas de métodos sin forzar su carga inmediata en memoria.
from __future__ import annotations

# 2. from typing import TYPE_CHECKING:
# 'TYPE_CHECKING' es una bandera de Python:
# - En ejecución real del programa vale False (evita ejecutar imports dentro del 'if').
# - Para el editor / IDE (autocompletado y tipado estático) vale True.
# SOLUCIÓN A IMPORTACIÓN CIRCULAR: 'pedido.py' importa a 'Dron', y 'dron.py' necesita a 'Pedido'.
# Gracias a este patrón, el ciclo se rompe completamente y el programa corre sin errores.
from typing import TYPE_CHECKING
from src.flota.dron import Dron
from src.excepciones.errores import ActualizarEstadoDronError

# 4. Condicional de Importación Diferida (Type Hinting Circular):
# 'Pedido' está en otro módulo que también importa a 'Dron'.
# Para evitar un bucle infinito de importación, le decimos al editor: "No te preocupes por esto ahora".

if TYPE_CHECKING:
    # Esta importación solo existe para que el IDE reconozca el tipo en: 'ejecutar_mision(self, pedido: Pedido)'
    from src.pedidos.pedido import Pedido
    
class DronEntregaLigera(Dron):
    CATEGORIA_ESPECIALIZADA = "ENTREGA_LIGERA"
    CAPACIDAD_CARGA_DEFAULT_KG = 5.0

    def __init__(
        self,
        id_dron: str,
        modelo_aeronave: str,
        velocidad_promedio_kmh: float = 60.0,
        kilometraje_total_km: float = 0.0,
        disponible: bool = True,
        calculador=None,
        capacidad_carga_kg: float = CAPACIDAD_CARGA_DEFAULT_KG,
        compartimento_refrigerado: bool = False,
        mecanismo_suelta_rapida: bool = True
    ) -> None:
        
        # 1. Llamada correcta a los atributos del padre Dron
        super().__init__(
            id_dron=id_dron,
            modelo_aeronave=modelo_aeronave,
            velocidad_promedio_kmh=velocidad_promedio_kmh,
            kilometraje_total_km=kilometraje_total_km,
            disponible=disponible,
            calculador=calculador
        )
        
        # 2. Asignación de categoría oficial fija
        self.categoria = self.CATEGORIA_ESPECIALIZADA

        # 3. Asignación a través de los setters (para que apliquen las validaciones)
        self.capacidad_carga_kg = capacidad_carga_kg
        self.compartimento_refrigerado = compartimento_refrigerado
        self.mecanismo_suelta_rapida = mecanismo_suelta_rapida

    # --- GETTERS Y SETTERS PROTEGIDOS ---

    @property
    def capacidad_carga_kg(self) -> float:
        return self._capacidad_carga_kg

    @capacidad_carga_kg.setter
    def capacidad_carga_kg(self, valor: float) -> None:
        if isinstance(valor, bool) or not isinstance(valor, (int, float)):
            raise TypeError(f"La capacidad de carga debe ser numérica. Recibido: {type(valor).__name__}")
        if valor <= 0:
            raise ValueError(f"La capacidad de carga debe ser mayor a 0 kg. Recibido: {valor}")
        self._capacidad_carga_kg = float(valor)

    @property
    def compartimento_refrigerado(self) -> bool:
        return self._compartimento_refrigerado

    @compartimento_refrigerado.setter
    def compartimento_refrigerado(self, valor: bool) -> None:
        if not isinstance(valor, bool):
            raise TypeError(f"El indicador de refrigeración debe ser booleano. Recibido: {type(valor).__name__}")
        self._compartimento_refrigerado = valor

    @property
    def mecanismo_suelta_rapida(self) -> bool:
        return self._mecanismo_suelta_rapida

    @mecanismo_suelta_rapida.setter
    def mecanismo_suelta_rapida(self, valor: bool) -> None:
        if not isinstance(valor, bool):
            raise TypeError(f"El mecanismo de suelta rápida debe ser booleano. Recibido: {type(valor).__name__}")
        self._mecanismo_suelta_rapida = valor
        
    def ejecutar_mision(self, pedido: Pedido) -> dict:
        # Validación de sobrepeso (Criterio clave HU-09)
        if pedido.peso_carga_kg > self._capacidad_carga_kg:
            raise ActualizarEstadoDronError(
                self.id_dron,
                f"Misión rechazada por sobrepeso: La carga de {pedido.peso_carga_kg:.1f} kg supera la capacidad máxima ({self._capacidad_carga_kg:.1f} kg)."
            )

        # Invocamos la lógica común de despegue y telemetría de la clase base
        reporte_despegue = super().ejecutar_mision(pedido)

        print(f"[{self.id_dron}] Despachando paquete ligero de {pedido.peso_carga_kg:.1f} kg...")
        if self._compartimento_refrigerado:
            print(f"  -> Manteniendo cadena de frío activa para suministros termosensibles.")
        if self._mecanismo_suelta_rapida:
            print(f"  -> Sistema de suelta rápida electromecánico armado.")

        # Especializamos el diccionario de resultado
        reporte_despegue.update({
            "instrumental_activado": "COMPARTIMENTO_REFRIGERADO" if self._compartimento_refrigerado else "TOLVA_ESTANDAR",
            "peso_transportado_kg": pedido.peso_carga_kg,
            "mecanismo_suelta_rapida": self._mecanismo_suelta_rapida,
            "estado_especifico": "Paquete ligero asegurado en cabina",
        })
        return reporte_despegue
    
    def calcular_consumo_estimado(self, distancia_km: float) -> float:
        if isinstance(distancia_km, bool) or not isinstance(distancia_km, (int, float)):
            raise TypeError(f"La distancia debe ser numérica. Recibido: {type(distancia_km).__name__}")
        if distancia_km <= 0:
            return 0.0
        return float(distancia_km * 1.2)
    
    def inspeccionar_sistemas_especializados(self) -> str:
        refri = "ACTIVO" if self._compartimento_refrigerado else "NO_DISPONIBLE"
        suelta = "OPERATIVO" if self._mecanismo_suelta_rapida else "NO_DISPONIBLE"
        return f"Diagnóstico: Capacidad {self._capacidad_carga_kg:.1f}kg | Refrigeración [{refri}] | Suelta Rápida [{suelta}]"
    
    def es_apto_carga(self, peso_carga_kg: float) -> bool:
        """Verifica de forma previa si el dron soporta el peso de la carga."""
        if isinstance(peso_carga_kg, bool) or not isinstance(peso_carga_kg, (int, float)):
            raise TypeError(f"El peso debe ser numérico. Recibido: {type(peso_carga_kg).__name__}")
        return 0 <= peso_carga_kg <= self._capacidad_carga_kg

    def __str__(self) -> str:
        ficha_base = super().__str__().rstrip()
        ficha_sin_cierre = ficha_base.rsplit("\n", 1)[0]
        cierre = "=" * 56
        refri = "Sí" if self._compartimento_refrigerado else "No"
        suelta = "Sí" if self._mecanismo_suelta_rapida else "No"
        return (
            f"{ficha_sin_cierre}\n"
            f"  Capacidad Máxima   : {self._capacidad_carga_kg:.1f} kg\n"
            f"  Refrigeración      : [{refri}] | Suelta Rápida: [{suelta}]\n"
            f"{cierre}"
        )