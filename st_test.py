import streamlit as st
import pandas as pd
import numpy as np

# Title of the app
st.title('Simple File Download App')

# Create a sample DataFrame
data = {
    'Column 1': np.random.randn(10),
    'Column 2': np.random.randn(10),
    'Column 3': np.random.randn(10)
}
df = pd.DataFrame(data)

# Display the DataFrame
st.write('Here is a sample DataFrame:')
st.write(df)

# Convert DataFrame to CSV
csv = df.to_csv(index=False)

# Create a download button
st.download_button(
    label='Download CSV',
    data=csv,
    file_name='sample_data.csv',
    mime='text/csv'
)

# Additional text
st.write('Click the button above to download the CSV file.')
