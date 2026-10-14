import asyncio
import sys
import ctypes
from generator import run_pipeline

def disable_quick_edit():
    """
    Deshabilita el "Modo de edición rápida" en Windows. 
    Este modo es el culpable de que la consola se quede 'pillada' (pausada)
    si haces clic sin querer dentro de la ventana negra.
    """
    if sys.platform == 'win32':
        try:
            kernel32 = ctypes.windll.kernel32
            handle = kernel32.GetStdHandle(-10) # STD_INPUT_HANDLE = -10
            mode = ctypes.c_uint32()
            kernel32.GetConsoleMode(handle, ctypes.byref(mode))
            mode.value &= ~0x0040 # ENABLE_QUICK_EDIT_MODE = 0x0040
            kernel32.SetConsoleMode(handle, mode)
        except Exception:
            pass

async def main():
    disable_quick_edit()
    print("=== INICIANDO GENERADOR DE YOUTUBE SHORTS (EJECUCION UNICA) ===")
    try:
        # Ejecuta el pipeline sin tema fijo para que busque uno nuevo automaticamente (topic=None)
        await run_pipeline(None)
        print("\n=== PROCESO COMPLETADO CON EXITO ===")
        print("El video ha sido subido y procesado.")
    except Exception as e:
        print(f"\n[ERROR CRITICO]: {e}")
        sys.exit(1)
    
    print("La ventana se cerrara automaticamente...")

if __name__ == "__main__":
    asyncio.run(main())
