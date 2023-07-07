import pandas as pd
import streamlit as st
import numpy as np
import altair as alt

def get_df(colnames,results):
  
    y_axis_arr = []
    x_axis_arr = []

    for r in results:
        x_axis_arr.append(r[0])
        y_axis_arr.append(r[1])
        print(r)
    
    df = pd.DataFrame({
        colnames[1]: y_axis_arr,
        colnames[0]: x_axis_arr
    })
    print(df)

    return df

    




st.title("Echo Bot")
colnames = ['zip_codes','number_of_calls']
# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# React to user input
if prompt := st.chat_input("What is up?"):
    # Display user message in chat message container
    st.chat_message("user").markdown(prompt)
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
 
    results = [("KA",90),("MH",30),("TN",50)]
    df = get_df(colnames,results)
    bar_chart = alt.Chart(df).mark_bar().encode(
        y=colnames[1],
        x=colnames[0]
    )



    print(np.random.randn(3, 3))
    with st.chat_message("assistant"):
        chart_data = pd.DataFrame(
        np.random.randn(1, 3),
        columns=["a", "b", "c"])
        #st.bar_chart(chart_data)
        st.altair_chart(bar_chart, use_container_width=True)
    

    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": f"Echo {prompt}"})

