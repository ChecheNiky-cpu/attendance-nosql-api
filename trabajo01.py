import re
from pymongo import MongoClient
from datetime import datetime


class AsistenciaDB:
    def __init__(self, uri="mongodb://localhost:27017/", db_name="sistema_asistencia"):
        """Configura la conexión inicial con la base de datos."""
        try:
            self.client = MongoClient(uri, serverSelectionTimeoutMS=5000)
            self.db = self.client[db_name]
            self.usuarios = self.db['estudiantes']
            # Validamos la conexión con un ping
            self.client.admin.command('ping')
            print("Conexión establecida con MongoDB Compass.")
        except Exception as e:
            print(
                f"Error crítico: No se pudo conectar a la base de datos. {e}")
            self.client = None

    def validar_formato_run(self, run):
        patron = r'^\d{1,2}\.\d{3}\.\d{3}-[\dkK]$'
        return bool(re.match(patron, run))

    def normalizar_run(self, run):
        return run.replace(".", "").upper()

    def registrar_estudiante(self, run, nombre, carrera):
        if not self.validar_formato_run(run):
            return False, "Formato de RUN inválido (use XX.XXX.XXX-Y)."

        id_normalizado = self.normalizar_run(run)
        nuevo_doc = {
            "_id": id_normalizado,
            "nombre": nombre,
            "carrera": carrera,
            "asistencias": []
        }
        try:
            self.usuarios.insert_one(nuevo_doc)
            return True, f"Estudiante '{nombre}' registrado exitosamente."
        except Exception:
            return False, "El estudiante ya existe en la base de datos."

    def listar_estudiantes(self):
        return list(self.usuarios.find({}, {"nombre": 1, "_id": 1}))

    def marcar_asistencia(self, run, sala):
        id_normalizado = self.normalizar_run(run)
        registro = {
            "fecha": datetime.now().strftime("%Y-%m-%d"),
            "hora": datetime.now().strftime("%H:%M:%S"),
            "sala": sala
        }
        resultado = self.usuarios.update_one(
            {"_id": id_normalizado},
            {"$push": {"asistencias": registro}}
        )
        return resultado.modified_count > 0

    def eliminar_estudiante(self, run):
        """Borra permanentemente a un estudiante por su RUT."""
        id_normalizado = self.normalizar_run(run)
        resultado = self.usuarios.delete_one({"_id": id_normalizado})
        return resultado.deleted_count > 0

    def cerrar_conexion(self):
        if self.client:
            self.client.close()


"""Menu del sistema"""


def mostrar_menu():
    sistema = AsistenciaDB()
    if not sistema.client:
        return

    while True:
        print("\n" + "="*40)
        print("   SISTEMA DE ASISTENCIA ")
        print("="*40)
        print("1. Registrar Nuevo Estudiante")
        print("2. Listar Estudiantes (Resumen)")
        print("3. Marcar Asistencia")
        print("4. Eliminar Estudiante")
        print("5. Salir")

        opcion = input("\nSeleccione una opción: ")

        if opcion == "1":
            run = input("RUN (ej: 12.345.678-9): ")
            nombre = input("Nombre completo: ")
            carrera = input("Carrera: ")
            exito, mensaje = sistema.registrar_estudiante(run, nombre, carrera)
            print(mensaje)

        elif opcion == "2":
            alumnos = sistema.listar_estudiantes()
            print(f"\n{'RUT (ID)':<15} | {'NOMBRE':<30}")
            print("-" * 48)
            for a in alumnos:
                print(f"{a['_id']:<15} | {a['nombre']:<30}")

        elif opcion == "3":
            run = input("RUT del estudiante: ")
            sala = input("Nombre de la sala: ")
            if sistema.marcar_asistencia(run, sala):
                print("Asistencia registrada correctamente.")
            else:
                print("No se encontró al estudiante. Verifique el RUT.")

        elif opcion == "4":
            run = input("RUT del estudiante a eliminar: ")
            confirmar = input(f"¿Seguro que desea eliminar {run}? (s/n): ")
            if confirmar.lower() == 's':
                if sistema.eliminar_estudiante(run):
                    print("Estudiante eliminado.")
                else:
                    print("No se pudo eliminar (RUT no encontrado).")

        elif opcion == "5":
            sistema.cerrar_conexion()
            print("Conexión cerrada. ¡Éxito en tu trabajo!")
            break
        else:
            print("Opción no válida.")


if __name__ == "__main__":
    mostrar_menu()
