from nicegui import ui
import webapp

if __name__ in {"__main__", "__mp_main__"}:
    print("🚀 Avvio dell'Interfaccia Grafica...")
    ui.run(title="Sala di Doppiaggio AI", port=8080)