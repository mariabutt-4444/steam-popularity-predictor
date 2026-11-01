# Steam Game Popularity Predictor: Exploratory Data Analysis (EDA) Report

**Course**: Programming for AI (Project 1: ETL + EDA)  
**Branch**: `eda-tables`  
**Dataset**: SQLite database (`data/steam.db`), 1,500 games stratified sample  
**Analysis Date**: October 2026  

---

## 1. Executive Summary & Context

This report presents the exploratory data analysis (EDA) for the **Steam Game Popularity Predictor** project. The core objective of this study is to examine how pre-launch attributes—such as pricing, multi-label genres, platform availability, and release timing—relate to commercial popularity (estimated owner tiers) on the Steam platform.

The underlying dataset was processed, transformed, and validated by the ETL pipeline into a relational SQLite database (`data/steam.db`). All analysis herein is strictly read-only on the stored data.

### Key Data Architecture
- **Primary Observation Unit**: 1,500 validated video games in the `games` table.
- **Relational Genre Taxonomy**: 23 distinct genres linked via 4,243 many-to-many associations in `game_genres`.
- **Target Variable**: `popularity_tier` (`Low`, `Medium`, `High`), derived from estimated maximum owners (`owners_max`).
- **Post-Launch Data Isolation**: 5 fields represent post-launch outcomes and are quarantined to avoid data leakage during subsequent machine learning stages.

---

## 2. 9 Key Findings (Plain Language for Viva Defense)

### Finding 1: Severe Class Imbalance in Popularity Tiers
The target variable is heavily skewed toward low-volume releases:
- **Low** ($\le$ 20,000 owners): **1,030 games (68.67%)**
- **Medium** (20,000–200,000 owners): **340 games (22.67%)**
- **High** (> 200,000 owners): **130 games (8.67%)**

The Low-to-High imbalance ratio is **7.9 : 1**. A naive baseline model that uniformly predicts "Low" would achieve nearly 69% raw accuracy while having zero predictive utility for commercial hits.

---

### Finding 2: Free-to-Play Titles Possess a Massive Scale Advantage
Free-to-play (F2P) titles constitute 9.2% of the dataset (138 games) and average **154,529 estimated owners**, compared to **101,766 owners** for paid titles—a **1.52x volume advantage**. Furthermore, **15.22% of free games reach the High popularity tier**, compared to only **8.00% of paid titles**. By eliminating the monetary barrier to entry, the F2P model dramatically raises the probability of reaching broad audiences.

---

### Finding 3: Price Band Non-Linearity and the "$20–$40" Quality Sweet Spot
Segmenting prices into 6 standard commercial tiers reveals significant non-linear behavior:
1. **Free** ($0.00, $n=138$): High volume ($\bar{y} = 154,529$ owners), moderate review score ($\bar{s} = 0.707$).
2. **Budget / Sub-$5** ($0.01–$4.99, $n=788$): Largest share of titles (52.5%), lowest average owners ($\bar{y} = 65,992$), and lowest average review score ($\bar{s} = 0.704$).
3. **Mid-tier** ($5.00–$9.99, $n=312$): Moderate volume ($\bar{y} = 96,894$).
4. **Upper-mid** ($10.00–$19.99, $n=217$): Strong volume ($\bar{y} = 186,076$) and solid review scores ($\bar{s} = 0.771$).
5. **Premium Indie / AA** ($20.00–$39.99, $n=40$): Highest average review score across all bands (**$\bar{s} = 0.782$**), with 20.0% reaching the High tier.
6. **Full-price / AAA** ($40.00+, $n=5$): Highest owner averages ($\bar{y} = 1,480,000$), but constrained by a very small sample count ($n=5$).

*Viva Takeaway*: Higher price does not reduce sales volume on Steam; instead, premium prices reflect higher production value and brand strength, yielding higher review scores and healthy owner figures.

---

### Finding 4: Extreme Right-Tail Skewness Across Engagement Metrics
All count- and volume-based numeric attributes display heavy right-tail skewness ($|\text{skew}| \gg 1.0$):
- **Price**: Median is \$3.99, mean is \$6.15, standard deviation is \$8.52, maximum is \$209.99.
- **Estimated Owners (`owners_mid`)**: Median is 35,000, mean is 106,620, maximum is 7,500,000.
- **Achievements**: Median is 11, mean is 58.7, maximum is 5,000.
- **Outlier Density**: The IQR method flags **1,723 total outliers** across the 9 numeric fields. Playtime has 346 outliers (23.07% of rows), and positive ratings has 232 outliers (15.47%).

*Viva Takeaway*: Standard linear scaling (e.g., standard z-score) will be distorted by these extreme values; robust scaling or log-transformations are mathematically necessary.

---

### Finding 5: Genre Volume vs. Popularity Divergence
Steam games are multi-label (average of 2.83 genres per title). Evaluating performance per genre reveals stark differences:
- **Mass-Market Drivers**: `Massively Multiplayer` ($\bar{y} = 227,115$, $n=26$), `Free to Play` ($\bar{y} = 217,358$, $n=106$), and `RPG` ($\bar{y} = 163,892$, $n=241$) lead the highest average owners among major genres.
- **Catalog Dominators**: `Indie` ($n=1,128$ games, 75.2% of catalog) and `Action` ($n=605$ games) dominate total volume, but have lower mean owners ($\bar{y} = 88,432$ for Indie) due to heavy competition in the "indie long-tail".
- **Low-Sample Niches**: 7 genres contain fewer than 10 games (e.g., `Utilities`, `Design & Illustration`, `Early Access`). While `Utilities` statistically tops the owner table ($\bar{y} = 290,000$), this is an artifact of a low sample size ($n=7$) and must be interpreted with caution.

---

