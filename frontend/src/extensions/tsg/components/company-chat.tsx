'use client'

import { useState } from 'react'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Send } from 'lucide-react'
import { useTsgChat } from '../hooks/use-tsg-api'

interface Message {
  role: 'user' | 'assistant'
  content: string
  source?: string
  type?: string
}

export function CompanyChat({ companyId }: { companyId: string }) {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const chat = useTsgChat()

  const handleSend = async () => {
    if (!input.trim()) return
    const question = input.trim()
    setInput('')

    setMessages((prev) => [...prev, { role: 'user', content: question }])

    try {
      const result = await chat.mutateAsync({ question, company_id: companyId })
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: result.answer,
          source: result.source || undefined,
          type: result.answer_type,
        },
      ])
    } catch (err: any) {
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: 'Bir hata oluştu. Lütfen tekrar deneyin.', type: 'error' },
      ])
    }
  }

  return (
    <div className="flex flex-col h-[500px]">
      {/* Mesajlar */}
      <div className="flex-1 overflow-y-auto space-y-3 p-4">
        {messages.length === 0 && (
          <div className="text-center text-muted-foreground text-sm mt-8">
            <p>Bu şirket hakkında soru sorun.</p>
            <div className="mt-4 space-y-1 text-xs">
              <p className="text-muted-foreground/60">Örnek sorular:</p>
              <p>&quot;Yönetim kurulunda kimler var?&quot;</p>
              <p>&quot;Sermaye ne zaman değişti?&quot;</p>
              <p>&quot;Şirketin faaliyet konusu ne?&quot;</p>
            </div>
          </div>
        )}
        {messages.map((m, i) => (
          <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div
              className={`max-w-[80%] rounded-lg p-3 text-sm ${
                m.role === 'user'
                  ? 'bg-primary text-primary-foreground'
                  : 'bg-muted'
              }`}
            >
              <div className="whitespace-pre-wrap">{m.content}</div>
              {m.source && (
                <div className="text-xs opacity-60 mt-2 border-t border-current/10 pt-1">
                  📄 {m.source}
                </div>
              )}
              {m.type && m.type !== 'error' && (
                <div className="text-[10px] opacity-40 mt-1">
                  {m.type === 'db' ? 'Veritabanı' : m.type === 'llm' ? 'AI Analiz' : m.type}
                </div>
              )}
            </div>
          </div>
        ))}
        {chat.isPending && (
          <div className="flex justify-start">
            <div className="bg-muted rounded-lg p-3 text-sm text-muted-foreground">
              Düşünüyor...
            </div>
          </div>
        )}
      </div>

      {/* Input */}
      <div className="border-t p-3 flex gap-2">
        <Input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && handleSend()}
          placeholder="Soru sorun..."
          disabled={chat.isPending}
          className="flex-1"
        />
        <Button onClick={handleSend} disabled={chat.isPending || !input.trim()} size="icon">
          <Send className="h-4 w-4" />
        </Button>
      </div>
    </div>
  )
}
