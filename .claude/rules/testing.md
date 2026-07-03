# Convenciones de Testing

- **Framework:** pytest.
- **Property-Based Testing (PBT):** activo **parcial** en el núcleo determinista (extensión aprobada en Requirements). Usar `hypothesis` para invariantes del cálculo de recall por span, el gate de no-regresión y el localizador de capa.
- **Cada test cubre:** happy path, errores y edge cases.
- **Nombres descriptivos:** "recall_por_span acierta cuando el chunk cubre el span dorado", "el gate bloquea el deploy cuando la variante no supera el baseline con significancia".
- **Factories, no hardcode:** usar fábricas para golden sets, chunks y resultados de eval; no incrustar datos mágicos.
- **Determinista vs. LLM:** el `recall` se **recomputa** en el test (es determinista) — nunca "se cree". Lo que depende del LLM-judge se testea con casos fijos/mocks y se mide acuerdo juez-vs-humano aparte.
- **Regresiones inyectadas:** incluir tests que inyecten una regresión conocida y verifiquen que el gate/revert la atrapa (0 no detectadas dentro de cobertura).
