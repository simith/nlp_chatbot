import streamlit as st
import psycopg2
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.llms import OpenAI
from langchain.chains.question_answering import load_qa_chain
import pandas as pd
import altair as alt

#@st.cache_resource
def init_connection():
    return psycopg2.connect(**st.secrets["postgres"])

conn = init_connection()

def get_df(colnames,results):
    y_axis_arr = []
    x_axis_arr = []
    for r in results:
        x_axis_arr.append(str(r[0]))
        y_axis_arr.append(r[1])
    df = pd.DataFrame({
        colnames[1]: y_axis_arr,
        colnames[0]: x_axis_arr
    })
    return df


# Perform query.
# Uses st.cache_data to only rerun when the query changes or after 10 min.
#@st.cache_data(ttl=600)
def run_query(query):
    err = None
    colnames = None
    rows = None
    with conn.cursor() as cur:
        try:
            cur.execute(query)
            colnames = [desc[0] for desc in cur.description]
            rows = cur.fetchall()
        except Exception as e:
            err = str(e)
            print(err)
    return err,colnames,rows
            

def query_llm(user_query):
    #need to go to secrets - TODO
    OPENAI_API_KEY="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"
    llm = OpenAI(temperature=0, openai_api_key=OPENAI_API_KEY)
    query = f"### Postgres SQL tables, with their properties:\
         fire_calls(caller_phone_number,city,zip_code)\
         use group by clause to group and summarise \
         use count(*) as number of ... when naming columns, include count where possible\
         always return sql query in descending order where possible\
         suburbs can also mean zip_codes\
         {user_query}\
         SELECT"

    chain = load_qa_chain(llm, chain_type="stuff")
    llm_response = chain.run(input_documents=[],question=query,verbose=True)
    return llm_response

#########################################################################################
############ STREAMLIT RUNS THIS CODE on each RENDER ####################################
#########################################################################################

st.title("Echo Bot")

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

    llm_response = query_llm(prompt)
    #validate the response, sanity checks - TODO, throw exception and handle
    #response to user 
    print(llm_response)
    err,colnames,result_set = run_query(llm_response)
    print(result_set)
    df = get_df(colnames,result_set)
    bar_chart = alt.Chart(df).mark_bar().encode(
        x=alt.X(colnames[0],sort=None),
        y=alt.Y(colnames[1]) 
    )
    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        if err == None:
            st.altair_chart(bar_chart, use_container_width=True)
            resp_msg = "need to figure out a way to save the chart in the conversation - TODO"
        else:
            resp_msg = st.markdown("Sorry, i'm not sure")
           
        

    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": resp_msg})