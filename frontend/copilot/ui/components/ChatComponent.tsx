"use client";
import React, { useState } from 'react';
import { CopilotChat } from "@copilotkit/react-ui";
import "@copilotkit/react-ui/styles.css";

interface Message {
    role: 'user' | 'assistant';
    content: string;
}

const ChatComponent: React.FC = () => {
    const [messages, setMessages] = useState<Message[]>([]);

    // Handler for sending a message
    const handleSendMessage = async (message: string) => {
        const userMessage: Message = { role: 'user', content: message };
        setMessages((prevMessages) => [...prevMessages, userMessage]);

        // API call to backend (Arxiv Agent)
        try {
            const response = await fetch('/api/copilotkit_remote', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ messages: [...messages, userMessage] }),
            });

            const data = await response.json();
            const assistantMessage: Message = { role: 'assistant', content: data.content || 'No response' };

            setMessages((prevMessages) => [...prevMessages, assistantMessage]);
        } catch (error) {
            console.error('Error fetching from Arxiv Agent:', error);
            setMessages((prevMessages) => [
                ...prevMessages,
                { role: 'assistant', content: 'Error: Could not reach the server' },
            ]);
        }
    };

    return (
        <CopilotChat
            messages={messages}
            onMessageSend={handleSendMessage}
            placeholder="Ask something about research papers..."
        />
    );
};

export default ChatComponent;
