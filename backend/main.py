# main.py

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import asyncio
from agent import get_graph  # 에이전트 가져오기

app = FastAPI()

# 컴파일된 그래프 가져오기
graph = get_graph()

@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    await websocket.accept()

    try:
        while True:
            data = await websocket.receive_json()
            user_input = data.get("message", "")

            state = {"messages": [("user", user_input)]}
            response_message = ""
            partial_message = ""

            # 동기 제너레이터를 반복하면서 비동기적으로 처리
            for event in graph.stream(state):
                for value in event.values():
                    response_message = value["messages"][-1].content

                # 실시간으로 클라이언트에게 부분적으로 응답을 전송
                for char in response_message[len(partial_message):]:
                    partial_message += char
                    await websocket.send_json({"response": partial_message})
                    await asyncio.sleep(0.05)  # 타이핑 딜레이

            await websocket.send_json({"response": "[END]"})

    except WebSocketDisconnect:
        print("WebSocket connection closed")

    except Exception as e:
        print(f"Error: {e}")
        await websocket.close()

# FastAPI 실행
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)