### Finding 6: Cross-Platform Support Correlates with Popularity
All 1,500 games in the dataset support Windows (100.0%). Examining multi-OS support:
- **Windows Only** ($n=1,057$, 70.5%): Average owners = **76,805**; High tier share = **6.24%**.
- **Windows + Mac** ($n=157$, 10.5%): Average owners = **112,694**; High tier share = **10.19%**.
- **Windows + Mac + Linux** ($n=286$, 19.1%): Average owners = **213,297**; High tier share = **16.78%**.

*Viva Takeaway*: Offering Linux and Mac support is a strong proxy for development maturity, engine portability, and developer resource allocation, correlating with a **2.7x higher likelihood** of achieving High popularity.

---

### Finding 7: Yearly Catalog Growth and Market Saturation
Analyzing release volume across the 14-year period (2006–2019):
- Prior to 2014, annual catalog additions remained below 30 games per year in this sample.
- Following the introduction of Steam Greenlight and Steam Direct (2014–2017), release volume surged, peaking at **425 games in 2018** (28.3% of the entire sample).
- Concurrently, the proportion of free games increased from 0% in 2006–2009 to **11.5% in 2018–2019**, reflecting the broader industry shift toward games-as-a-service.

---

### Finding 8: Post-Launch Outcome Collinearity (Data Leakage Control)
The strongest correlation in the entire numeric feature space is between **`positive_ratings` and `negative_ratings`** ($r = 0.901$, Spearman $\rho = 0.887$). Furthermore, `positive_ratings` correlates strongly with `owners_mid` ($r = 0.841$).
- Both review counts and playtime hours represent **post-launch outcomes** that occur *after* players have purchased and experienced the game.
- If included as predictive features in a pre-launch classifier, they would introduce **catastrophic data leakage**, yielding artificially inflated test metrics that fail completely in production for unreleased titles.

---

### Finding 9: Pre-Launch Features Have Weak Linear Correlation with Owners
When isolating valid **pre-launch features**:
- `price` vs `owners_mid`: Pearson $r = 0.089$, Spearman $\rho = 0.024$.
- `achievements` vs `owners_mid`: Pearson $r = 0.046$, Spearman $\rho = 0.071$.
- `required_age` vs `owners_mid`: Pearson $r = 0.049$, Spearman $\rho = 0.065$.

*Viva Takeaway*: Commercial success on Steam is not governed by simple linear relationships with isolated variables. Popularity is driven by complex non-linear interactions among genre combinations, price tier positioning, multi-platform accessibility, and release timing. Non-linear models (Random Forest, Gradient Boosting, Multi-Layer Perceptron) are therefore fundamentally better suited than simple linear baselines.

---

## 3. Study Limitations & Methodological Constraints

When presenting this project in an academic or viva defense context, three primary limitations must be emphasized:

1. **Stratified Sample Size ($N = 1,500$)**:
   The full Steam store catalog exceeds 50,000 titles. Our dataset is a 1,500-game stratified sample designed for university computational budgets. While statistically valid for macro-level trends, smaller sub-segments (such as games priced \$40+ with $n=5$, or niche genres with $n < 10$) carry higher standard errors.

2. **SteamSpy Estimation Bounds**:
   SteamSpy owners data is not an exact sensor readout; it is a survey-sampled estimate reported in discretized range buckets (e.g., `20000-50000`). While `owners_mid` provides a continuous working proxy, the true target is the discrete bucket boundary (`owners_max`), which defines our 3-tier classification problem.

3. **Imbalanced Class Support**:
   With only 130 examples in the `High` class, unstratified train/test splits could easily leave the test set with fewer than 25 positive hit examples, causing volatile evaluation metrics.

---

## 4. Machine Learning Implications (Bridge to Project 2 & Project 3)

The findings from this EDA establish the required architecture for the subsequent classical ML (Project 2) and deep learning (Project 3) pipelines:

| EDA Finding | Machine Learning Implication | Pipeline Implementation |
| :--- | :--- | :--- |
| **Data Leakage** (`positive_ratings`, `review_score`, `playtime`) | Post-launch outcome contamination must be prevented. | Explicitly drop all 5 post-launch columns from the feature matrix `X` before pipeline ingestion. |
| **Class Imbalance** (68.7% / 22.7% / 8.7%) | Accuracy is an uninformative metric; minority classes risk being ignored. | 1. Use `StratifiedKFold` (5 folds) and stratified 80/20 train-test splits.<br>2. Set `class_weight='balanced'` in Random Forest and Logistic Regression.<br>3. Optimize **Macro-F1 score** as primary tuning metric. |
| **Heavy Skewness** (Price, Achievements) | Outliers compress gradient updates and distort distance metrics. | Apply `StandardScaler` after `SimpleImputer`, or evaluate quantile/log transforms within `ColumnTransformer`. |
| **Multi-Label Genres** (23 categories, multi-tag per game) | Semicolon strings cannot be ingested directly into scikit-learn estimators. | Multi-hot encode genre features (via `MultiLabelBinarizer` or binary indicator columns from `game_genres`). |
| **Categorical Non-Linearity** (Price bands, platform combos) | Simple linear boundaries will fail to capture threshold effects. | Tree-based ensembles (Random Forest, LightGBM/XGBoost) and deep MLP networks with non-linear activations (ReLU) should outperform linear classifiers. |

---

## 5. Summary Table Reference

All underlying tables are exported and versioned in `eda/output/`:
- `01_summary_statistics.csv`
- `02_missing_and_outliers.csv`
- `03_genre_performance.csv`
- `04_price_band_analysis.csv`
- `05_free_vs_paid.csv`
- `06_platform_support.csv`
- `07_yearly_trends.csv`
- `08_correlation_table.csv`
- `09_tier_distribution.csv`
