# ADR-007: PostgreSQL desde el arranque, tras puerto/repositorio

*Fecha: 2026-07-04*

## Contexto
La reproducibilidad/auditabilidad (NFR-2) es uno de los tres NFR estrella y descansa en dos mecánicas de base de datos: **`UNIQUE(StateKey)`** (idempotencia de corridas) e **inmutabilidad versionada** del golden set y el baseline. La filosofía walking-skeleton favorece arrancar rápido, lo que tienta a usar SQLite y migrar después. Pero el destino declarado en la arquitectura es PostgreSQL.

## Decisión
Usar **PostgreSQL 16 desde el arranque** (vía docker-compose), **no** SQLite. El acceso a datos va **tras un puerto/repositorio**: los tests unitarios corren contra un *fake* in-memory (rápidos), y los de integración/e2e contra Postgres real. Las migraciones son Alembic, ejecutadas al arranque del contenedor `app`.

## Alternativas consideradas
- **SQLite-first, migrar a Postgres al endurecer** — descartada: no ejercita de verdad la idempotencia (tipos, constraints, `ON CONFLICT`) ni la mecánica que sostiene NFR-2; arrastra el riesgo "funcionó en SQLite, falla en Postgres" justo en la capa crítica.
- **ORM sin puerto/repositorio** — descartada: acopla el core al motor y a SQLAlchemy, y elimina la posibilidad de tests unitarios rápidos contra un fake.

## Consecuencias
- ✅ NFR-2 se prueba en el motor real desde el día 1 (idempotencia por clave compuesta + versionado inmutable).
- ✅ La costura puerto/repo habilita un *fake* in-memory para unit tests veloces.
- ⚠️ Algo más de fricción local (requiere Docker/Postgres para integración).
- ⚠️ Dos suites de test (unit rápida / integración contra Postgres) que mantener.

## Estado
Aceptado
