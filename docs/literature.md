# Literature review (Chapter 2)

**Scope:** product-level **demand forecasting** from clickstream behaviour — predict next-day purchase count per `(product_id, date)`.

This document has four parts: peer-reviewed references, data sources (Methodology chapter only), comparative analysis table, and themed review prose.

---

## 1. Reference list (15 papers)

Cite in Chapter 2. Grouped by role in this dissertation.

### A. Clickstream → behaviour (4)

**[1] Tokúç, A. A., & Dag, T. (2025).** Predicting user purchases from clickstream data: A comparative analysis of clickstream data representations and machine learning models. *IEEE Access*, 13, 43796–43817. DOI: [10.1109/ACCESS.2025.3548267](https://doi.org/10.1109/ACCESS.2025.3548267)

**[2] Requena, B., Cassani, G., Tagliabue, J., Greco, C., & Lacasa, L. (2020).** Shopper intent prediction from clickstream e-commerce data with minimal browsing information. *Scientific Reports*, 10, 16983. DOI: [10.1038/s41598-020-73622-y](https://doi.org/10.1038/s41598-020-73622-y)

**[3] Ling, C., Zhang, T., & Chen, Y. (2019).** Customer purchase intent prediction under online multi-channel promotion: A feature-combined deep learning framework. *IEEE Access*, 7, 112963–112976. DOI: [10.1109/ACCESS.2019.2935121](https://doi.org/10.1109/ACCESS.2019.2935121)

**[4] Gan, M., & Xiao, K. (2019).** R-RNN: Extracting user recent behavior sequence for click-through rate prediction. *IEEE Access*, 7, 111767–111777. DOI: [10.1109/ACCESS.2019.2927717](https://doi.org/10.1109/ACCESS.2019.2927717)

### B. Product demand forecasting (4)

**[5] Zhang, X., Li, P., Han, X., Yang, Y., & Cui, Y. (2024).** Enhancing time series product demand forecasting with hybrid attention-based deep learning models. *IEEE Access*, 12, 190079–190091. DOI: [10.1109/ACCESS.2024.3516697](https://doi.org/10.1109/ACCESS.2024.3516697)

**[6] Panda, S. K., & Mohanty, S. N. (2023).** Time series forecasting and modeling of food demand supply chain based on regressors analysis. *IEEE Access*, 11, 42679–42700. DOI: [10.1109/ACCESS.2023.3266275](https://doi.org/10.1109/ACCESS.2023.3266275)

**[7] Salinas, D., Flunkert, V., & Gasthaus, J. (2020).** DeepAR: Probabilistic forecasting with autoregressive recurrent networks. *International Journal of Forecasting*, 36(3), 1181–1191. DOI: [10.1016/j.ijforecast.2019.07.001](https://doi.org/10.1016/j.ijforecast.2019.07.001)

**[8] Makridakis, S., Spiliotis, E., & Assimakopoulos, V. (2018).** Statistical and machine learning forecasting methods: Concerns and ways forward. *PLOS ONE*, 13(3), e0194889. DOI: [10.1371/journal.pone.0194889](https://doi.org/10.1371/journal.pone.0194889)

### C. ML model comparison (3)

**[9] Sen, N., Temur, L. O., & Atilla, D. C. (2024).** Yellow fever vaccine demand forecasting with ARIMA, SARIMA, linear regression, and XGBoost. *IEEE Access*, 12, 197557–197576. DOI: [10.1109/ACCESS.2024.3517652](https://doi.org/10.1109/ACCESS.2024.3517652)

**[10] Obaidat, M., Almomani, H. A., Mallouhy, R., AlMotari, A., & Al Meanazel, O. T. (2025).** A hybrid machine learning framework for daily demand forecasting: Integrating SARIMAX and XGBoost for seasonal production optimization. *IEEE Access*, 13, 162668–162680. DOI: [10.1109/ACCESS.2025.3610316](https://doi.org/10.1109/ACCESS.2025.3610316)

**[11] Mitra, A., Jain, A., Kishore, A., & Kumar, P. (2022).** A comparative study of demand forecasting models for a multi-channel retail company: A novel hybrid machine learning approach. *Operations Research Forum*, 3, 68. DOI: [10.1007/s43069-022-00166-4](https://doi.org/10.1007/s43069-022-00166-4)

### D. Pipeline / preprocessing / evaluation (2)

**[12] Bilal, M., Ali, G., Iqbal, M. W., Anwar, M., Malik, M. S. A., & Abdul Kadir, R. (2022).** Auto-Prep: Efficient and automated data preprocessing pipeline. *IEEE Access*, 10, 107764–107784. DOI: [10.1109/ACCESS.2022.3198662](https://doi.org/10.1109/ACCESS.2022.3198662)

**[13] Hyndman, R. J., & Athanasopoulos, G.** *Forecasting: Principles and Practice* (3rd ed.). OTexts. [https://otexts.com/fpp3/](https://otexts.com/fpp3/) — time-based validation, MAE/RMSE.

### E. Background (2)

**[14] Li, W., & Law, K. L. E. (2024).** Deep learning models for time series forecasting: A review. *IEEE Access*, 12, 92306–92327. DOI: [10.1109/ACCESS.2024.3422528](https://doi.org/10.1109/ACCESS.2024.3422528)

**[15] Bandara, K., Bergmeir, C., & Hewamalage, H. (2021).** LSTM-MSNet: Leveraging forecasts on sets of related time series with multiple seasonal patterns. *IEEE Transactions on Neural Networks and Learning Systems*, 32(4), 1586–1599. DOI: [10.1109/TNNLS.2020.2985720](https://doi.org/10.1109/TNNLS.2020.2985720) — Free preprint: [arXiv:1909.04293](https://arxiv.org/abs/1909.04293)

**Supplementary (not in table):** Punia et al. (2020) Springer *Int. J. Prod. Res.* — LSTM + RF retail demand. Silahtaroğlu & Dönertaşli (2015) IEEE Big Data — clickstream mining. Oreshkin et al. (2020) N-BEATS, ICLR — [arXiv:1905.10437](https://arxiv.org/abs/1905.10437).

**Related work only (future work):** Chong et al. (2022) IEEE Access — deep RL for apparel supply chain / inventory. DOI: [10.1109/ACCESS.2022.3205720](https://doi.org/10.1109/ACCESS.2022.3205720)

**Local WIP (gitignored):** Automated check → [`../workspace/verification/literature_verification.md`](../workspace/verification/literature_verification.md) · Manual workbook → [`../workspace/verification/literature_manual_verification.md`](../workspace/verification/literature_manual_verification.md) · Submission plan → [`../workspace/plans/submission_plan_7days.md`](../workspace/plans/submission_plan_7days.md)

---

## 2. Data sources (Chapter 3 — not literature)

Do **not** cite these as peer-reviewed papers in Chapter 2.

| Source | URL | Use |
|--------|-----|-----|
| Kechinov — eCommerce behavior (Kaggle / Open CDP) | [kaggle.com/.../ecommerce-behavior-data-from-multi-category-store](https://www.kaggle.com/datasets/mkechinov/ecommerce-behavior-data-from-multi-category-store) | Bronze input (`2019-Oct.csv`) |
| REES46 datasets | [rees46.com/en/datasets](https://rees46.com/en/datasets) | Data publisher / attribution |
| NVIDIA Merlin preprocessing notes | [Transformers4Rec REES46 example](https://github.com/NVIDIA-Merlin/Transformers4Rec/tree/main/examples/tutorial/preprocessing) | Event schema reference |

---

## 3. Comparative analysis

**Row numbers match the reference list [1]–[15] above.** Row 16 is this dissertation (not a published reference).

| # | Authors | Year | Venue | Method | Dataset | Metrics | Gap vs this dissertation |
|---|---------|------|-------|--------|---------|---------|--------------------------|
| 1 | Tokúç & Dag | 2025 | IEEE Access | LightGBM + hybrid representations | E-commerce clickstream sessions | Precision, Recall, AUC | Session purchase intent, not product-day demand counts |
| 2 | Requena et al. | 2020 | Scientific Reports | k-gram features + LSTM | Proprietary e-commerce clickstream | AUC, accuracy | Session-level intent; no product-day aggregation |
| 3 | Ling et al. | 2019 | IEEE Access | FC-LSTM | Concert ticket multi-channel purchase data | Precision, Recall, AUC | Purchase intent classification under promotion, not demand regression |
| 4 | Gan & Xiao | 2019 | IEEE Access | R-RNN (attention + LSTM) | CTR benchmark dataset | AUC | Sequential click behaviour for CTR, not purchase demand forecasting |
| 5 | Zhang et al. | 2024 | IEEE Access | HA-LSTM (multi-head attention + LSTM) | Predict Future Sales (retail competition) | RMSE (primary), MAE, MAPE | vs N-BEATS: −2.3% RMSE/MAE, −2.6% MAPE; also benchmarks XGBoost/LightGBM on **sales history** — no clickstream funnel |
| 6 | Panda & Mohanty | 2023 | IEEE Access | LSTM, BiLSTM vs RF, GBR, LightGBM, XGBoost, CatBoost | Genpact food demand (meal delivery orders) | RMSLE, RMSE, MAPE, MAE | LSTM best per meal (e.g. RMSLE 0.28, MAPE 6.56%); **sales/order TS** — no clickstream features |
| 7 | Salinas et al. | 2020 | IJF | DeepAR (LSTM) | Multiple real-world datasets | ρ-quantile loss | Probabilistic retail forecast; no clickstream |
| 8 | Makridakis et al. | 2018 | PLOS ONE | 8 statistical vs 8 ML methods (incl. LSTM, MLP) | M3 subset: **1,045 monthly** series (of 3,003 total) | sMAPE, MASE | Train n−18 / test 18 holdout; **post-sample** ML often ≤ statistical; motivates baselines + temporal split — not clickstream |
| 9 | Sen et al. | 2024 | IEEE Access | ARIMA, SARIMA, LR, XGBoost | Turkey yellow fever vaccine (2003–2023) | MAE, RMSE (+ VaR for inventory risk) | Supports comparison methodology; not e-commerce clickstream |
| 10 | Obaidat et al. | 2025 | IEEE Access | SARIMAX vs XGBoost | Jordan dairy (6 products, 1 year) | MAPE (avg 5.55% vs 7.04%), economic impact | **SARIMAX beat XGBoost** on seasonal dairy; weather/holiday exogenous vars — not clickstream; ML wins not guaranteed |
| 11 | Mitra et al. | 2022 | Springer OR Forum | RF, XGBoost, GB, AdaBoost, ANN + hybrid RF-XGBoost-LR | Weekly US retail sales (w/ temp + store size) | Multiple accuracy metrics | Sales history only; no behavioural events |
| 12 | Bilal et al. | 2022 | IEEE Access | Auto-Prep pipeline | Generic ML datasets | Accuracy | Preprocessing automation; supports pipeline design |
| 13 | Hyndman & Athanasopoulos | — | OTexts (book) | Forecasting methods & evaluation | Textbook / multiple examples | MAE, RMSE, MAPE (conceptual) | Time-based holdout and accuracy measures — not an empirical clickstream study |
| 14 | Li & Law | 2024 | IEEE Access | Survey (DL forecasting) | Multiple | Review | Background only |
| 15 | Bandara et al. | 2021 | IEEE TNNLS | LSTM-MSNet (globally trained LSTM + seasonal decomp) | M4 + real-world multi-seasonal series | sMAPE | General TS benchmark; no clickstream |
| **16** | **This dissertation** | **2026** | **BITS WILP** | **Lag/MA baselines, RF, XGBoost, LightGBM** | **REES46/Kaggle Oct 2019** | **MAE, RMSE, MAPE, R²** | **End-to-end clickstream → product-day demand pipeline** |

**Gap statement:** Prior work addresses session intent, sales-only time series, or supply-chain forecasting separately. None combines public multi-category clickstream events, product-day aggregation, and comparative tree-based ML under temporal validation on open CDP data — which this dissertation addresses (row 16).

---

## 4. Review prose (Chapter 2 draft)

### 2.1 Clickstream and behavioural features

E-commerce clickstream research typically predicts whether a session or user will purchase, using views, carts, and dwell time as signals (Tokúç & Dag, 2025; Requena et al., 2020; Ling et al., 2019; Gan & Xiao, 2019). Feature engineering from event sequences — counts, conversion-style ratios, and rolling activity — is well established at session or user grain. **Gap:** these studies do not forecast **next-day purchase volume per product**, which is the grain needed for SKU-level demand planning. **Therefore**, this work aggregates silver-layer events to `(product_id, date)` and engineers daily views, carts, purchases, and 7-day rollups as regression features.

### 2.2 Demand forecasting

Product and retail demand forecasting literature compares statistical and machine-learning models on time-series or sales history, reporting MAE, RMSE, and MAPE (Zhang et al., 2024; Sen et al., 2024; Obaidat et al., 2025; Panda & Mohanty, 2023; Mitra et al., 2022). Probabilistic and deep sequence models (Salinas et al., 2020) set benchmarks on retail datasets. Makridakis et al. (2018) found that statistical methods outperformed ML methods (MLP, LSTM, CART, SVR) on M3 series, attributing this to overfitting and inadequate preprocessing — motivating the careful temporal validation and feature engineering applied in this work. **Gap:** demand targets in this body of work are rarely built directly from clickstream funnels (view → cart → purchase). **Therefore**, the target variable here is `purchases_next_day`, derived from purchase events in the gold layer.

### 2.3 Models and evaluation

Tree ensembles (Random Forest, XGBoost, LightGBM) are standard strong baselines for tabular demand features (Sen et al., 2024; Mitra et al., 2022). However, Obaidat et al. (2025) found that SARIMAX outperformed XGBoost on dairy demand data with strong seasonality, and Makridakis et al. (2018) showed statistical methods consistently outperforming ML (MLP, LSTM, CART) on M3 series — both results highlight that ML gains depend on domain, feature quality, and temporal structure, not just model choice. Forecast accuracy should be evaluated with held-out **future** periods, not random row splits (Hyndman & Athanasopoulos, FPP3). Simple baselines — lag-1, moving average, historical mean — therefore serve as essential sanity checks in this dissertation's evaluation. **Gap:** no published study documents a reproducible batch pipeline from REES46-style clickstream to product-day demand with comparative tree models on a temporal October 2019 holdout. **Therefore**, this dissertation trains lag/MA/hist_mean baselines plus RF, XGBoost, and LightGBM on the same split, reporting MAE, RMSE, MAPE, and R².

---

Copy Section 1 references into the report **References** chapter using your supervisor's format (IEEE numbered `[1]` is typical for WILP CS). No separate BibTeX file is required unless you write the report in LaTeX.
