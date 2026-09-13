# Módulo de gestión y validación de usuarios
# Responsable: Valery Arboleda Ardila


class Usuario:
    ROLES_PERMITIDOS: list[str] = ['CLIENTE', 'OPERADOR_VUELO', 'ADMINISTRADOR']

    def __init__(self, id_usuario: str, nombre: str, rol: str) -> None:
        # ID_USUARIO
        if not isinstance(id_usuario, str):
            raise TypeError("El ID de usuario debe ser una cadena de texto. Por favor, intenta de nuevo")

        if not id_usuario.strip():
            raise ValueError("El ID de usuario no puede estár vacío!")
        self.id_usuario = id_usuario.strip()

        # NOMBRE
        if not isinstance(nombre, str):
            raise TypeError("El nombre debe ser una cadena de texto. Por favor, intenta de nuevo")

        if not nombre.strip():
            raise ValueError("El nombre no puede estár vacío!")
        self.nombre = nombre.strip()

        # ROL
        if not isinstance(rol, str):
            raise TypeError("El rol debe ser una cadena de texto. Por favor, intenta de nuevo")
        self.rol = rol.strip().upper()
        if not self.validar_rol():
            raise ValueError(f"El rol '{rol}' no es válido, debe ser 'CLIENTE', 'OPERADOR_VUELO' o 'ADMINISTRADOR'")

    def validar_rol(self) -> bool:
        return self.rol in self.ROLES_PERMITIDOS

    def validar_usuario(self) -> bool:
        return bool(self.id_usuario and self.nombre and self.validar_rol())

    def __str__(self) -> str:
        return f"Usuario: {self.nombre} (ID: {self.id_usuario}) - Rol: [{self.rol}]"

    def __repr__(self) -> str:
        return f"Usuario(id_usuario='{self.id_usuario}', nombre='{self.nombre}', rol='{self.rol}')"

