# Verificación del deploy público

Cada generación del dashboard produce `docs/deploy_manifest.json` junto a
`docs/index.html`. El manifest registra el hash SHA-256 exacto del HTML, la
última fecha de datos y la revisión de código disponible durante el build.

Después del push, el pipeline ejecuta:

```powershell
python src/pipeline/verify_public_deploy.py
```

El probe descarga el manifest y el HTML de GitHub Pages y compara el hash. Un
resultado distinto o un HTTP no exitoso devuelve código 1 y queda visible en
el log del pipeline. GitHub Pages puede tardar en propagar el commit: el probe
no interpreta esa demora como éxito ni reintenta indefinidamente.

Para un diagnóstico manual:

```powershell
python src/pipeline/verify_public_deploy.py `
  --dashboard-url https://marianolaxague-crypto.github.io/irpm-argentina/ `
  --manifest-url https://marianolaxague-crypto.github.io/irpm-argentina/deploy_manifest.json
```

P5.3 persiste un fallo del probe como estado `FAILED` separado y reutiliza el
webhook operativo para alertar. P5.2 prueba que el artefacto público coincida
con el build que se intentó publicar.
