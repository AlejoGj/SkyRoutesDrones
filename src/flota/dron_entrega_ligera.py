# Módulo de especialización para Dron de Entrega Ligera (Logística de Última Milla)
# Responsable: Juan Manuel Pava Higuita (Sprint 2 - HU-09, HU-10)

# ==============================================================================
# 1. IMPORTACIONES Y CONTROL DE TIPADO DIFERIDO (PEP 563 & PEP 484)
# ==============================================================================
# 'from __future__ import annotations' habilita la evaluación pospuesta de anotaciones.
# En tiempo de ejecución, los type hints se almacenan como cadenas de texto, lo que
# optimiza el rendimiento y permite referenciar clases que aún no han sido evaluadas.
from __future__ import annotations

# 'TYPE_CHECKING' es una constante booleana del módulo typing:
# - En ejecución normal del intérprete vale False (evita ejecutar importaciones internas).
# - Durante el análisis estático / autocompletado en el IDE vale True.
# SOLUCIÓN DE ARQUITECTURA A IMPORTACIÓN CIRCULAR:
# 'pedido.py' necesita importar 'Dron', y 'dron_entrega_ligera.py' necesita a 'Pedido'
# para la firma de 'ejecutar_mision(self, pedido: Pedido)'. Con este condicional rompemos
# el ciclo en runtime sin perder el tipado estático ni la ayuda del editor.
from typing import TYPE_CHECKING
from src.flota.dron import Dron
from src.excepciones.errores import ActualizarEstadoDronError

if TYPE_CHECKING:
    from src.pedidos.pedido import Pedido


