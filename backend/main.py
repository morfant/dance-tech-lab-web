from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_openai import ChatOpenAI
from typing import Annotated
from typing_extensions import TypedDict

app = FastAPI()

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 모든 출처 허용 (프로덕션에서는 특정 도메인으로 제한하는 것이 좋습니다)
    allow_credentials=True,
    allow_methods=["*"],  # 모든 메서드 허용
    allow_headers=["*"],  # 모든 헤더 허용
)

# 환경 변수 설정
import os
import getpass

def _set_env(var: str):
    if not os.environ.get(var):
        os.environ[var] = getpass.getpass(f"{var}: ")

_set_env("OPENAI_API_KEY")
_set_env("LANGSMITH_API_KEY")
os.environ["LANGCHAIN_PROJECT"] = "LangGraph Tutorial"

# 메시지 상태 관리 설정
class State(TypedDict):
    messages: Annotated[list, add_messages]

graph_builder = StateGraph(State)
llm = ChatOpenAI(model="gpt-4o")

def chatbot(state: State):
    return {"messages": [llm.invoke(state["messages"])]}

# 챗봇 노드 및 엣지 설정
graph_builder.add_node("chatbot", chatbot)
graph_builder.add_edge(START, "chatbot")
graph_builder.add_edge("chatbot", END)
graph = graph_builder.compile()

# 사용자 메시지 모델
class UserMessage(BaseModel):
    message: str

@app.post("/chat")
def chat_endpoint(user_message: UserMessage):
    user_input = user_message.message
    state = {"messages": [("user", user_input)]}
    
    try:
        # 그래프 실행 및 응답 메시지 생성
        for event in graph.stream(state):
            for value in event.values():
                response = value["messages"][-1].content
                return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))