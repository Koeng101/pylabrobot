# Byonoy

```{toctree}
:maxdepth: 1

absorbance_96/hello-world
luminescence_96/hello-world
luminescence_96/led_bar
```

Each unit keeps its body and holders in a resource store (`unit.store`, a new in-memory one unless
one is given). A unit's body is created there at `setup` or `create_body`; the full-setup factories
(`byonoy_a96a`, `byonoy_l96`, `byonoy_l96a`) are async and create every unit at once. Plates and
units are handles in that store.

## Absorbance 96 models

| Model | PLR resource | Factory function |
|---|---|---|
| A96A full setup | `ByonoyAbsorbance96` + illumination unit | `byonoy_a96a` |
| Detection unit only | `ByonoyAbsorbance96` | `byonoy_a96a_detection_unit` |
| Illumination unit | definition, for `store.create` | `byonoy_a96a_illumination_unit` |
| Parking base (no backend) | `ByonoyAbsorbanceBaseUnit` | `byonoy_a96a_parking_unit` |
| SBS adapter | definition, for `store.create` | `byonoy_sbs_adapter` |

## Luminescence 96 models

| Model | PLR resource | Factory function |
|---|---|---|
| L96 full setup | `ByonoyLuminescenceBaseUnit` + `ByonoyLuminescence96` | `byonoy_l96` |
| L96A full setup (automate) | `ByonoyLuminescenceBaseUnit` + `ByonoyLuminescence96` | `byonoy_l96a` |
| L96 reader unit only | `ByonoyLuminescence96` | `byonoy_l96_reader_unit` |
| L96A reader unit only | `ByonoyLuminescence96` | `byonoy_l96a_reader_unit` |
| L96 base unit only | `ByonoyLuminescenceBaseUnit` | `byonoy_l96_base_unit` |
| L96A base unit only | `ByonoyLuminescenceBaseUnit` | `byonoy_l96a_base_unit` |
