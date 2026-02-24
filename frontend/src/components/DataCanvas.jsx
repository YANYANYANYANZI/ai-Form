import React, { useState, useEffect, useRef } from 'react';
import { Workbook } from '@fortune-sheet/react';
import axios from 'axios';

export default function DataCanvas() {
  const [sheetData, setSheetData] = useState([]);
  const [isLoaded, setIsLoaded] = useState(false);
  const saveTimeout = useRef(null);
  const isFirstRender = useRef(true);
  const workbookRef = useRef(null);

  // 💡 新增：用于存放修改前的单元格快照
  const pendingEdits = useRef({});

  useEffect(() => {
    // 1. 预览修改 (带高亮)
    const handlePreview = (e) => {
        const { id, updates } = e.detail;
        if (!workbookRef.current) return;
        const sheetDataArray = workbookRef.current.getAllSheets()[0].data;
        const originals = [];

        updates.forEach(u => {
            // 保存原单元格状态的深拷贝
            const origCell = sheetDataArray[u.r] && sheetDataArray[u.r][u.c]
                ? JSON.parse(JSON.stringify(sheetDataArray[u.r][u.c])) : null;
            originals.push({ r: u.r, c: u.c, cell: origCell });

            // 写入新值，并打上醒目的黄色高亮背景
            workbookRef.current.setCellValue(u.r, u.c, { v: u.v, m: String(u.v), bg: '#fef08a' });
        });
        pendingEdits.current[id] = originals;
    };

    // 2. 确认应用 (去除高亮并落盘)
    const handleApply = (e) => {
        const { id, updates } = e.detail;
        if (!workbookRef.current) return;
        updates.forEach(u => {
            workbookRef.current.setCellValue(u.r, u.c, { v: u.v, m: String(u.v), bg: null });
        });
        delete pendingEdits.current[id];
        handleSheetChange(workbookRef.current.getAllSheets());
    };
// 3. 拒绝修改 (恢复快照并彻底清除高亮)
    const handleReject = (e) => {
        const { id } = e.detail;
        if (!workbookRef.current || !pendingEdits.current[id]) return;
        const originals = pendingEdits.current[id];
        originals.forEach(orig => {
            // 💡 修复：强制加上 bg: null，一脚把黄底色踢开
            const cellToRestore = orig.cell ? { ...orig.cell, bg: null } : { v: '', m: '', bg: null };
            workbookRef.current.setCellValue(orig.r, orig.c, cellToRestore);
        });
        delete pendingEdits.current[id];
        handleSheetChange(workbookRef.current.getAllSheets());
    };

    window.addEventListener('ai_sheet_preview', handlePreview);
    window.addEventListener('ai_sheet_apply', handleApply);
    window.addEventListener('ai_sheet_reject', handleReject);

    axios.get('http://127.0.0.1:8000/api/v1/sheet/1/Sheet_V4')
      .then(res => {
        let dbData = res.data.celldata;
        const isValidData = Array.isArray(dbData) && dbData.length > 0 && (dbData[0]?.celldata || dbData[0]?.data);
        if (!isValidData) {
            dbData = [{ name: "Sheet_V4", celldata: [{ r: 0, c: 0, v: { m: "向 AI 下达修改指令吧！", v: "向 AI 下达修改指令吧！" } }] }];
        }
        setSheetData(dbData);
        setIsLoaded(true);
        setTimeout(() => isFirstRender.current = false, 1500);
      })
      .catch(() => setIsLoaded(true));

    return () => {
        window.removeEventListener('ai_sheet_preview', handlePreview);
        window.removeEventListener('ai_sheet_apply', handleApply);
        window.removeEventListener('ai_sheet_reject', handleReject);
    };
  }, []);

  const handleSheetChange = (data) => {
    if (isFirstRender.current) return;
    if (saveTimeout.current) clearTimeout(saveTimeout.current);

    const sheetToSave = JSON.parse(JSON.stringify(data));
    sheetToSave.forEach(sheet => {
        if (sheet.data) {
            const newCelldata = [];
            for (let r = 0; r < sheet.data.length; r++) {
                if (!sheet.data[r]) continue;
                for (let c = 0; c < sheet.data[r].length; c++) {
                    const cell = sheet.data[r][c];
                    if (cell && typeof cell === 'object' && Object.keys(cell).length > 0 && cell.v !== null && cell.v !== '') {
                        newCelldata.push({ r, c, v: cell });
                    }
                }
            }
            sheet.celldata = newCelldata;
            delete sheet.data;
        }
    });

    saveTimeout.current = setTimeout(async () => {
     await axios.post('http://127.0.0.1:8000/api/v1/sheet/save/', { workspace_id: 1, sheet_name: "Sheet_V4", celldata: sheetToSave })
    }, 1000);
  };

  if (!isLoaded) return <div style={{ padding: '20px' }}>正在建立数据流...</div>;
  return <Workbook ref={workbookRef} data={sheetData} onChange={handleSheetChange} />;
}