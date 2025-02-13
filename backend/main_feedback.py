import json
import pprint
# from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import asyncio

# from agent import get_graph  # 에이전트 가져오기
# from agents_ import get_graph  # 에이전트 가져오기
# from agents_ import initialPlan, Review, Research, Result
from agents_for_feedback import get_graph,initialPlan, Review, Research, Result  # 에이전트 가져오기

from langchain_core.messages import AIMessage
# from langchain_core.messages import AIMessage
from langchain_core.runnables.config import RunnableConfig


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


def object_to_json_string(obj, key_to_remove='documents'):
    """
    객체에서 특정 키를 제거한 후 JSON 문자열로 변환하는 함수.
    
    Args:
        obj (dict): 변환할 객체.
        key_to_remove (str, optional): 제거할 키. 기본값은 None.
        
    Returns:
        str: JSON 문자열.
    """
    if key_to_remove and key_to_remove in obj:
        del obj[key_to_remove]
    
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
        # print(">> json_dict:{}".format(json_dict))
        
        # 키의 값을 반환
        return json_dict.get(key, None)
    except json.JSONDecodeError as e:
        return f"Error decoding JSON: {e}"


def has_key_in_json(json_string, key):
    """
    JSON 문자열에서 특정 키의 존재 여부를 검사하는 함수.
    
    Args:
        json_string (str): JSON 문자열.
        key (str): 검사할 키.
        
    Returns:
        bool: 키의 존재 여부.
    """
    try:
        # JSON 문자열을 Python 딕셔너리로 변환
        json_dict = json.loads(json_string)
        
        # 키의 존재 여부를 반환
        return key in json_dict
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
# 정적 파일 경로를 '/static'으로 설정하고, 파일들이 저장된 디렉토리를 지정
# app.mount("/static", StaticFiles(directory="static"), name="static")

# 컴파일된 그래프 가져오기
graph = get_graph()

# config = RunnableConfig(recursion_limit=100)
config = {"configurable": {"thread_id": "1"}}
print(config)

researcher_index = 0

@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    global researcher_index  # 전역 변수로서 접근을 명시

    await websocket.accept()

    try:
        feedback = False
        inputs = None

        while True:
            data = await websocket.receive_json()

            # "heartbeat" 메시지인지 확인
            if data.get("heartbeat") == "ping":
                # await websocket.send_json({"response": "pong", "agentType": "heartbeat"})
                continue  # "heartbeat" 메시지일 경우, 아래의 로직을 건너뜁니다.

            user_input = data.get("message", "")
            # print("user_input: ", user_input)

            response_message = ""
            partial_message = ""

            if feedback is False: #처음 질문할 때 ###
                print(">> 요청을 전달합니다.")
                inputs = {"question": user_input}

            else:   #그 이후에 피드백할 때  ###   
                print(">> 작성하신 피드백 전달합니다. {}".format(user_input))

                graph.update_state(
                            config,
                            # The updated values to provide. The messages in our `State` are "append-only", meaning this will be appended
                            # to the existing state. We will review how to update existing messages in the next section!
                            {"user_feedback": user_input},
                )

                inputs = None
                feedback = False

            next_node = None    

            for output in graph.stream(inputs, config):
                snapshot = graph.get_state(config)
                next_node = snapshot.next

                for key, value in output.items():
                    print('\n')
                    pprint.pprint("----------------------------------------------------------------------------------------------------------------")
                    pprint.pprint(f">> Node: [{key}]")
                    # pprint.pprint({"STATE": value}, indent=2, width=80, depth=None)
                    print(">> value: ", value)

                    if key != '__interrupt__':

                        if key == 'critic':
                            print("-------critic!--------")
                            
                            # print(f"{key_}:, {value_}")
                            result = "\n".join([f"{key_}, : {value_}" for key_, value_ in value.items()])
                            
                            response_message = result

                        else:
                            initialPlan_ = find_instance_of(value, initialPlan)
                            review_ = find_instance_of(value, Review)
                            research_ = find_instance_of(value, Research)
                            generation_ = find_instance_of(value, AIMessage)
                            # generation_ = find_instance_of(value, Result) 

                            # print("****************")
                            # print(type(initialPlan_))
                            # print(initialPlan_)

                            if initialPlan_ != None:
                                response_message = format_initial_plan_response(initialPlan_)

                            elif review_ != None:
                                response_message = format_review_response(review_)

                            elif research_ != None:
                                response_message = format_research_response(research_)

                            elif generation_ != None:
                                response_message = generation_.content
                                # response_message = generation_.report
    
                            else:
                                print("--------------Other types--------------")
                                response_message = object_to_json_string(value)
                                print("response message")
                                print(response_message)
                                research_direction_ = get_value_from_json(response_message, "research_direction")
                                print("research direction")
                                print(research_direction_)
                                research_archive_ = get_value_from_json(response_message, "archive")
                                print("research archive")
                                print(research_archive_)

                                if research_direction_ != None and key == 'research_director':
                                    response_message = research_direction_
                                elif research_archive_ != None and key == 'researcher':
                                    response_message = research_archive_[-1]
                                    key = key + "_" + str(researcher_index)
                                    researcher_index = researcher_index + 1
                                    researcher_index = researcher_index % 3 # researcher 의 css 스타일에 3가지 변주가 가능
                                else:
                                    response_message = None

                        print(">> Node: ", key)
                        print(">> response_message: ", response_message)
                       
                        # 타이핑 효과를 위해, 실시간으로 클라이언트에게 부분적으로 응답을 전송
                        chunk_size = 30  # 한 번에 보낼 글자의 수를 설정, 클수록 출력 빠름

                        if response_message != None:
                            for i in range(len(partial_message), len(response_message), chunk_size):
                                partial_message += response_message[i:i+chunk_size]
                                await websocket.send_json({"response": partial_message, "agentType": key})
                                await asyncio.sleep(0.001)  # 타이핑 딜레이
                        partial_message = ""

                        # await websocket.send_json({"response": "[END]", "agentType": key})

                    else:
                        print(">> interupted!")    
                        await websocket.send_json({"response": "[FEEDBACK]", "agentType": key}) ## activate the input

            pprint.pprint("END OF CYCLE ---------------------------------------------------------------------")
            
            # Final generation
            # pprint.pprint(value["generation"])

            ### LAST NODE OF THE GRAPH
            if len(next_node) == 0:
                if feedback == False:
                    print(">> REQUEST TIME AGAIN")
                    print("요청을 입력해주세요.")#웹상에서 대화 형식으로 표시되어야 함! (구현 필요)
                    input_description = "요청을 입력해주세요."
                    await websocket.send_json({"response":  input_description, "agentType": 'prompter'}) #KEY 값
                    await websocket.send_json({"response": "[END]", "agentType": key})
                    # feedback = False
                    
            ### interruptions before nodes
            else:
                if feedback == False:
                    print(">> FEEDBACK TIME")
                    feedback = True
                    print("피드백 하실 내용을 입력해주세요.") #웹상에서 대화 형식으로 표시되어야 함! (구현 필요)
                    input_description = "피드백 하실 내용을 입력해주세요. 괜찮으시면 OK 라고 입력해주세요. : "   
                    await websocket.send_json({"response":  input_description, "agentType":'prompter'})  #KEY 값

    except WebSocketDisconnect:
        print("WebSocket connection closed")

    except Exception as e:
        print(f"WebSocket Error: {e}")
        await websocket.close()

# FastAPI 실행
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main_feedback:app", host="0.0.0.0", port=4001)
