# main.py

import json
import pprint
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import asyncio
# from agent import get_graph  # 에이전트 가져오기
from agents_ import get_graph  # 에이전트 가져오기
from agents_ import initialPlan, Review, Research

def find_instance_of(d, cls):
    """
    딕셔너리 d의 모든 값 중에서 cls 클래스의 인스턴스를 재귀적으로 찾아 반환합니다.
    
    :param d: 검사할 딕셔너리
    :param cls: 찾고자 하는 클래스
    :return: cls 클래스의 인스턴스가 존재하면 그 객체를 반환, 존재하지 않으면 None을 반환
    """
    if isinstance(d, dict):
        for value in d.values():
            if isinstance(value, cls):
                return value
            elif isinstance(value, dict):
                result = find_instance_of(value, cls)
                if result is not None:
                    return result
    return None


def object_to_json_string(obj):
    """
    객체를 JSON 문자열로 변환하는 함수.
    
    Args:
        obj (dict): 변환할 객체.
        
    Returns:
        str: JSON 문자열.
    """
    try:
        # 객체를 JSON 문자열로 변환
        json_string = json.dumps(obj, ensure_ascii=False, indent=4)
        return json_string
    except TypeError as e:
        return f"Error converting object to JSON: {e}"


def get_value_from_json(json_string, key):
    """
    JSON 문자열에서 특정 키의 값을 추출하는 함수.
    
    Args:
        json_string (str): JSON 문자열.
        key (str): 값을 추출할 키.
        
    Returns:
        Any: 키에 해당하는 값.
    """
    try:
        # JSON 문자열을 Python 딕셔너리로 변환
        json_dict = json.loads(json_string)
        
        # 키의 값을 반환
        return json_dict.get(key, None)
    except json.JSONDecodeError as e:
        return f"Error decoding JSON: {e}"


def format_initial_plan_response(plan_instance: initialPlan) -> str:
    print("--------------format_initial_plan_response()--------------")
    _dict = plan_instance.dict()
    # print(_dict)
    
    response = (
        f"Explanation:\n{_dict.get('explanation')}\n\n"
        f"Plan:\n" + "\n".join(f"- {step}" for step in _dict.get('plan')) + "\n\n"
        f"Research Areas:\n" + "\n".join(f"- {area}" for area in _dict.get('research_area'))
    )
    return response  

    
def format_review_response(review_instance: Review) -> str:
    print("--------------format_review_response()--------------")
    _dict = review_instance.dict()
    # print(_dict)
    
    response = (
        f"Review Note:\n{_dict.get('review_note')}\n\n"
        f"Plan:\n" + "\n".join(f"- {step}" for step in _dict.get('plan')) + "\n\n"
        f"Research Areas:\n" + "\n".join(f"- {area}" for area in _dict.get('research_area'))
    )
    return response


def format_research_response(research_instance: Research) -> str:
    print("--------------format_research_response()--------------")
    _dict = research_instance.dict()
    # print(_dict)
    
    response = (
        f"Research Direction:\n{_dict.get('research_direction')}\n\n"
        f"Research Areas:\n" + "\n".join(f"- {area}" for area in _dict.get('research_area'))
    )
    return response



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
                    # pprint.pprint({"STATE": value}, indent=2, width=80, depth=None)
                    print("value: ", value)

                    initialPlan_ = find_instance_of(value, initialPlan)
                    review_ = find_instance_of(value, Review)
                    research_ = find_instance_of(value, Research)

                    # print("****************")
                    # print(type(initialPlan_))
                    # print(initialPlan_)

                    if initialPlan_ != None:
                        response_message = format_initial_plan_response(initialPlan_)

                    elif review_ != None:
                        response_message = format_review_response(review_)

                    elif research_ != None:
                        response_message = format_research_response(research_)
                    else:
                        print("--------------Other types--------------")
                        response_message = object_to_json_string(value)
                        research_direction_ = get_value_from_json(response_message, "research_direction")
                        if research_direction_ != None:
                            response_message = research_direction_
                        
                    print("response_message: ", response_message)

                    # 타이핑 효과를 위해, 실시간으로 클라이언트에게 부분적으로 응답을 전송
                    if response_message != None:
                        for char in response_message[len(partial_message):]:
                            partial_message += char
                            await websocket.send_json({"response": partial_message, "agentType": key})
                            await asyncio.sleep(0.001)  # 타이핑 딜레이
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
    uvicorn.run("main:app", host="0.0.0.0", port=4001)
