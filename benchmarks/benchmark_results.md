# Benchmark Results

These results are generated from the repo's sample inputs with the `small` output budget so the tradeoffs are visible.

| Case | Input Tokens | Raw Tokens | Trunc Tokens | Generic Summary Tokens | Engine Tokens | Raw Hits | Trunc Hits | Summary Hits | Engine Hits |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| logs-root-cause | 264 | 264 | 228 | 102 | 228 | 1 | 0 | 0 | 2 |
| rag-evidence-ranking | 83 | 121 | 121 | 77 | 150 | 3 | 3 | 2 | 3 |
| code-hotspot-compression | 116 | 191 | 191 | 58 | 228 | 1 | 1 | 0 | 3 |

## Notes

- `logs-root-cause`: Engine keeps the root cause section while simple truncation starts from noisy poll lines.
- `rag-evidence-ranking`: Engine keeps the incident evidence first and marks weaker evidence separately.
- `code-hotspot-compression`: Engine preserves issue, failure signal, and likely hotspot in one compact block.
- Token count is not the only success metric here. The code case shows why: the engine spends a few more tokens to keep the exact failure signal and hotspot structure that a repair agent needs.
