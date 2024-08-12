<template>
  <div id="app">
    <div class="sidebar">
      <h2>Menu</h2>
      <ul>
        <li v-for="menu in menus" :key="menu">{{ menu }}</li>
      </ul>
    </div>
    <div class="main-container">
      <div class="chat-container">
        <h1>Dance Tech Lab</h1>
        <div class="chat-box">
          <div
            v-for="(message, index) in messages"
            :key="index"
            :class="['message', message.sender]"
            v-html="renderMessage(message.text)"
          ></div>
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
      menus: ["Home", "About", "Services", "Contact"], // 메뉴 항목 추가
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

        if (data.response === "[END]") {
          this.isFetching = false;
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
      this.isFetching = true;
      this.websocket.send(JSON.stringify({ message: this.userInput }));
      this.userInput = "";
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
/* 기본 스타일 설정 */
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  display: flex;
  height: 100vh;
  margin: 0;
  background-color: #f5f5f5; /* 전체 배경색을 통일감 있게 설정 */
}

.sidebar {
  width: 200px;
  background-color: #333;
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
  color: #ddd;
}

.sidebar ul li:hover {
  color: #007bff;
}

.main-container {
  margin-left: 220px; /* 사이드바 너비와 여백을 고려한 마진 */
  flex: 1;
  display: flex;
  flex-direction: column;
  height: 100vh;
  background-color: #f5f5f5; /* 사이드바와 같은 배경색 */
}

.chat-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: #fff;
  width: 255%; /* 여기서 기본 width를 설정합니다 */

}

h1 {
  background-color: #007bff; /* 상단 헤더 색상 */
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
  background-color: #007bff; /* 사용자 메시지 색상 */
  color: #fff;
}

.input-container {
  display: flex;
  padding: 10px;
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
  background-color: #007bff; /* 버튼 색상 통일 */
  color: white;
  font-size: 16px;
  border-radius: 20px;
  cursor: pointer;
  transition: background-color 0.3s ease;
}

.send-button:hover {
  background-color: #0056b3;
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
</style>