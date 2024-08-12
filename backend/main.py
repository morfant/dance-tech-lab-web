# main.py

import pprint
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import asyncio
# from agent import get_graph  # 에이전트 가져오기
from agents import get_graph  # 에이전트 가져오기

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
            # print("user_input: ", user_input)

            response_message = ""
            partial_message = ""

            inputs = {"question": user_input}
            for output in graph.stream(inputs):
                for key, value in output.items():
                    print('\n')
                    pprint.pprint(f">> Node: [{key}]")
                    pprint.pprint("------------------------------------")
                    pprint.pprint({"STATE": value}, indent=2, width=80, depth=None)

                    # value에 포함될 수 있는, web 에 출력 되어야 하는 key 들
                    _plan = value.get('plan')
                    _generation = value.get('generation')
                    _research = value.get('research')

                    response_message = _plan or _generation or _research

                    # 타이핑 효과를 위해, 실시간으로 클라이언트에게 부분적으로 응답을 전송
                    if response_message != None:
                        for char in response_message[len(partial_message):]:
                            partial_message += char
                            await websocket.send_json({"response": partial_message, "agentType": key})
                            await asyncio.sleep(0.01)  # 타이핑 딜레이
                    partial_message = ""

                    await websocket.send_json({"response": "[END]", "agentType": key})

            pprint.pprint("------------------------------------")
            # Final generation
            pprint.pprint(value["generation"])


    except WebSocketDisconnect:
        print("WebSocket connection closed")

    except Exception as e:
        print(f"WebSocket Error: {e}")
        await websocket.close()

# FastAPI 실행
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)