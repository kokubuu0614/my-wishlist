import os

# フォルダ構造の定義
files = {
    "package.json": """{
  "name": "wishlist-app",
  "private": true,
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "firebase": "^11.0.0",
    "lucide-react": "^0.450.0",
    "react": "^18.3.1",
    "react-dom": "^18.3.1"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^4.3.2",
    "autoprefixer": "^10.4.20",
    "postcss": "^8.4.47",
    "tailwindcss": "^3.4.13",
    "vite": "^5.4.8"
  }
}""",
    "tailwind.config.js": """/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: { extend: {} },
  plugins: [],
}""",
    "postcss.config.js": """export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}""",
    "index.html": """<!DOCTYPE html>
<html lang="ja">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no" />
    <title>Wishlist App</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
  </body>
</html>""",
    "src/index.css": """@tailwind base;
@tailwind components;
@tailwind utilities;""",
    "src/main.jsx": """import React from 'react'
import ReactDom from 'react-dom/client'
import App from './App.jsx'
import './index.css'

ReactDom.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)""",
    "src/App.jsx": """import React, { useState, useEffect, useCallback, memo } from 'react';
import { initializeApp } from 'firebase/app';
import { getAuth, signInAnonymously, onAuthStateChanged } from 'firebase/auth';
import { getFirestore, collection, doc, setDoc, deleteDoc, onSnapshot, writeBatch } from 'firebase/firestore';
import { Plus, Trash2, ArrowUp, ArrowDown, ExternalLink, GripVertical, Pencil, Check, X, Loader2, Heart } from 'lucide-react';

const firebaseConfig = {
  apiKey: "YOUR_API_KEY",
  authDomain: "YOUR_AUTH_DOMAIN",
  projectId: "YOUR_PROJECT_ID",
  storageBucket: "YOUR_STORAGE_BUCKET",
  messagingSenderId: "YOUR_MESSAGING_SENDER_ID",
  appId: "YOUR_APP_ID"
};

const app = initializeApp(firebaseConfig);
const auth = getAuth(app);
const db = getFirestore(app);

const WishItem = memo(({ item, index, total, isEditing, onStartEdit, onCancelEdit, onSaveEdit, onDelete, onMove, onDragStart, onDragOver, onDragEnd, draggedIndex }) => {
  const [editName, setEditName] = useState(item.name);
  const [editUrl, setEditUrl] = useState(item.url || '');
  useEffect(() => { if (isEditing) { setEditName(item.name); setEditUrl(item.url || ''); } }, [isEditing, item]);
  return (
    <div draggable={!isEditing} onDragStart={() => onDragStart(index)} onDragOver={(e) => { e.preventDefault(); onDragOver(index); }} onDragEnd={onDragEnd}
      className={`flex items-center bg-white p-4 rounded-2xl shadow-sm border transition-all ${draggedIndex === index ? 'opacity-30' : 'border-slate-100 hover:border-slate-200'} ${isEditing ? 'ring-2 ring-indigo-400' : ''}`}>
      <div className="hidden md:block text-slate-300 mr-2 cursor-grab"><GripVertical size={20} /></div>
      <div className="flex-grow min-w-0">
        {isEditing ? (
          <div className="space-y-2">
            <input className="w-full px-3 py-1 border rounded-lg text-sm" value={editName} onChange={e => setEditName(e.target.value)} autoFocus />
            <input className="w-full px-3 py-1 border rounded-lg text-xs" value={editUrl} onChange={e => setEditUrl(e.target.value)} placeholder="URL" />
          </div>
        ) : (
          <><h3 className="font-bold text-slate-800 truncate">{item.name}</h3>{item.url && <a href={item.url} target="_blank" className="text-xs text-indigo-500">リンクを表示</a>}</>
        )}
      </div>
      <div className="flex gap-1">
        {isEditing ? (
          <><button onClick={() => onSaveEdit(item.id, editName, editUrl)} className="p-2 bg-green-500 text-white rounded-lg"><Check size={16}/></button><button onClick={onCancelEdit} className="p-2 bg-slate-100 rounded-lg"><X size={16}/></button></>
        ) : (
          <><button onClick={() => onMove(index, -1)} disabled={index === 0} className="p-1 text-slate-400 disabled:opacity-10"><ArrowUp size={16}/></button>
            <button onClick={() => onMove(index, 1)} disabled={index === total-1} className="p-1 text-slate-400 disabled:opacity-10"><ArrowDown size={16}/></button>
            <button onClick={() => onStartEdit(item.id)} className="p-2 text-slate-400"><Pencil size={16}/></button>
            <button onClick={() => onDelete(item.id)} className="p-2 text-slate-400 hover:text-red-500"><Trash2 size={16}/></button></>
        )}
      </div>
    </div>
  );
});

export default function App() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [editingId, setEditingId] = useState(null);
  const [draggedIndex, setDraggedIndex] = useState(null);
  const [newName, setNewName] = useState('');
  const [newUrl, setNewUrl] = useState('');

  useEffect(() => {
    signInAnonymously(auth);
    return onAuthStateChanged(auth, (u) => {
      if (u) {
        return onSnapshot(collection(db, 'users', u.uid, 'wishlist'), (s) => {
          setItems(s.docs.map(d => ({ id: d.id, ...d.data() })).sort((a,b) => (a.order??0)-(b.order??0)));
          setLoading(false);
        });
      }
    });
  }, []);

  const saveOrders = async (current) => {
    const batch = writeBatch(db);
    current.forEach((item, i) => batch.set(doc(db, 'users', auth.currentUser.uid, 'wishlist', item.id), { order: i }, { merge: true }));
    await batch.commit();
  };

  const handleAdd = async (e) => {
    e.preventDefault(); if (!newName.trim()) return;
    const id = Date.now().toString();
    await setDoc(doc(db, 'users', auth.currentUser.uid, 'wishlist', id), { name: newName, url: newUrl, order: items.length });
    setNewName(''); setNewUrl('');
  };

  if (loading) return <div className="min-h-screen flex items-center justify-center font-bold text-slate-400">Loading...</div>;

  return (
    <div className="min-h-screen bg-slate-50 p-4 md:p-8 max-w-2xl mx-auto">
      <header className="mb-10 text-center uppercase tracking-tighter"><h1 className="text-4xl font-black text-indigo-600">Wishlist</h1></header>
      <form onSubmit={handleAdd} className="bg-white p-6 rounded-[2rem] shadow-sm border mb-8 flex flex-col gap-3">
        <input className="px-4 py-3 bg-slate-50 rounded-xl outline-none text-sm" placeholder="名前" value={newName} onChange={e => setNewName(e.target.value)} />
        <input className="px-4 py-3 bg-slate-50 rounded-xl outline-none text-sm" placeholder="URL" value={newUrl} onChange={e => setNewUrl(e.target.value)} />
        <button className="bg-indigo-600 text-white font-bold py-3 rounded-xl">追加</button>
      </form>
      <div className="space-y-3">
        {items.map((item, i) => (
          <WishItem key={item.id} item={item} index={i} total={items.length} isEditing={editingId===item.id} onStartEdit={setEditingId} onCancelEdit={()=>setEditingId(null)}
            onSaveEdit={async (id, n, u) => { await setDoc(doc(db, 'users', auth.currentUser.uid, 'wishlist', id), { name: n, url: u }, { merge: true }); setEditingId(null); }}
            onDelete={id => deleteDoc(doc(db, 'users', auth.currentUser.uid, 'wishlist', id))}
            onMove={(idx, dir) => { const n = [...items]; [n[idx], n[idx+dir]] = [n[idx+dir], n[idx]]; setItems(n); saveOrders(n); }}
            onDragStart={setDraggedIndex} onDragOver={idx => { if(draggedIndex===idx) return; const n = [...items]; const t = n.splice(draggedIndex, 1)[0]; n.splice(idx, 0, t); setDraggedIndex(idx); setItems(n); }}
            onDragEnd={() => { saveOrders(items); setDraggedIndex(null); }} draggedIndex={draggedIndex}
          />
        ))}
      </div>
    </div>
  );
}"""
}

# ファイル作成実行
for path, content in files.items():
    os.makedirs(os.path.dirname(path), exist_ok=True) if os.path.dirname(path) else None
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Created: {path}")

print("\\n--- すべてのファイルが作成されました！ ---")
print("1. 'npm install' を実行してください。")
print("2. 'npm run dev' でアプリが起動します。")
