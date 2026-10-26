# Tareas del Día

Aplicación de escritorio para Windows que te ayuda a administrar tus tareas pendientes del día. Hecha con Python y Tkinter, en un solo archivo y sin dependencias externas.

<!-- TODO: agrega aquí una captura de pantalla, por ejemplo: ![Captura](captura.png) -->

## Características

- **Agregar, modificar y eliminar** tareas de forma rápida.
- **Prioridades** (Alta, Media y Baja) con códigos de color.
- **Completar tareas** con un clic. Las completadas se tachan y pasan al final de la lista.
- **Barra de progreso animada** que muestra cuántas tareas llevas hechas.
- **Filtros** (Todas, Pendientes, Hechas) y **búsqueda en vivo**.
- **Deshacer** eliminaciones con `Ctrl+Z`.
- **Modo oscuro y claro**, que se recuerda al volver a abrir la app.
- **Guardado automático** de tus tareas.

## Requisitos

- Windows 10 u 11
- Python 3.9 o superior, descargado desde [python.org](https://www.python.org/downloads/). El instalador oficial ya incluye Tkinter.

No hay que instalar ninguna librería adicional.

## Cómo ejecutarla

1. Descarga `tareas_del_dia.py`.
2. Abre una terminal en la carpeta del archivo.
3. Ejecuta:

```
python tareas_del_dia.py
```

## Uso

| Acción | Cómo hacerlo |
| --- | --- |
| Agregar una tarea | Escribe en el campo superior y pulsa `Enter` o el botón **＋ Agregar** |
| Elegir prioridad al crear | Clic en el botón de color junto al campo (cambia entre Alta, Media y Baja) |
| Completar o reabrir | Clic en el círculo ○ de la tarea |
| Editar el texto | Doble clic sobre la tarea o clic en ✎. `Enter` guarda y `Esc` cancela |
| Cambiar la prioridad | Clic sobre la etiqueta de prioridad de la tarea |
| Eliminar | Clic en ✕ |
| Deshacer | `Ctrl+Z` o el botón **↶ Deshacer** |
| Eliminar todas las completadas | Botón **Limpiar completadas** (también se puede deshacer) |
| Buscar | `Ctrl+F` y escribe en el cuadro de búsqueda |
| Cambiar de tema | Botón ☾ / ☀ en la esquina superior derecha |

## Dónde se guardan los datos

Las tareas y el tema elegido se guardan automáticamente en:

```
%APPDATA%\TareasDelDia\tareas.json
```

Para hacer una copia de seguridad, copia ese archivo. Para empezar de cero, elimínalo con la app cerrada.

Las tareas no se reinician cada día: se mantienen hasta que las completes o las elimines.
