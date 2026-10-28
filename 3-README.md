# Building Electricity Review

A Streamlit portfolio demo using a fixed historical snapshot from the Building Data Genome Project 2. It compares actual electricity use against a per-building model's expectation and lists hours for review.

This is historical US data, not UAE validation or live monitoring. Flags are review candidates, not confirmed faults, waste, or savings.

## Run

Install `requirements.txt`, then run:

```sh
streamlit run streamlit_app.py
```

## Deploy

Create a separate GitHub repository with this folder's contents. In Streamlit Community Cloud, select the repository and `streamlit_app.py` as the entrypoint. No credentials, secrets, or paid services are needed by the app itself. Keep any existing MoneyInsights app unchanged.

## Snapshot and model

- Fox_office_Thelma; site-local US/Mountain timestamps.
- Training Jan-Jun 2016; validation Jul-Dec 2016; test Jan-Dec 2017.
- Features: hour of week, temperature, observed same-hour-last-week electricity.
- SVD ridge model; holiday dates mapped to Sunday.
- Review threshold: positive-residual 99th percentile on validation, floored at zero; strict crossing.
- 8,760 scored test hours, 103 review candidates, test MAE 10.020177914 kWh.
- Snapshot reproduced on 2026-10-28 from the original checked model. Predictions are precomputed; this deployment does not retrain.

Thelma was selected after exploring three buildings. No labelled faults were available. Low prior-week readings, especially holidays or closures, can depress expectations. Precision and false-alarm rates are unknown.

## Attribution

Miller, C., Kathirgamanathan, A., Picchetti, B. et al. The Building Data Genome Project 2, energy meter data from the ASHRAE Great Energy Predictor III competition. Scientific Data 7, 368 (2020). https://doi.org/10.1038/s41597-020-00712-x

Source: https://github.com/buds-lab/building-data-genome-project-2

The data and derived snapshot are provided under Creative Commons Attribution-ShareAlike 4.0. See `BDG2-LICENSE.txt`. Changes: one building selected, model predictions and review flags added. Dataset authors do not endorse this demo.
