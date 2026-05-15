# Cerebellum Project - Guía de Contribución para Sebastián

Este repositorio contiene la estructura y las tareas del proyecto. Para mantener el historial limpio y trabajar de forma segura sin interferir con la rama principal (`main`), utilizaremos un flujo de trabajo basado en ramas individuales.

---

## Configuración y glujo de trabajo diario

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