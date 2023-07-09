import streamlit as st
import psycopg2
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.llms import OpenAI
from langchain.chains.question_answering import load_qa_chain
import pandas as pd
import altair as alt
import time

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
    OPENAI_API_KEY=st.secrets["open_ai_key"]
    llm = OpenAI(temperature=0, openai_api_key=OPENAI_API_KEY)
    query = f"### Postgres SQL tables, with their columns below:\
    fire_calls(caller_phone_number integer,incident_type text,zip_code integer,neighbourhoods integer,year integer,call_received_date date)\
    law_enforcement_calls(incident_number text,incident_type text,received_datetime text,close_datetime text,year integer,district text,call_received_date)\
    ### instructions for SQL query below\
    use group by clause to group and summarise \
    use count(*) as number_of_xxxx when naming columns, include count where possible\
    suburbs can also mean zip_codes, don't hallucinate on table names, use only the one provided\
    all queries regarding law enforcement use the law_enforcement_calls table\
    answer questions for the year upto 2023 inclusive, do not worry about it\
    For date queries always use YYYY-MM-DD format\
    For date queries always use call_received_date\
    if the query has a word trend, sort by the number month or year not the name of the month and do not sort descending or ascending\
    Every column the select clause must be included in the group by clause when group by clause is used\
    To extract month in Postgres sql use to_char(date_column,'MON') instead of month(date_column)\
    For trend queries in Postgre sql use EXTRACT(MONTH FROM current_timestamp) as number\
    When using queries for data types of text, always use upper(incident_type) == 'CAPITALISED INCIDENT TYPE' for a match\
    ### user query below\
    user query: {user_query}\
    SELECT"

    chain = load_qa_chain(llm, chain_type="stuff")
    llm_response = chain.run(input_documents=[],question=query,verbose=True)
    return llm_response

def llm_response_is_valid(llm_response):
    is_valid_response = False
    print(llm_response.strip().startswith("SE"))
    if llm_response.strip().startswith("SE") == True:
        is_valid_response=True
    print(f"Returning {is_valid_response}")
    return is_valid_response
        


#########################################################################################
############ STREAMLIT RUNS THIS CODE on each RENDER ####################################
#########################################################################################

st.title("9-1-1 Calls Analyzer Bot")

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
    print(llm_response)
    #validate the response, sanity checks - TODO, throw exception and handle
    #response to user 
    if llm_response_is_valid(llm_response) == True:
        err,colnames,result_set = run_query(llm_response)
        print(result_set)
        df = get_df(colnames,result_set)
        bar_chart = alt.Chart(df).mark_bar().encode(
            x=alt.X(colnames[0],sort=None),
            y=alt.Y(colnames[1]) 
        )
    else:
        err = {'Error': 'Failed to get a valid LLM response'}
    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        if err == None:
            st.altair_chart(bar_chart, use_container_width=True)
            if st.secrets["debug"] == "ON":
                st.write(llm_response)
            resp_msg = "Render the chart in message history: https://github.com/simith/nlp_chatbot/issues/1"
        else:
            resp_msg = st.markdown("Sorry, i'm not sure")
           
        
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": resp_msg})