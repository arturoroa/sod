import React, { useState } from 'react';
import { View, Text, TextInput, TouchableOpacity } from 'react-native';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Header } from '../widgets/components';
import { httpRequest } from '../services/generalService';
import { getSessionData } from '../services/storage';

type ChatMessage = {
  role: 'user' | 'assistant' | 'system';
  text: string;
};

const STORAGE_KEY = 'aiChatMessages';

const AIAnalysis: React.FC<{ session:(value:boolean)=>void }> = ({ session }) => {
  const initialMessages: ChatMessage[] = [
    { role: 'system', text: 'Ai Chat Assistance ready.' },
  ];

  const [messages, setMessages] = useState<ChatMessage[]>(() => {
    try {
      const stored = window.sessionStorage.getItem(STORAGE_KEY);
      if (stored) {
        const parsed = JSON.parse(stored) as ChatMessage[];
        if (Array.isArray(parsed) && parsed.length > 0) {
          return parsed;
        }
      }
    } catch {
      // ignore storage errors
    }
    return initialMessages;
  });
  const [input, setInput] = useState('');
  const [isSending, setIsSending] = useState(false);

  const persistMessages = (updatedMessages: ChatMessage[]) => {
    setMessages(updatedMessages);
    try {
      window.sessionStorage.setItem(STORAGE_KEY, JSON.stringify(updatedMessages));
    } catch {
      // ignore storage errors
    }
  };

  const clearHistory = () => {
    persistMessages(initialMessages);
    try {
      window.sessionStorage.removeItem(STORAGE_KEY);
    } catch {
      // ignore storage errors
    }
  };

  const sendMessage = async () => {
    if (!input.trim() || isSending) return;
    const userMessage: ChatMessage = { role: 'user', text: input.trim() };
    const queuedMessages: ChatMessage[] = [...messages, userMessage, { role: 'assistant', text: 'Sending your query to the backend... please wait.' }];
    persistMessages(queuedMessages);
    setInput('');
    setIsSending(true);

    const sessionData = getSessionData();
    const chatHistory = [...messages, userMessage]
      .filter((msg) => msg.role !== 'assistant' || msg.text !== 'Sending your query to the backend... please wait.');

    const response = await httpRequest('POST', '/chat', {
      session: sessionData,
      message: userMessage.text,
      history: chatHistory,
    });

    setIsSending(false);
    const assistantText = response?.assistant || response?.detail || response?.error || 'No response received from AI.';
    persistMessages([
      ...queuedMessages.filter((msg) => msg.role !== 'assistant' || msg.text !== 'Sending your query to the backend... please wait.'),
      { role: 'assistant', text: assistantText },
    ]);
  };

  return (
    <View className="flex flex-col h-screen bg-gray-100 font-sans w-full overflow-hidden">
      <Header title="Ai Chat Assistance" />
      <View className="flex flex-col flex-1 p-4 space-y-4" style={{ minHeight: 0 }}>
        <View className="rounded-xl bg-white border border-gray-200 p-4 shadow-sm">
          <View className="flex-row items-center justify-between flex-wrap gap-3">
            <Text className="text-lg font-semibold text-slate-900">Ai Chat Assistance</Text>
          </View>
          <Text className="text-sm text-slate-600 mt-2">
            Chat history is preserved until you clear it.
          </Text>
        </View>

        <View className="flex-1 rounded-xl bg-white border border-gray-200 p-4 shadow-sm overflow-hidden" style={{ minHeight: 0, flexDirection: 'column' }}>
          <Text className="text-sm uppercase tracking-[0.16em] text-slate-500 font-semibold mb-3">Chat</Text>
          <View className="rounded-xl bg-slate-50 border border-slate-200 p-3 mb-4 overflow-hidden" style={{ minHeight: 0 }}>
            <div style={{ maxHeight: 'calc(100vh - 480px)', minHeight: 0, overflowY: 'auto', paddingRight: 12, paddingBottom: 12 }}>
              {messages.map((message, index) => (
                <View key={index} className="mb-3 w-full">
                  <View className={message.role === 'user' ? 'rounded-2xl bg-blue-500 px-4 py-3 w-full text-right' : 'rounded-2xl bg-slate-200 px-4 py-3 w-full'}>
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                      {message.text}
                    </ReactMarkdown>
                  </View>
                </View>
              ))}
            </div>
          </View>
          <View className="flex flex-col sm:flex-row sm:items-end sm:gap-3">
            <TextInput
              value={input}
              onChangeText={setInput}
              placeholder="Type your question here..."
              className="flex-1 rounded-xl border border-gray-300 bg-white px-4 py-3 text-slate-900"
              placeholderTextColor="#94a3b8"
              onKeyPress={(e) => {
  if (e.nativeEvent.key === 'Enter') {
    sendMessage();
  }
}}
            />
            <TouchableOpacity
              className="mt-3 sm:mt-0 rounded-xl bg-[#2563eb] px-6 py-3 items-center justify-center"
              onPress={sendMessage}
            >
              <Text className="text-white font-semibold">Submit</Text>
            </TouchableOpacity>
          </View>
          <View className="mt-3 flex-row items-center justify-end">
            <TouchableOpacity onPress={clearHistory} className="rounded-full px-3 py-2 bg-slate-100 hover:bg-slate-200">
              <Text className="text-sm text-slate-600">Clear history</Text>
            </TouchableOpacity>
          </View>
        </View>
      </View>
    </View>
  );
};

export default AIAnalysis;
