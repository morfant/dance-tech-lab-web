<template>
  <div id="app">
    <div class="sidebar">
      <h2>AI Collaborator</h2>
      <ul>
        <li 
          v-for="menu in menus" 
          :key="menu" 
          @click="setActiveMenu(menu)"
          :class="{ active: menu === activeMenu }"
        >
          {{ menu }}
        </li>
      </ul>


    </div>
    <div class="main-container">
      <div class="chat-container">
        <h1>{{ activeMenu }}</h1>
        <div class="chat-box">
          <div
            v-for="(message, index) in messages"
            :key="index"
            :class="['message', message.sender]"
            v-html="renderMessage(message.text)"
          ></div>
          <div v-if="isFetching" class="loading-indicator">응답을 받아오는 중입니다...</div>
        </div>
        <div class="input-container">
          <input
            v-model="userInput"
            @keyup.enter="handleButtonClick"
            placeholder="Type a message..."
            class="input-box"
            :disabled="isFetching"
          />
          <button @click="handleButtonClick" class="send-button">
            {{ isFetching ? "Sending..." : "Send" }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { marked } from "marked";

export default {
  data() {
    return {
      userInput: "",
      messages: [],
      isFetching: false,
      websocket: null,
      menus: ["Research", "Rehearsal", "Production", "Feedback"], // 메뉴 항목 추가
      activeMenu: "Research", // 기본 메뉴 설정
    };
  },
  methods: {
    handleButtonClick() {
      if (!this.isFetching) {
        this.sendMessage();
      }
    },
    connectWebSocket() {
      console.log("connectWebSocket()");
      this.websocket = new WebSocket("ws://localhost:8000/ws/chat");

      this.websocket.onmessage = (event) => {
        const data = JSON.parse(event.data);


        if (data.response === "[END]"){
          if (data.agentType === "generate") {
            this.isFetching = false;
          }
        } else {
          const { agentType, response } = data;
          if (
            this.messages.length > 0 &&
            this.messages[this.messages.length - 1].sender === "Bot" &&
            this.messages[this.messages.length - 1].agentType === agentType
          ) {
            const lastMessage = this.messages[this.messages.length - 1];
            lastMessage.text = response;
          } else {
            this.messages.push({ sender: "Bot", text: response, agentType });
          }
          // this.isFetching = false; // 데이터 수신 후 로딩 상태 해제
        }
      };

      this.websocket.onclose = () => {
        console.log("WebSocket connection closed");
        this.isFetching = false;
      };

      this.websocket.onerror = (error) => {
        console.error("WebSocket error:", error);
        this.isFetching = false;
      };
    },
    sendMessage() {
      console.log("sendMessage()");
      if (this.userInput.trim() === "") return;
      this.messages.push({
        sender: "User",
        text: this.userInput,
        agentType: "User",
      });
      this.isFetching = true; // 메시지 전송 시 로딩 상태 설정
      this.websocket.send(JSON.stringify({ message: this.userInput }));
      this.userInput = "";
    },
    setActiveMenu(menu) {
      this.activeMenu = menu; // 선택된 메뉴 항목 설정
    },
    renderMessage(text) {
      return marked.parse(text);
    },
  },
  mounted() {
    this.connectWebSocket();
  },
};
</script>

<style>

body {
  margin-top: 0px;
}
/* 기본 스타일 설정 */
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  display: flex;
  height: 100vh;
  margin: 0 auto;
  background-color: #ffffff; /* 전체 배경색을 통일감 있게 설정 */
  width: 100%;
}

.sidebar {
  width: 200px;
  background-color: #599898;
  padding: 20px;
  box-shadow: 2px 0 5px rgba(0, 0, 0, 0.1);
  position: fixed;
  top: 0;
  left: 0;
  height: 100vh;
}

.sidebar h2 {
  color: #fff;
  margin-bottom: 20px;
}

.sidebar ul {
  list-style: none;
  padding: 0;
}

.sidebar ul li {
  margin: 10px 0;
  cursor: pointer;
  color: #ffffff;
  font-size: larger;
}

.sidebar ul li:hover {
  color: #01050f;
}

.main-container {
  margin-left: 220px; /* 사이드바 너비와 여백을 고려한 마진 */
  flex: 1;
  display: flex;
  flex-direction: column;
  height: 100vh;
  background-color: #ffffff; /* 사이드바와 같은 배경색 */

}

.chat-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: #fff;

  width: 100%;
  max-width: 1200px; /* 여기서 기본 width를 설정합니다 */
  margin: 0 auto;
}

h1 {
  background-color: #4b8b9f; /* 상단 헤더 색상 */
  color: white;
  padding: 15px;
  margin: 0;
  text-align: center;
  border-bottom: 1px solid #e0e0e0; /* 헤더와 내용물 구분 */
}

.chat-box {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
  background-color: #f9f9f9; /* 채팅 박스 배경색 */
}

.message {
  padding: 10px;
  margin-bottom: 10px;
  border-radius: 4px;
  width: 100%; /* 메시지가 채팅 박스의 전체 너비를 사용하도록 설정 */
  box-sizing: border-box; /* 패딩과 테두리까지 포함하여 width를 설정 */
}

.message.Bot {
  background-color: #e9ecef; /* 봇 메시지 색상 */
}

.message.User {
  background-color: #75abe4; /* 사용자 메시지 색상 */
  color: #fff;
}

.input-container {
  display: flex;
  padding: 10px 10px 10px 20px;
  background-color: #fff; /* 입력창 배경색 */
  border-top: 1px solid #ddd;
}

.input-box {
  flex: 1;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 20px;
  font-size: 16px;
  outline: none;
}

.input-box:focus {
  border-color: #007bff; /* 입력창 포커스 색상 */
}

.send-button {
  margin-left: 10px;
  padding: 10px 20px;
  border: none;
  background-color: #599898; /* 버튼 색상 통일 */
  color: white;
  font-size: 16px;
  border-radius: 20px;
  cursor: pointer;
  transition: background-color 0.3s ease;
}

.send-button:hover {
  background-color: #31add2;
}

.send-button:disabled,
.input-box:disabled {
  background-color: #ddd;
  cursor: not-allowed;
}

.loading-indicator {
  text-align: center;
  padding: 10px;
  color: #999;
  font-style: italic;
}

.sidebar ul li.active {
  background-color: #007bff; /* 활성화된 메뉴의 배경색 */
  color: #ffffff; /* 활성화된 메뉴의 글자색 */
}
</style>