# Groups — (27 March 2026)

**`group` and `group_det` columns — all tasks (`saves.py`, 27 May 2026):**

Added a `group_det` column (next to `group`) and a `location` column (next to `language`) across all 7 task saves.py files: `2d`, `ccc`, `ccs`, `ied`, `nBack`, `sd`, `template`.

The `group` column now stores an **abbreviated** label derived from `cfg.GROUP` (the numeric value entered at task start):

| `cfg.GROUP` | `group`  | `group_det` |
|-------------|----------|-------------|
| 1           | Pilot    | Pilot       |
| 2           | Ctrl     | Control     |
| 3           | Pat      | CD          |
| 4           | Pat      | Stroke      |
| 5           | Pat      | Tumor       |
| 6           | Pat      | Other       |
| (other/NA)  | NA       | NA          |

- **`group`**: coarse label — `"Pilot"`, `"Ctrl"`, or `"Pat"`.
- **`group_det`**: detailed label — distinguishes patient subgroups (`CD`, `Stroke`, `Tumor`, `Other`).
- Both values are computed by `_group_label()` / `_group_det_label()`.

The `location` column stores the participant's location derived from `cfg.PID[0]`:

| `PID[0]`    | `location` |
|-------------|------------|
| U / u       | USA        |
| M / m       | MEX        |
| (other)     | NA         |

---

# Cerebellum Project - Guía de Contribución para Sebastián

Este repositorio contiene la estructura y las tareas del proyecto. Para mantener el historial limpio y trabajar de forma segura sin interferir con la rama principal (`main`), utilizaremos un flujo de trabajo basado en ramas individuales.

---

## Configuración y flujo de trabajo diario

Antes de empezar a trabajar por primera vez, debes asegurarte de estar ubicado en tu rama asignada de manera local. Abre la terminal en la carpeta del proyecto y ejecuta:

```bash
# 1. Traer la información actualizada de las ramas de GitHub
git fetch

# 2. Cambiarte a tu rama de trabajo independiente
git checkout sebastian

##Asegúrate de que en la esquina inferior izquierda de VS Code o en tu terminal aparezca el nombre de la rama sebastian antes de realizar cualquier cambio.

# 3. Antes de tocar el código, revisa si hay cambios en el repositorio remoto y confirma tu estado actual

git fetch
git status

# 4. Sincronizar repositorio local y luego relaizar modificaciones

 git pull origin sebastian

 # 5. Guardar y subir cambios 

 # A. Añadir todas las modificaciones al área de preparación
git add .

# B. Registrar el commit con un mensaje descriptivo en inglés de lo que hiciste
git commit -m "Breve descripcion de los cambios que hiciste"

# C. Subir los cambios exclusivamente a tu rama en GitHub
git push origin sebastian

## Nunca realices git push origin main directamente. Todos tus avances deben vivir en la rama sebastian.