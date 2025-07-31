import React, { useState, useRef, useEffect } from 'react';
import { useAppStore } from '../../store/useAppStore';
import { Send, Bot, User, Sparkles } from 'lucide-react';
import { cn } from '../../utils/cn';
import { Button } from '../ui/button';
import { ChatMessage } from '../../types';
import { useRouting } from '../../hooks/useRouting';

const ChatInput: React.FC = () => {
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  
  const { 
    chatHistory, 
    addChatMessage, 
    constraints, 
    setConstraints,
    isLoading
  } = useAppStore();
  
  const { performAutonomousRouting } = useRouting();

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [chatHistory]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      type: 'user',
      content: input,
      timestamp: new Date(),
    };

    addChatMessage(userMessage);
    
    // Update constraints if this looks like routing instructions
    const isRoutingInstruction = /route|deliver|truck|avoid|priority|constraint/i.test(input);
    if (isRoutingInstruction) {
      setConstraints(constraints ? `${constraints}\n${input}` : input);
    }

    setInput('');
    setIsTyping(true);

    // Simulate AI thinking time
    setTimeout(() => {
      const assistantMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: generateAIResponse(input),
        timestamp: new Date(),
      };
      
      addChatMessage(assistantMessage);
      setIsTyping(false);
    }, 1000 + Math.random() * 2000);
  };

  const generateAIResponse = (userInput: string): string => {
    const input = userInput.toLowerCase();
    
    // Route generation requests
    if (input.includes('route') || input.includes('optimize') || input.includes('plan')) {
      return "I'll help you generate optimal routes! Please provide the delivery addresses in the address input below, and I'll apply your routing constraints automatically.";
    }
    
    // Constraint acknowledgments
    if (input.includes('avoid') || input.includes('priority') || input.includes('first') || input.includes('last')) {
      return "Got it! I've noted your routing constraint. When you generate routes, I'll make sure to apply this rule to optimize your delivery sequence.";
    }
    
    // Time-related constraints
    if (input.includes('time') || input.includes('hour') || input.includes('morning') || input.includes('afternoon')) {
      return "Time constraint understood! I'll factor in your timing preferences when generating routes and estimating delivery windows.";
    }
    
    // Cost optimization
    if (input.includes('cost') || input.includes('fuel') || input.includes('save') || input.includes('budget')) {
      return "I'll optimize for cost efficiency! This includes minimizing fuel costs, reducing total miles, and maximizing truck utilization.";
    }
    
    // Geographic constraints
    if (input.includes('highway') || input.includes('downtown') || input.includes('area') || input.includes('zone')) {
      return "Geographic constraint noted! I'll make sure to respect your area preferences and route restrictions during optimization.";
    }
    
    // Truck/fleet related
    if (input.includes('truck') || input.includes('vehicle') || input.includes('fleet')) {
      return "Fleet constraint recorded! I'll automatically generate an appropriate truck fleet or apply your specific vehicle requirements.";
    }
    
    // Default helpful response
    return "I understand! Feel free to describe any routing constraints or preferences in natural language. I can handle complex instructions like 'avoid highways during rush hour' or 'deliver frozen goods first'.";
  };

  const quickPrompts = [
    "Avoid highways during rush hour",
    "Deliver frozen goods first",
    "Keep routes under 150 miles",
    "Complete all deliveries by 3 PM",
    "Minimize fuel costs",
    "Use refrigerated trucks only"
  ];

  return (
    <div className="flex flex-col h-80 bg-card rounded-lg border border-border">
      {/* Chat messages */}
      <div className="flex-1 overflow-y-auto p-3 space-y-3">
        {chatHistory.length === 0 && (
          <div className="text-center py-6">
            <Bot className="h-8 w-8 text-muted-foreground mx-auto mb-2" />
            <p className="text-sm text-muted-foreground">
              Ask me about routing constraints or preferences
            </p>
          </div>
        )}
        
        {chatHistory.map((message) => (
          <div
            key={message.id}
            className={cn(
              "flex items-start space-x-2 animate-fade-in",
              message.type === 'user' ? "justify-end" : "justify-start"
            )}
          >
            {message.type === 'assistant' && (
              <div className="w-6 h-6 bg-primary/10 rounded-full flex items-center justify-center flex-shrink-0">
                <Bot className="h-3 w-3 text-primary" />
              </div>
            )}
            
            <div
              className={cn(
                "max-w-[80%] px-3 py-2 rounded-lg text-sm",
                message.type === 'user'
                  ? "bg-primary text-primary-foreground rounded-br-sm"
                  : "bg-background border border-border rounded-bl-sm"
              )}
            >
              {message.content}
            </div>
            
            {message.type === 'user' && (
              <div className="w-6 h-6 bg-muted rounded-full flex items-center justify-center flex-shrink-0">
                <User className="h-3 w-3 text-muted-foreground" />
              </div>
            )}
          </div>
        ))}
        
        {isTyping && (
          <div className="flex items-start space-x-2">
            <div className="w-6 h-6 bg-primary/10 rounded-full flex items-center justify-center">
              <Bot className="h-3 w-3 text-primary" />
            </div>
            <div className="bg-background border border-border rounded-lg rounded-bl-sm px-3 py-2">
              <div className="flex space-x-1">
                <div className="w-2 h-2 bg-muted-foreground rounded-full animate-pulse"></div>
                <div className="w-2 h-2 bg-muted-foreground rounded-full animate-pulse" style={{animationDelay: '0.2s'}}></div>
                <div className="w-2 h-2 bg-muted-foreground rounded-full animate-pulse" style={{animationDelay: '0.4s'}}></div>
              </div>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>
      
      {/* Quick prompts */}
      {chatHistory.length === 0 && (
        <div className="px-3 pb-2">
          <p className="text-xs text-muted-foreground mb-2">Quick examples:</p>
          <div className="flex flex-wrap gap-1">
            {quickPrompts.slice(0, 3).map((prompt, index) => (
              <Button
                key={index}
                variant="outline"
                size="sm"
                onClick={() => setInput(prompt)}
                className="text-xs h-6"
              >
                {prompt}
              </Button>
            ))}
          </div>
        </div>
      )}
      
      {/* Input form */}
      <form onSubmit={handleSubmit} className="p-3 border-t border-border">
        <div className="flex space-x-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Describe routing constraints..."
            className="flex-1 px-3 py-2 bg-background border border-input rounded-md focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent text-sm"
            disabled={isLoading}
          />
          <Button
            type="submit"
            disabled={!input.trim() || isLoading}
            size="sm"
          >
            <Send className="h-4 w-4" />
          </Button>
        </div>
      </form>
    </div>
  );
};

export default ChatInput;