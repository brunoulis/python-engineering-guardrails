# Python Engineering Guardrails — v0.1.0

Skill de ingeniería Python, con la filosofía de las otras cuatro Engineering Guardrails: **código simple, anti-slop, seguridad, contratos preservados, recursos controlados, pruebas y optimizaciones basadas en evidencias**.

Incluye los modos `audit`, `implement`, `refactor` y `deep-refactor`, y perfiles para Python general, APIs, async, ETL, ciencia de datos y Azure Databricks.

## Arquitectura sin duplicar Databricks

**Para cualquier trabajo específico de Azure Databricks es obligatoria la skill oficial [`databricks-agent-skills`](https://github.com/databricks/databricks-agent-skills)**, empezando por `databricks-core` y el perfil especializado correspondiente (`databricks-docs`, `databricks-execution-compute`, `databricks-python-sdk`, etc.). Las reglas de la plataforma viven allí. Aquí mantenemos únicamente los guardrails de Python, las hipótesis sobre consumo de memoria y el método de verificación.

Instalación recomendada del upstream oficial:

```bash
databricks aitools install
```

La dependencia **no se instala de forma automática**. Si el agente no puede verificarla, debe detener las operaciones específicas de Databricks; puede seguir haciendo auditoría Python general.

## Instalar nuestra skill

Copia esta carpeta entera a `.agents/skills/python-engineering-guardrails/` (Codex/agentes compatibles) o `.claude/skills/python-engineering-guardrails/` (Claude Code). Mantén sus subcarpetas `references/`, `tools/`, `profiles/` y demás.

## Auditor estático (Python 3.10+, sin dependencias)

```bash
python tools/py_rails.py audit /ruta/proyecto --profile python-general

python tools/py_rails.py doctor \
  --profile databricks-classic --upstream-root ~/.claude/skills

python tools/py_rails.py audit /ruta/proyecto \
  --profile databricks-classic --upstream-root ~/.claude/skills

python tools/py_rails.py audit /ruta/proyecto \
  --profile databricks-serverless --upstream-root ~/.claude/skills \
  --format json

python -m unittest discover -s tests -v
```

Solo analiza código local: **no usa Azure, no ejecuta consultas Spark, no crea clusters ni modifica el proyecto**. Sus avisos son heurísticas; conocer `collect()` no permite deducir el tamaño real del DataFrame. Admite salida JSON/SARIF, baseline opcional y puertas de calidad por severidad. Las salidas a archivo son explícitas y no se sobrescriben.

## Qué investigamos para reducir RAM

1. **Driver:** `collect`, `toPandas`, conversiones y `toLocalIterator` sobre resultados grandes.
2. **Executors:** skew, shuffle, particiones únicas, joins, grandes agrupaciones.
3. **Python workers:** UDFs, Arrow y `applyInPandas`, especialmente grupos sesgados.
4. **Spark cache:** coste, reutilización, semántica de los datos y ciclo de vida.
5. **Streaming:** estado, watermark, micro-batches y checkpoints.
6. **Python local:** colecciones, lecturas completas, colas y tareas async sin límites.

**Atención a serverless:** el 23 de octubre de 2026 se anunció la vista previa pública del caché de DataFrames, con requisitos de versión y comportamiento distinto de classic. No asumimos que `df.cache()` esté prohibido; comprobamos la versión real y la documentación vigente. Más información en `references/databricks-runtime-and-compute.md`.

## Qué se entrega

`SKILL.md`, filosofía, perfiles, contrato de integración, referencias oficiales, auditor de código Python, tests unitarios, CI GitHub, ejemplos seguros, plantilla de informe y licencia MIT para el código propio.

**Estado:** v0.1.0 probada offline. **No se han medido ahorros reales de memoria de clusters**; se necesitan pruebas autorizadas en un workspace de desarrollo para afirmarlo.
