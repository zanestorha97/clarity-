import io
import streamlit as st
import numpy as np
import pandas as pd
import json

from presidio_setup import create_presidio_engines, DEFAULT_OPERATORS
from processors import anonymize_dataframe
from zipfile import ZipFile

# Cache engines so they don’t re-init on every interaction
@st.cache_resource
def get_engines():
    return create_presidio_engines()

@st.cache_resource
def combine_data(uploaded_file, zip_uploaded_file):
    df = pd.read_csv(uploaded_file)
    with ZipFile(zip_uploaded_file, 'r') as zip_object:
        with zip_object.open('users.json') as slack_user:
            slack_user_data = json.loads(slack_user.read())

            slack_user_data = pd.DataFrame([{
                'slack_id': _['id'],
                'team_id': _['team_id'],
                'first_name': _['profile'].get('first_name'),
                'last_name': _['profile'].get('last_name'),
                'email_address': _['profile'].get('email'),
                'is_bot': _['profile'].get('bot_id')
            } for _ in slack_user_data
            ])

    slack_and_hr_data = slack_user_data.merge(df, how = 'outer', left_on = 'email_address', right_on = 'Email Address')
    
    employee_data = slack_and_hr_data[slack_and_hr_data.is_bot.isna()]
    list_of_bots_ids = slack_and_hr_data[~slack_and_hr_data.is_bot.isna()].slack_id.values.tolist()

    employee_data['Clarity_ID'] = pd.Series(['E' + str(_) for _ in employee_data.index])

    return employee_data, list_of_bots_ids

@st.cache_resource
def extract_zip_files(zip_uploaded_file, employee_data, list_of_bots_ids):
    
    employee_hashes = list(employee_data.loc[:, ['slack_id', 'Clarity_ID', 'Job Title', 'Department', 'Team']].T.to_dict().values())
    employee_hashes = {
        curr_data['slack_id']: {
            'Clarity_ID': curr_data['Clarity_ID'],
            'Job Title': curr_data['Job Title'],
            'Department': curr_data['Department'],
            'Team': curr_data['Team']
        }
    for curr_data in employee_hashes}

    with ZipFile(zip_uploaded_file, 'r') as zip_object:
        list_of_folders = [_ for _ in zip_object.namelist() if _.endswith('/')]

    folder_search = lambda x: [ 
        _
        for _ in zip_object.namelist()
        if _.startswith(x) and _.endswith('.json')
    ]

    slack_folder_data = {}
    for folder_name in list_of_folders:
        with ZipFile(zip_uploaded_file, 'r') as zip_object:
            
            folder_data = []
            for file_name in folder_search(folder_name):
                folder_data += json.loads(zip_object.open(file_name).read())
        
        slack_folder_data[folder_name.replace('/', '')] = folder_data

    with ZipFile(zip_uploaded_file, 'r') as zip_object:

        slack_folder_data['users'] = json.loads(zip_object.open('users.json').read())
        slack_folder_data['channels'] = json.loads(zip_object.open('channels.json').read())

    ### Prepare Data
    slack_folder_data['users'] = [
        employee_hashes[curr_data['id']] if curr_data['id'] not in list_of_bots_ids else curr_data
        for curr_data in slack_folder_data['users']
    ]

    for curr_data in slack_folder_data['channels']:

        curr_data['creator'] = employee_hashes[curr_data['creator']]['Clarity_ID']
        curr_data['members'] = [(employee_hashes[_]['Clarity_ID'] if employee_hashes.get(_) is not None else _) for _ in curr_data['members']]

    for name in list_of_folders:
        slack_folder_data[name[:-1]] = [
            {
                'clarity_id': employee_hashes[_['user']]['Clarity_ID'] if _['user'] not in list_of_bots_ids + ['USLACKBOT'] else _['user'],
                'timestamp': _['ts'],
                'file_count': len(_['files']) if _.get('files') else 0,
                'reaction_count': sum([__['count'] for __ in _['reactions']]) if _.get('reactions') else 0,
                'reaction_interactions': np.unique([employee_hashes[___]['Clarity_ID'] for __ in _['reactions'] for ___ in __['users']]).tolist() if _.get('reactions') else [],
            } 
            for _ in slack_folder_data[name[:-1]]
        ]

    return slack_folder_data

def main():
    st.set_page_config(page_title="PII Sanitizer", page_icon="🧹", layout="wide")
    st.title("PII Sanitizer for CSV (Microsoft Presidio powered)")

    st.markdown(
        """
        Upload a CSV (e.g. Slack export), select columns to scrub, 
        and download an anonymized version safe for sharing.
        """
    )

    uploaded_file = st.file_uploader("Upload CSV", type=["csv"])

    if not uploaded_file:
        st.info("Drop in a CSV to get started.")
        return

    zip_uploaded_file = st.file_uploader("Upload Slack Zip", type=["zip"])

    if not zip_uploaded_file:
        st.info("Drop in the Slack Zip to get started.")
        return

    # Read CSV
    try:
        combined_df, list_of_bots_ids = combine_data(uploaded_file, zip_uploaded_file)
    except Exception as e:
        st.error(f"Could not read CSV: {e}")
        return

    if combined_df.empty:
        st.warning("The uploaded CSV is empty. Try another one?")
        return

    st.subheader("Preview of uploaded data")
    st.dataframe(combined_df.head())

    # Prepare downloadable CSV
    buffer = io.StringIO()
    combined_df.to_csv(buffer, index=False)
    buffer.seek(0)
    csv_str = buffer.getvalue()  # ✅ plain string


    st.download_button(
        label="⬇️ Download User Data",
        data=csv_str,
        file_name="combined.csv",
        mime="text/csv",
    )


    # # Default: all object (string-like) columns
    # default_cols = [c for c in combined_df.columns if combined_df[c].dtype == "object"]

    # st.subheader("Select columns to anonymize")
    # cols_to_anonymize = st.multiselect(
    #     "These columns will be scanned for PII and anonymized:",
    #     options=list(combined_df.columns),
    #     default=default_cols,
    # )

    # if not cols_to_anonymize:
    #     st.warning("Select at least one column to anonymize.")
    #     return

    # st.markdown(
    #     """
    #     Upload a CSV (e.g. Slack export), select columns to scrub, 
    #     and download an anonymized version safe for sharing.
    #     """
    # )

    if combined_df.empty:
        st.warning("The uploaded CSV is empty. Try another one?")
        return

    # analyzer, anonymizer = get_engines()

    if st.button("Anonymize Slack"):
        with st.spinner("Scrubbing your secrets..."):

            slack_folder_data = extract_zip_files(zip_uploaded_file, combined_df, list_of_bots_ids)
            # sanitized_df = anonymize_dataframe(
            #     df=combined_df,
            #     analyzer=analyzer,
            #     anonymizer=anonymizer,
            #     operators=DEFAULT_OPERATORS,
            #     columns=cols_to_anonymize,
            # )

        st.success("Done. Here’s a preview of the anonymized data:")
        # st.dataframe(sanitized_df.head())

        # # Prepare downloadable CSV
        # buffer = io.StringIO()
        # sanitized_df.to_csv(buffer, index=False)
        # buffer.seek(0)
        # csv_str = buffer.getvalue()  # ✅ plain string

        st.download_button(
            label="⬇️ Download anonymized Slack Data",
            data=json.dumps(slack_folder_data),
            file_name="slack_folder.json",
            mime="application/json",
        )

        st.caption(
            "Note: automated PII detection is not perfect. "
            "Review before publishing if stakes are high."
        )


if __name__ == "__main__":
    main()
