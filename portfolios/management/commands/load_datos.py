from pathlib import Path
from django.core.management.base import BaseCommand
from django.conf import settings
from portfolios.services.etl_load_datos import load_datos_xlsx

class Command(BaseCommand):
    help = "Carga los datos de los portafolios desde un archivo Excel"
    def handle(self, *args, **kwargs):
        path = Path(settings.BASE_DIR) / "datos.xlsx"
        self.stdout.write(f"Cargando datos desde {path}...")
        result = load_datos_xlsx(path)
        self.stdout.write(self.style.SUCCESS(f"Datos cargados correctamente: {result}"))
