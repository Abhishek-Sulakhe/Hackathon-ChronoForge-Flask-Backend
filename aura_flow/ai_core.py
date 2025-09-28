from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema.output_parser import StrOutputParser
from langchain.schema.runnable import RunnablePassthrough
from deepgram import DeepgramClient, PrerecordedOptions
from dotenv import load_dotenv
import os




from aura_flow.prompts.debate_prompts import (
    DEBATE_PROMPT_TEMPLATE,
    REALTIME_FEEDBACK_PROMPT_TEMPLATE,
    FINAL_JUDGEMENT_PROMPT_TEMPLATE,
    WINNER_JUDGE_PROMPT_TEMPLATE,
    COACH_PROMPT_TEMPLATE
)
from aura_flow.prompts.roast_prompts import(
    COACH_PROMPT_TEMPLATE,
    FINAL_PERFORMANCE_REVIEW_PROMPT_TEMPLATE,
    REALTIME_COMEDY_FEEDBACK_PROMPT_TEMPLATE,
    ROAST_JUDGE_PROMPT_TEMPLATE,
    ROAST_OPPONENT_PROMPT_TEMPLATE
)

# Initialize Deepgram
load_dotenv()
DG_API_KEY = os.getenv("DEEPGRAM_API_KEY")
deepgram = DeepgramClient(DG_API_KEY)


# Initialize OpenAI LLM
# A single powerful model is used for all tasks
try:
    llm = ChatOpenAI(model="provider-3/gpt-4o-mini", temperature=0.7)
    # A more deterministic model for JSON outputs
    json_llm = ChatOpenAI(model="provider-3/gpt-4o-mini", temperature=0.2)
except Exception as e:
    print(f"Error initializing OpenAI model: {e}")
    exit()

# --- Chain for Interactive Debate ---
debate_prompt = ChatPromptTemplate.from_template(DEBATE_PROMPT_TEMPLATE)
debate_chain = (
    {"topic": RunnablePassthrough(), "chat_history": RunnablePassthrough(), "user_input": RunnablePassthrough()}
    | debate_prompt
    | llm
    | StrOutputParser()
)

# --- Chain for Real-time Language Feedback ---
feedback_prompt = ChatPromptTemplate.from_template(REALTIME_FEEDBACK_PROMPT_TEMPLATE)
language_feedback_chain = (
    {"user_input": RunnablePassthrough()}
    | feedback_prompt
    | llm
    | StrOutputParser()
)

# --- Chain for Final User-Only Judgment ---
final_judgement_prompt = ChatPromptTemplate.from_template(FINAL_JUDGEMENT_PROMPT_TEMPLATE)
final_judgement_chain = (
    {"chat_history": RunnablePassthrough()}
    | final_judgement_prompt
    | llm
    | StrOutputParser()
)


# --- Chain for Determining a Winner (from script 2) ---
winner_judge_prompt = ChatPromptTemplate.from_template(WINNER_JUDGE_PROMPT_TEMPLATE)
winner_judge_chain = winner_judge_prompt | json_llm | StrOutputParser()


# --- Chain for Detailed Player Coaching (from script 2) ---
coach_prompt = ChatPromptTemplate.from_template(COACH_PROMPT_TEMPLATE)
coach_chain = coach_prompt | llm | StrOutputParser()




roast_prompt = ChatPromptTemplate.from_template(ROAST_OPPONENT_PROMPT_TEMPLATE)

roast_opponent_chain = (
    {
        "chat_history": RunnablePassthrough(),
        "user_input": RunnablePassthrough(),
    }
    | roast_prompt
    | llm
    | StrOutputParser()
)

# ---

## 2. Real-time Comedy Feedback Chain
# This chain takes only the user's most recent input to provide instant feedback on their joke.

feedback_prompt = ChatPromptTemplate.from_template(REALTIME_COMEDY_FEEDBACK_PROMPT_TEMPLATE)

realtime_comedy_feedback_chain = (
    {"user_input": RunnablePassthrough()}
    | feedback_prompt
    | llm
    | StrOutputParser()
)

# ---

## 3. Final Performance Review Chain
# This chain takes the entire chat history to generate a final, structured review of the user's performance.

review_prompt = ChatPromptTemplate.from_template(FINAL_PERFORMANCE_REVIEW_PROMPT_TEMPLATE)

final_performance_review_chain = (
    {"chat_history": RunnablePassthrough()}
    | review_prompt
    | llm
    | StrOutputParser()
)


## 1. Comedy Coach Chain
# This chain takes a roaster's text and provides structured feedback.

coach_prompt = ChatPromptTemplate.from_template(COACH_PROMPT_TEMPLATE)

coach_chain = (
    {"player_text": RunnablePassthrough()}
    | coach_prompt
    | llm
    | StrOutputParser()
)

# ---

## 2. Roast Judge Chain
# This chain takes a full transcript and determines a winner, outputting in JSON format.

judge_prompt = ChatPromptTemplate.from_template(ROAST_JUDGE_PROMPT_TEMPLATE)

roast_judge_chain = (
    {"transcript": RunnablePassthrough()}
    | judge_prompt
    | llm
    | StrOutputParser()
)