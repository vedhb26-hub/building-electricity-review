"""Public historical building-electricity demo. No live monitoring or uploads."""
from datetime import date, timedelta
from pathlib import Path
import json
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent
st.set_page_config(page_title='Building Electricity Review', page_icon='📊', layout='wide')

@st.cache_data
def load_snapshot():
    summary = json.loads((ROOT/'4-summary.json').read_text())
    df = pd.read_csv(ROOT/'5-hourly_predictions.csv', parse_dates=['site_local_hour'])
    assert len(df) == summary['scored_hours'] == 8760
    assert int(df.review_candidate.sum()) == summary['review_hours'] == 103
    assert abs((df.actual_kwh-df.expected_kwh).abs().mean()-summary['test_MAE_kwh']) < 1e-8
    assert df.site_local_hour.is_unique and df.site_local_hour.is_monotonic_increasing
    assert (df.review_candidate == (df.above_expected_kwh > summary['positive_residual_threshold_kwh'])).all()
    return summary, df

S, all_hours = load_snapshot()
st.caption('HISTORICAL DATA DEMO · PUBLIC US DATA')
st.title('Building Electricity Review')
st.write('Compare actual electricity use with a learned expectation and review the largest positive differences.')
st.caption(f"{S['building']} · 2017 · Site-local time: {S['timezone']}")
st.info('A review candidate is not a confirmed fault, wasted energy or a savings estimate. This prototype uses historical US data, not live monitoring.')
a,b,c=st.columns(3)
a.metric('Review hours, full test year', f"{S['review_hours']:,}")
b.metric('Scored hours, full test year', f"{S['scored_hours']:,}")
c.metric('Mean absolute error, full year', f"{S['test_MAE_kwh']:.2f} kWh")

st.header('Actual vs expected')
first,last=date(2017,1,1),date(2017,12,31)
if 'selected_period' not in st.session_state: st.session_state.selected_period=(first,last)
x,y=st.columns(2)
if x.button('Full year', width='stretch'):
    st.session_state.selected_period=(first,last)
    st.session_state.illustrative=False
if y.button('Largest deviation week', width='stretch'):
    biggest=all_hours.loc[all_hours.above_expected_kwh.idxmax(),'site_local_hour'].date()
    start=max(first,min(biggest-timedelta(days=biggest.weekday()),date(2017,12,25)))
    st.session_state.selected_period=(start,start+timedelta(days=6))
    st.session_state.illustrative=True
period=st.date_input('Date range (site-local)', min_value=first,max_value=last,key='selected_period')
if len(period)!=2:
    st.warning('Select a start date and an end date to apply the date range.')
    st.stop()
start,end=period
hours=all_hours[all_hours.site_local_hour.dt.date.between(start,end)].copy()
review=hours[hours.review_candidate].sort_values('above_expected_kwh',ascending=False,kind='stable')
st.caption(f'{start} to {end} · {len(hours):,} scored hours · {len(review):,} review hours')
chart=hours.set_index('site_local_hour')[['actual_kwh','expected_kwh']].rename(columns={'actual_kwh':'Actual','expected_kwh':'Expected'})
chart['Review boundary']=chart.Expected+S['positive_residual_threshold_kwh']
daily=len(hours)>24*14
if daily: chart=chart.resample('D').mean()
st.line_chart(chart, x_label='Site-local date and time', y_label='Electricity (kWh)',color=['#251f21','#0f766e','#a8a29e'])
st.caption('Daily means of hourly readings; review counts use original hourly data.' if daily else 'Hourly readings. The review boundary is expected electricity plus the fixed threshold.')
st.caption(f"Hourly review boundary = expected + {S['positive_residual_threshold_kwh']:.2f} kWh. Threshold calibrated on validation data only.")
if st.session_state.get('illustrative'):
    st.caption('The shortcut selects the week containing the largest positive deviation, for illustration, not as a typical week. Date controls show the currently applied period.')

st.header('Hours to review')
st.write('Ranked by actual minus expected. Adjacent hours may belong to one event.')
if review.empty: st.info('No review hours in this date range.')
else:
    display=review[['site_local_hour','actual_kwh','expected_kwh','above_expected_kwh']].rename(columns={'site_local_hour':'Site-local hour','actual_kwh':'Actual (kWh)','expected_kwh':'Expected (kWh)','above_expected_kwh':'Above expected (kWh)'})
    st.dataframe(display,hide_index=True,width='stretch')
x,y=st.columns(2)
x.download_button('Download filtered review CSV',review.to_csv(index=False),file_name=f'review_hours_{start}_to_{end}.csv',mime='text/csv',width='stretch')
y.download_button('Download filtered hourly CSV',hours.to_csv(index=False),file_name=f'hourly_readings_{start}_to_{end}.csv',mime='text/csv',width='stretch')
st.warning('Check schedules, occupancy, equipment operation, weather and meter quality. A low reading at the same hour last week, including a holiday or closure, can make the expectation too low.')

with st.expander('Method and limitations',expanded=True):
    st.markdown('''
- The per-building model uses hour of week, temperature and measured electricity from the same hour 168 hours earlier. This is not a week-ahead forecast.
- Training: Jan-Jun 2016. Validation: Jul-Dec 2016. Test: Jan-Dec 2017. The model was not retrained after validation.
- The review threshold is the 99th percentile of all validation actual-minus-expected residuals, floored at zero. Date filters do not change it.
- Only readings with an observed target and last-week reading are scored. Missing weather is filled with the training median.
- No labelled faults were provided. Review precision and the false-alarm rate are unknown.
- Thelma was selected after exploring three buildings. This is exploratory evidence, not a blind generalisation test.
- The dashboard displays a fixed historical snapshot. No uploads or building connections are collected. The hosting service receives ordinary web requests.
''')
    st.caption(S['snapshot_note'])
st.divider()
st.markdown('Data: [Building Data Genome Project 2](https://github.com/buds-lab/building-data-genome-project-2) · Miller et al. (2020), [Scientific Data](https://doi.org/10.1038/s41597-020-00712-x).')
st.caption('Data and derived snapshot: Creative Commons Attribution-ShareAlike 4.0. Changes: one building selected, historical model predictions and review flags added. This is not an endorsement by the dataset authors.')
