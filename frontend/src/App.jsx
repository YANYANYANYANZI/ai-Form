import React, { useState, useEffect, useRef } from 'react';
// 💡 引入了新的图标 UploadCloud 和 FileText
import { Database, FileSpreadsheet, Bot, SendHorizontal, Check, X, UploadCloud, FileText } from 'lucide-react';
import axios from 'axios';
import * as echarts from 'echarts';
import '@fortune-sheet/react/dist/index.css';
import DataCanvas from './components/DataCanvas';

function App() {
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [messages, setMessages] = useState([{ role: 'assistant', text: '你好！我是智能分析助手。你可以让我画图、改表，或者上传文档向我提问。' }]);

  // 💡 RAG 知识库上传相关的状态
  const fileInputRef = useRef(null);
  const [knowledgeFiles, setKnowledgeFiles] = useState([]);

  const chartRef = useRef(null);
  const chartInstance = useRef(null);

  useEffect(() => {
    if (chartRef.current) chartInstance.current = echarts.init(chartRef.current);
    return () => { if (chartInstance.current) chartInstance.current.dispose(); };
  }, []);

  // 💡 处理文档上传逻辑
  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    const formData = new FormData();
    formData.append('file', file);
    try {
      setMessages(prev => [...prev, { role: 'assistant', text: `⏳ 正在极速解析文档：${file.name}...` }]);
      const res = await axios.post('http://127.0.0.1:8000/api/v1/upload/', formData);
      if (res.data.status === 'success') {
        setKnowledgeFiles(prev => [...prev, res.data.filename]);
        setMessages(prev => [...prev, { role: 'assistant', text: `✅ 知识库已挂载：${res.data.filename}\n你可以直接向我提问文档里的内容了！` }]);
      }
    } catch (error) {
      setMessages(prev => [...prev, { role: 'assistant', text: '❌ 文档解析失败。' }]);
    }
  };

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;
    const userText = input.trim();
    setMessages(prev => [...prev, { role: 'user', text: userText }]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await axios.post('http://127.0.0.1:8000/api/v1/chat/', { message: userText });
      const data = response.data;

      if (data.intent === 'edit_table') {
         const editId = Date.now();
         setMessages(prev => [...prev, { role: 'assistant', type: 'proposal', text: '修改已高亮显示在左侧表格中，请审核。', updates: data.sheet_updates, status: 'pending', editId: editId }]);
         window.dispatchEvent(new CustomEvent('ai_sheet_preview', { detail: { id: editId, updates: data.sheet_updates } }));
      }
      // 💡 处理日常问答与知识库解读
      else if (data.intent === 'qa') {
         setMessages(prev => [...prev, { role: 'assistant', text: `📖 ${data.answer}` }]);
      }
      else {
         setMessages(prev => [...prev, { role: 'assistant', text: `✅ 分析完成！\n[执行SQL]:\n${data.generated_sql}` }]);
         if (data.echarts_config && chartInstance.current) {
           chartInstance.current.setOption(data.echarts_config, true);
         }
      }
    } catch (error) {
      setMessages(prev => [...prev, { role: 'assistant', text: '❌ 请求失败。' }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleApply = (msg) => {
    window.dispatchEvent(new CustomEvent('ai_sheet_apply', { detail: { id: msg.editId, updates: msg.updates } }));
    setMessages(prev => prev.map(m => m.editId === msg.editId ? { ...m, status: 'applied' } : m));
  };
  const handleReject = (msg) => {
    window.dispatchEvent(new CustomEvent('ai_sheet_reject', { detail: { id: msg.editId } }));
    setMessages(prev => prev.map(m => m.editId === msg.editId ? { ...m, status: 'rejected' } : m));
  };

  return (
    <div style={{ display: 'flex', height: '100vh', width: '100vw', fontFamily: '-apple-system, sans-serif', backgroundColor: '#f3f4f6', overflow: 'hidden' }}>

      {/* 1. 左侧栏 (包含表格与知识库组件) */}
      <div style={{ width: '260px', backgroundColor: '#ffffff', borderRight: '1px solid #e5e7eb', zIndex: 10, display: 'flex', flexDirection: 'column' }}>
        <div style={{ padding: '1.2rem 1rem', borderBottom: '1px solid #f3f4f6' }}>
          <h2 style={{ fontSize: '1rem', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '8px', margin: 0 }}><Database size={18} /> 数据资产</h2>
        </div>

        <div style={{ padding: '1rem', flex: 1 }}>
          <ul style={{ listStyle: 'none', padding: 0, margin: 0, fontSize: '0.9rem' }}>
            <li style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '8px 10px', backgroundColor: '#f3f4f6', borderRadius: '6px', cursor: 'pointer', fontWeight: 500 }}>
              <FileSpreadsheet size={16} color="#10b981" /> 极地海冰预测_V1
            </li>
          </ul>
        </div>

        {/* 💡 知识库挂载区 */}
        <div style={{ padding: '1rem', borderTop: '1px solid #f3f4f6', backgroundColor: '#fafbfc' }}>
          <div style={{ fontSize: '0.8rem', fontWeight: 600, color: '#9ca3af', marginBottom: '10px', textTransform: 'uppercase' }}>本地知识库 (RAG)</div>
          <ul style={{ listStyle: 'none', padding: 0, margin: 0, fontSize: '0.85rem' }}>
            {knowledgeFiles.map((f, i) => (
              <li key={i} style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '8px 10px', backgroundColor: '#f0fdf4', color: '#166534', borderRadius: '6px', marginBottom: '8px', fontWeight: 500 }}>
                <FileText size={16} /> <span style={{ textOverflow: 'ellipsis', overflow: 'hidden', whiteSpace: 'nowrap' }}>{f}</span>
              </li>
            ))}
            <li onClick={() => fileInputRef.current.click()} style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px', padding: '10px', border: '1px dashed #cbd5e1', borderRadius: '6px', cursor: 'pointer', color: '#64748b', fontWeight: 500, transition: 'all 0.2s', backgroundColor: '#ffffff' }}>
              <UploadCloud size={16} /> 上传 PDF 注入大脑
            </li>
            <input type="file" accept=".pdf" ref={fileInputRef} style={{ display: 'none' }} onChange={handleFileUpload} />
          </ul>
        </div>
      </div>

      <div style={{ flex: 1, minWidth: 0, display: 'flex', flexDirection: 'column', backgroundColor: '#ffffff', zIndex: 1 }}>
        <div style={{ padding: '12px 20px', borderBottom: '1px solid #e5e7eb', fontSize: '0.95rem', fontWeight: 600 }}>工作台 (Data Canvas)</div>
        <div style={{ flex: 1, position: 'relative', overflow: 'hidden' }}><DataCanvas /></div>
      </div>

      <div style={{ width: '380px', backgroundColor: '#ffffff', borderLeft: '1px solid #e5e7eb', display: 'flex', flexDirection: 'column', zIndex: 10 }}>
        <div style={{ padding: '1.2rem 1.5rem', borderBottom: '1px solid #e5e7eb' }}>
          <h2 style={{ fontSize: '1.05rem', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '10px', margin: 0 }}><Bot size={20} color="#3b82f6" /> DeepSeek Copilot</h2>
        </div>

        <div style={{ flex: 1, padding: '1.5rem', overflowY: 'auto', backgroundColor: '#f8fafc', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {messages.map((msg, index) => (
            <div key={index} style={{
              alignSelf: msg.role === 'user' ? 'flex-end' : 'flex-start',
              backgroundColor: msg.role === 'user' ? '#3b82f6' : '#ffffff',
              color: msg.role === 'user' ? '#ffffff' : '#334155',
              border: msg.role === 'user' ? 'none' : '1px solid #e2e8f0',
              padding: '12px 16px', borderRadius: '12px',
              borderTopRightRadius: msg.role === 'user' ? '2px' : '12px',
              borderTopLeftRadius: msg.role === 'assistant' ? '2px' : '12px',
              fontSize: '0.9rem', maxWidth: '90%', whiteSpace: 'pre-wrap', lineHeight: '1.5',
              boxShadow: '0 2px 4px rgba(0,0,0,0.02)'
            }}>
              {msg.text}
              {msg.type === 'proposal' && (
                <div style={{ display: 'flex', gap: '8px', marginTop: '12px' }}>
                  {msg.status === 'pending' && (
                    <>
                      <button onClick={() => handleApply(msg)} style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '4px', padding: '6px 0', backgroundColor: '#10b981', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer', fontWeight: 500 }}><Check size={14} /> 应用</button>
                      <button onClick={() => handleReject(msg)} style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '4px', padding: '6px 0', backgroundColor: '#ef4444', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer', fontWeight: 500 }}><X size={14} /> 撤销</button>
                    </>
                  )}
                  {msg.status === 'applied' && <div style={{ color: '#10b981', fontSize: '0.8rem', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '4px' }}><Check size={14} /> 已应用</div>}
                  {msg.status === 'rejected' && <div style={{ color: '#ef4444', fontSize: '0.8rem', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '4px' }}><X size={14} /> 已撤销</div>}
                </div>
              )}
            </div>
          ))}
          <div ref={messagesEndRef => messagesEndRef?.scrollIntoView({ behavior: "smooth" })} />
        </div>

        <div style={{ height: '300px', borderTop: '1px solid #e5e7eb', padding: '1rem', display: 'flex', flexDirection: 'column' }}>
           <div style={{ flex: 1, border: '1px dashed #cbd5e1', borderRadius: '8px', backgroundColor: '#f8fafc', position: 'relative' }}>
             <div ref={chartRef} style={{ width: '100%', height: '100%' }}></div>
           </div>
        </div>

        <div style={{ padding: '1.2rem', borderTop: '1px solid #e5e7eb' }}>
          <div style={{ display: 'flex', gap: '10px' }}>
            <input type="text" value={input} onChange={(e) => setInput(e.target.value)} onKeyDown={(e) => e.key === 'Enter' && handleSend()} placeholder="向 AI 下达指令..." style={{ flex: 1, padding: '12px 16px', borderRadius: '8px', border: '1px solid #d1d5db', outline: 'none' }} disabled={isLoading} />
            <button onClick={handleSend} disabled={isLoading} style={{ padding: '0 16px', backgroundColor: isLoading ? '#9ca3af' : '#3b82f6', color: 'white', border: 'none', borderRadius: '8px', cursor: 'pointer' }}><SendHorizontal size={18} /></button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;