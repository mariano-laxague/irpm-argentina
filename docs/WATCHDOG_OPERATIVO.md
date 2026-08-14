# Watchdog del scheduler

El healthcheck del pipeline sólo corre si el pipeline llega a iniciarse. Este
watchdog es un proceso separado: lee el heartbeat `logs/last_run.txt` después
de la hora límite y deja evidencia en `logs/watchdog_status.json`.

## Instalación en Windows Task Scheduler

Crear una segunda tarea, independiente de `run_update.bat`:

- **Programa:** `C:\Users\Mlaxague\Projects\IEP\tasks\run_watchdog.bat`
- **Frecuencia:** lunes a viernes, 20:35 (el deadline por defecto es 20:30).
- **Resultado esperado:** código 0 únicamente si la corrida de ese día terminó
  con `OK`. Código 1 significa alerta y código 2 que además falló la entrega
  del webhook.

No programarla como paso posterior dentro de `update_daily.py`: perdería el
caso que debe detectar, cuando el pipeline o su scheduler no arrancan.

## Alerta fuera de la máquina

Configurar en la tarea del watchdog la variable de entorno
`IRPM_WATCHDOG_WEBHOOK` con la URL de un endpoint de alertas de la organización
(Slack, Teams, ntfy, PagerDuty o equivalente). Cuando el estado es `ALERT`, el
watchdog envía un POST JSON con la hora de control, el deadline, la última
ejecución y el motivo. La URL no se versiona ni se escribe en `config.ini`.

Sin esa variable el monitor igual genera estado y código de salida no cero,
pero no hay entrega externa: P5.1 no debe considerarse operativamente cerrado
hasta configurar y comprobar ese destino.

## Prueba controlada

```powershell
python src/pipeline/watchdog.py --deadline 20:30 --now 2026-08-14T20:35:00
```

Para confirmar el circuito de alertas sin alterar el heartbeat real, ejecutar
el script desde una copia temporal del repositorio o invocar `evaluate` con un
archivo de heartbeat de prueba. La suite automatizada cubre los casos previo al
deadline, falta de heartbeat, heartbeat viejo, warning y OK.