# ==============================================================================
# 2. DEFINICIÓN DE CLASE Y APLICACIÓN DE PILARES DE POO
# ==============================================================================
# PILAR: HERENCIA
# 'DronEntregaLigera' hereda formalmente de la clase base abstracta 'Dron'.
# Reutiliza toda la infraestructura operativa común (telemetría, odómetro, estados
# operacionales, cálculo geodésico y retorno a base) a través de 'super()'.
class DronEntregaLigera(Dron):
    """
    Subclase especializada en el transporte rápido de suministros médicos y paquetería urgente.
    
    Características Principales:
    - Diseñado para entregas de última milla con cargas livianas (hasta 15 kg).
    - Incorpora tolva con opción de aislamiento térmico refrigerado para medicamentos/vacunas.
    - Mecanismo electromecánico de desacople rápido para entrega autónoma sin aterrizaje prolongado.
    - Tasa de consumo energético altamente eficiente (1.2% de batería por kilómetro).
    """

    # Constantes oficiales del sistema SkyRoute
    CATEGORIA_ESPECIALIZADA: str = "ENTREGA_LIGERA"
    CAPACIDAD_CARGA_DEFAULT_KG: float = 5.0

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
        mecanismo_suelta_rapida: bool = True,
    ) -> None:
        """
        Inicializa una aeronave de transporte ligero.
        
        Invoca el constructor de la clase base 'Dron' mediante 'super().__init__(...)' para
        inicializar los atributos generales del dron, y delega a sus propios setters la
        validación y asignación de sus aditamentos especializados.
        """
        # Delegación al constructor padre (Herencia)
        super().__init__(
            id_dron=id_dron,
            modelo_aeronave=modelo_aeronave,
            velocidad_promedio_kmh=velocidad_promedio_kmh,
            kilometraje_total_km=kilometraje_total_km,
            disponible=disponible,
            calculador=calculador,
        )

        # Categoría oficial fijada para compatibilidad con Pedido y SistemaCentroControl
        self.categoria = self.CATEGORIA_ESPECIALIZADA

        # PILAR: ENCAPSULAMIENTO Y DEFENSA DE DOMINIO
        # En lugar de atributos privados con doble guión (__), usamos protegidos con guión
        # simple (_) para que las subclases puedan heredar libremente sin sufrir name-mangling.
        # Las asignaciones pasan por los setters para activar las validaciones de negocio.
        self.capacidad_carga_kg = capacidad_carga_kg
        self.compartimento_refrigerado = compartimento_refrigerado
        self.mecanismo_suelta_rapida = mecanismo_suelta_rapida

    # ==========================================================================
    # 3. GETTERS Y SETTERS PROTEGIDOS (ENCAPSULAMIENTO DEFENSIVO)
    # ==========================================================================

    @property
    def capacidad_carga_kg(self) -> float:
        """Retorna el peso máximo de paquete autorizado para la tolva de este dron (kg)."""
        return self._capacidad_carga_kg

    @capacidad_carga_kg.setter
    def capacidad_carga_kg(self, valor: float) -> None:
        # Validación defensiva contra booleanos camuflados (en Python bool es subclase de int)
        if isinstance(valor, bool) or not isinstance(valor, (int, float)):
            raise TypeError(f"La capacidad de carga debe ser numérica. Recibido: {type(valor).__name__}")
        # La capacidad debe ser estrictamente positiva (un dron de transporte no puede cargar 0 kg o menos)
        if valor <= 0:
            raise ValueError(f"La capacidad de carga debe ser estrictamente mayor a 0 kg. Recibido: {valor}")
        self._capacidad_carga_kg = float(valor)

    @property
    def compartimento_refrigerado(self) -> bool:
        """Indica si el compartimento térmico refrigerado está habilitado en la aeronave."""
        return self._compartimento_refrigerado

    @compartimento_refrigerado.setter
    def compartimento_refrigerado(self, valor: bool) -> None:
        # Validación estricta de tipo booleano para prevenir cadenas ("si") o enteros (1)
        if not isinstance(valor, bool):
            raise TypeError(f"El indicador de refrigeración debe ser booleano (True/False). Recibido: {type(valor).__name__}")
        self._compartimento_refrigerado = valor

    @property
    def mecanismo_suelta_rapida(self) -> bool:
        """Indica si la aeronave cuenta con gancho de liberación rápida electromecánico."""
        return self._mecanismo_suelta_rapida

    @mecanismo_suelta_rapida.setter
    def mecanismo_suelta_rapida(self, valor: bool) -> None:
        if not isinstance(valor, bool):
            raise TypeError(f"El mecanismo de suelta rápida debe ser booleano (True/False). Recibido: {type(valor).__name__}")
        self._mecanismo_suelta_rapida = valor

    # ==========================================================================
    # 4. MÉTODOS AUXILIARES DE CONSULTA PREVIA
    # ==========================================================================

    def es_apto_carga(self, peso_carga_kg: float) -> bool:
        """
        Verificación rápida y previa para saber si el dron soporta el peso del pedido
        antes de iniciar formalmente la secuencia de despegue.
        """
        if isinstance(peso_carga_kg, bool) or not isinstance(peso_carga_kg, (int, float)):
            raise TypeError(f"El peso a consultar debe ser numérico. Recibido: {type(peso_carga_kg).__name__}")
        return 0 <= peso_carga_kg <= self._capacidad_carga_kg

    # ==========================================================================
    # 5. POLIMORFISMO Y ABSTRACCIÓN: IMPLEMENTACIÓN DEL CONTRATO ABSTRACTO
    # ==========================================================================

    def ejecutar_mision(self, pedido: Pedido) -> dict:
        """
        Ejecuta la misión de transporte ligero bajo un esquema de despacho polimórfico.
        
        FLUJO DE EJECUCIÓN:
        1. Regla de Negocio (HU-09): Valida que el peso del pedido no supere la capacidad
           máxima de la aeronave. Si la supera, se rechaza la misión con ActualizarEstadoDronError.
        2. Reutilización Base (Herencia): Invoca 'super().ejecutar_mision(pedido)' para que
           la clase base verifique autonomía de batería, disponibilidad, active motores a
           30 metros de altitud y transicione el pedido a 'EN_TRANSITO'.
        3. Especialización Polimórfica: Anexa al reporte técnico los metadatos propios de
           la entrega ligera (cadena de frío, suelta rápida y peso real transportado).
        """
        # Validación crítica de sobrepeso (Criterio de Aceptación HU-09)
        if pedido.peso_carga_kg > self._capacidad_carga_kg:
            raise ActualizarEstadoDronError(
                self.id_dron,
                f"Misión rechazada por sobrepeso: La carga de {pedido.peso_carga_kg:.1f} kg supera la capacidad máxima ({self._capacidad_carga_kg:.1f} kg)."
            )

        # Delegación a la lógica base abstracta de despegue y telemetría
        reporte_despegue = super().ejecutar_mision(pedido)

        # Registro pedagógico en consola para trazabilidad operacional
        print(f"[{self.id_dron}] Despachando paquete ligero de {pedido.peso_carga_kg:.1f} kg...")
        if self._compartimento_refrigerado:
            print(f"  -> Manteniendo cadena de frío activa para suministros termosensibles.")
        if self._mecanismo_suelta_rapida:
            print(f"  -> Sistema de suelta rápida electromecánico armado.")

        # Enriquecimiento polimórfico del reporte técnico
        reporte_despegue.update({
            "instrumental_activado": "COMPARTIMENTO_REFRIGERADO" if self._compartimento_refrigerado else "TOLVA_ESTANDAR",
            "peso_transportado_kg": pedido.peso_carga_kg,
            "mecanismo_suelta_rapida": self._mecanismo_suelta_rapida,
            "estado_especifico": "Paquete ligero asegurado en cabina",
        })
        return reporte_despegue

    def calcular_consumo_estimado(self, distancia_km: float) -> float:
        """
        PILAR: POLIMORFISMO EN CONSUMO ENERGÉTICO (HU-10)
        
        Calcula el porcentaje de batería que requerirá el viaje aplicando la tasa
        especializada para aeronaves ligeras:
            Consumo (%) = distancia_km * 1.2
        
        Si la distancia es negativa o nula, devuelve 0.0 de forma segura.
        """
        if isinstance(distancia_km, bool) or not isinstance(distancia_km, (int, float)):
            raise TypeError(f"La distancia debe ser numérica. Recibido: {type(distancia_km).__name__}")
        if distancia_km <= 0:
            return 0.0
        return float(distancia_km * 1.2)

    def inspeccionar_sistemas_especializados(self) -> str:
        """
        PILAR: POLIMORFISMO EN DIAGNÓSTICO TÉCNICO (HU-07 / HU-09)
        
        Retorna el estado de los componentes especializados de transporte ligero.
        """
        refri = "ACTIVO" if self._compartimento_refrigerado else "NO_DISPONIBLE"
        suelta = "OPERATIVO" if self._mecanismo_suelta_rapida else "NO_DISPONIBLE"
        return f"Diagnóstico: Capacidad {self._capacidad_carga_kg:.1f}kg | Refrigeración [{refri}] | Suelta Rápida [{suelta}]"

    # ==========================================================================
    # 6. REPRESENTACIÓN MULTILÍNEA Y FICHA TÉCNICA (HU-10)
    # ==========================================================================

    def __str__(self) -> str:
        """
        Sobrescribe __str__ reutilizando la ficha base de 'Dron' vía 'super().__str__()'
        e integrando de forma armónica los aditamentos especializados de transporte ligero.
        """
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
