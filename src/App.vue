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
            {{ isFetching ? "......" : "Send" }}
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
      // this.websocket = new WebSocket("ws://unbarrier.net:4001/ws/chat"); // Deploy
      this.websocket = new WebSocket("ws://127.0.0.1:4001/ws/chat"); // Local test

      this.websocket.onmessage = (event) => {
        const data = JSON.parse(event.data);


        if (data.response === "[END]"){
          if (data.agentType === "reporter") {
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

<style src="./App.css"></style>
