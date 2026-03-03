# IPOR Fusion - Vault Production Validation Conditions

## Spis plikow

| # | Plik | Opis |
|---|------|------|
| 01 | [01-VAULT-CORE.md](./01-VAULT-CORE.md) | Warunki walidacji konfiguracji bazowej vaulta |
| 02 | [02-ACCESS-CONTROL.md](./02-ACCESS-CONTROL.md) | Warunki walidacji systemu rol i uprawnien |
| 03 | [03-MARKET-CONFIGURATION.md](./03-MARKET-CONFIGURATION.md) | Warunki per-market: substrates, fuses, balance fuses |
| 04 | [04-MARKET-INTERACTIONS.md](./04-MARKET-INTERACTIONS.md) | Warunki interakcji miedzy marketami (dependency graph, limity) |
| 05 | [05-FUSES-CATALOG.md](./05-FUSES-CATALOG.md) | Kompletny katalog fuse'ow z warunkami per-protokol |
| 06 | [06-WITHDRAWAL-SYSTEM.md](./06-WITHDRAWAL-SYSTEM.md) | Warunki systemu wyplat (instant, scheduled, fees) |
| 07 | [07-FEE-SYSTEM.md](./07-FEE-SYSTEM.md) | Warunki systemu oplat (performance, management, deposit) |
| 08 | [08-PRICE-ORACLE.md](./08-PRICE-ORACLE.md) | Warunki konfiguracji price oracle i feedow cenowych |
| 09 | [09-BALANCE-TRACKING.md](./09-BALANCE-TRACKING.md) | Warunki sledzenia balansow i totalAssets |
| 10 | [10-REWARDS-SYSTEM.md](./10-REWARDS-SYSTEM.md) | Warunki systemu nagrod (claim, vesting, transfer) |
| 11 | [11-CHECKLIST-PER-MARKET-TYPE.md](./11-CHECKLIST-PER-MARKET-TYPE.md) | Checklist per typ marketu (lending, DEX, staking, etc.) |
| 12 | [12-PRODUCTION-VALIDATION-FLOW.md](./12-PRODUCTION-VALIDATION-FLOW.md) | Kolejnosc walidacji na produkcji |

## Jak uzywac

1. Kazdy plik zawiera **warunki** (conditions) do sprawdzenia
2. Warunki sa podzielone na kategorie: CRITICAL / HIGH / MEDIUM
3. Kazdy warunek ma format:
   - **ID**: Unikalny identyfikator
   - **Warunek**: Co musi byc spelnione
   - **Jak sprawdzic**: Wywolanie on-chain lub metoda weryfikacji
   - **Oczekiwany wynik**: Jaki powinien byc rezultat
   - **Priorytet**: CRITICAL / HIGH / MEDIUM
