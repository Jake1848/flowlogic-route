import React, { useState } from 'react';
import { useAppStore } from '../../store/useAppStore';
import { Send, Bot, User } from 'lucide-react';
import { cn } from '../../utils/cn';
import { Button } from '../ui/button';
import { useRouting } from '../../hooks/useRouting';

const ChatInput: React.FC = () => {
  const [input, setInput] = useState('');
  const [chatHistory, setChatHistory] = useState<Array<{id: string, type: 'user' | 'assistant', content: string}>>([]);
  const [isTyping, setIsTyping] = useState(false);
  
  const { 
    specialInstructions,
    setSpecialInstructions,
  } = useAppStore();
  
  const { generateRoutes, isLoading } = useRouting();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage = {
      id: Date.now().toString(),
      type: 'user' as const,
      content: input.trim()
    };

    setChatHistory(prev => [...prev, userMessage]);
    setSpecialInstructions(input.trim());
    setInput('');

    // Simulate AI response
    setIsTyping(true);
    setTimeout(() => {
      const response = getAutomatedResponse(input.trim());
      setChatHistory(prev => [...prev, {
        id: (Date.now() + 1).toString(),
        type: 'assistant' as const,
        content: response
      }]);
      setIsTyping(false);
    }, 1000);
  };

  const getAutomatedResponse = (input: string): string => {
    const lowerInput = input.toLowerCase();
    
    // Constraint acknowledgments
    if (lowerInput.includes('avoid') || lowerInput.includes('priority') || lowerInput.includes('first') || lowerInput.includes('last')) {
      return "Got it! I've noted your routing constraint. When you generate routes, I'll make sure to apply this rule to optimize your delivery sequence.";
    }

    // Time-related constraints
    if (lowerInput.includes('time') || lowerInput.includes('hour') || lowerInput.includes('morning') || lowerInput.includes('afternoon')) {
      return "Time constraint understood! I'll factor in your timing preferences when generating routes and estimating delivery windows.";
    }

    // Cost optimization
    if (lowerInput.includes('cost') || lowerInput.includes('fuel') || lowerInput.includes('save') || lowerInput.includes('budget')) {
      return "I'll optimize for cost efficiency! This includes minimizing fuel costs, reducing total miles, and maximizing truck utilization.";
    }

    // Geographic constraints
    if (lowerInput.includes('highway') || lowerInput.includes('downtown') || lowerInput.includes('area') || lowerInput.includes('zone')) {
      return "Geographic constraint noted! I'll make sure to respect your area preferences and route restrictions during optimization.";
    }

    // Truck/fleet related
    if (lowerInput.includes('truck') || lowerInput.includes('vehicle') || lowerInput.includes('fleet')) {
      return "Fleet constraint recorded! I'll automatically generate an appropriate truck fleet or apply your specific vehicle requirements.";
    }

    // Default helpful response
    return "I've recorded your constraint. These preferences will be applied when optimizing your routes to ensure the best possible delivery sequence.";
  };

  const quickPrompts = [
    "Avoid highways during rush hour",
    "Prioritize refrigerated deliveries first", 
    "Keep routes under 8 hours each",
    "Minimize fuel costs",
    "Stay within city limits"
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
              "flex items-start space-x-2",
              message.type === 'user' ? 'flex-row-reverse space-x-reverse' : ''
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